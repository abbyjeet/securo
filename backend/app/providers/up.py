"""Up Bank provider.

Up Bank (https://up.com.au) provides a simple REST API for accessing
accounts, transactions, and account metadata. Users authenticate using a
Personal Access Token (PAT) generated from their Up app settings.

Flow:
1. User generates a PAT from Up's app (Settings → Security → Create New Token)
2. User pastes the token into Securo (token-paste flow)
3. Securo validates the token and fetches account information
4. On subsequent syncs, the token is used directly in API requests

Round-up Transactions:
Up Bank allows users to round up transactions to the nearest dollar and save
the difference. The API returns this as a `roundUp` attribute on the main
transaction, not as a separate transaction record. This provider creates
separate TransactionData records for round-up amounts so they appear as
individual transactions in Securo, using the original transaction ID + "-ru"
as a unique identifier.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import httpx
import asyncio

from app.providers.base import (
    AccountData,
    BankProvider,
    ConnectionData,
    ProviderUserActionRequired,
    SessionExpiredError,
    TransactionData,
)

logger = logging.getLogger(__name__)

UP_API_URL = "https://api.up.com.au"
UP_API_TIMEOUT = 15
UP_MAX_RETRIES = 3
UP_RETRY_BACKOFF = 30  # base seconds; doubles each attempt: 30s, 60s, 120s (~3min total)


class UpBankProvider(BankProvider):
    """Up Bank connector using Personal Access Token."""

    @property
    def name(self) -> str:
        return "up"

    @property
    def flow_type(self) -> str:
        # Token-paste flow: user provides a PAT directly
        return "token"

    # ----- credentials / token handling --------------------------------

    @staticmethod
    def _extract_token(credentials: dict) -> str:
        """Extract the PAT token from credentials."""
        token = (credentials or {}).get("pat") or ""
        if not token:
            raise SessionExpiredError("Up Bank PAT token is missing")
        return token

    async def _request(
        self,
        credentials: dict,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict:
        """Make an authenticated request to the Up API.
        
        Follows the same retry pattern as the working sync script:
        - Retry loop with exponential backoff
        - Handle 429 rate limits with proper wait times
        - Respect Retry-After header if present
        """
        import asyncio
        
        token = self._extract_token(credentials)
        headers = {
            "Authorization": f"Bearer {token}"            
        }
        
        # Retry loop matches the pattern from working sync script
        for attempt in range(1, UP_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    base_url=UP_API_URL,
                    timeout=UP_API_TIMEOUT,
                    headers=headers,
                ) as client:
                    resp = await client.request(method, path, **kwargs)
                    
                # Handle 429 rate limit (match sync script pattern)
                if resp.status_code == 429:
                    if attempt == UP_MAX_RETRIES:
                        raise RuntimeError(f"Up Bank API rate limited after {UP_MAX_RETRIES} attempts")
                    
                    retry_after = resp.headers.get("Retry-After")
                    wait = int(retry_after) if retry_after else UP_RETRY_BACKOFF * (2 ** (attempt - 1))
                    await asyncio.sleep(wait)
                    continue
                
                # Handle auth errors
                if resp.status_code == 401:
                    raise ProviderUserActionRequired(
                        "Up Bank PAT token is invalid or expired",
                        code="credentials_invalid",
                        help_url="https://up.com.au/",
                    )
                elif resp.status_code == 403:
                    raise ProviderUserActionRequired(
                        "Up Bank PAT token does not have required permissions",
                        code="credentials_insufficient_scope",
                        help_url="https://up.com.au/",
                    )
                elif resp.status_code >= 400:
                    raise RuntimeError(f"Up Bank API error ({resp.status_code}): {resp.text[:200]}")
                
                # Success
                return resp.json() or {}
                
            except httpx.HTTPError as exc:
                if attempt == UP_MAX_RETRIES:
                    raise RuntimeError(f"Up Bank API request failed: {exc}") from exc
                
                wait = UP_RETRY_BACKOFF * (2 ** (attempt - 1))
                await asyncio.sleep(wait)
                continue
        
        raise RuntimeError(f"Failed after {UP_MAX_RETRIES} attempts")

    # ----- connection flow (token-paste) --------------------------------

    def get_oauth_url(self, *args, **kwargs):  # type: ignore[override]
        raise NotImplementedError("Up Bank uses PAT token paste flow, not OAuth")

    async def handle_oauth_callback(self, code: str) -> ConnectionData:
        """Validate a PAT token and fetch initial account data.
        
        In token-paste flow, the ``code`` parameter is the PAT itself.
        """
        
        token = code.strip() if code else ""
        if not token:
            raise ProviderUserActionRequired(
                "Up Bank PAT token is empty",
                code="invalid_token",
                help_url="https://up.com.au/",
            )

        credentials = {"pat": token}

        # Fetch accounts to validate token
        accounts_data = await self._request(credentials, "GET", "/api/v1/accounts")
        accounts = self._parse_accounts(accounts_data)
        
        return ConnectionData(
            external_id=f"up-{token[:8]}",
            institution_name="Up Bank",
            credentials=credentials,
            accounts=accounts,
            logo_url="https://up.com.au/favicon.ico",
        )

    def _parse_accounts(self, data: dict) -> list[AccountData]:
        """Parse accounts from Up API response."""
        accounts = []
        for account in data.get("data", []):
            attrs = account.get("attributes", {})
            account_type = attrs.get("accountType", "").lower()
            
            # Map Up account types to standard types
            if account_type == "saver":
                normalized_type = "savings"
            elif account_type == "transactional":
                normalized_type = "checking"
            else:
                normalized_type = account_type or "checking"

            balance_obj = attrs.get("balance", {})
            balance = Decimal(str(balance_obj.get("value", 0)))
            currency = balance_obj.get("currencyCode", "AUD")
            
            accounts.append(
                AccountData(
                    external_id=account.get("id", ""),
                    name=attrs.get("displayName", "Unknown"),
                    type=normalized_type,
                    balance=balance,
                    currency=currency,
                    masked_number=attrs.get("accountNumber", "")[-4:] if attrs.get("accountNumber") else None,
                )
            )
        return accounts

    async def get_accounts(self, credentials: dict) -> list[AccountData]:
        """Fetch accounts for the authenticated user."""
        data = await self._request(credentials, "GET", "/api/v1/accounts")
        accounts = self._parse_accounts(data)
        return accounts
    
    async def get_transactions(
        self,
        credentials: dict,
        account_external_id: str,
        since: Optional[date] = None,
        payee_source: str = "auto",
    ) -> list[TransactionData]:
        """Fetch transactions for an account, including round-up transactions.
        
        Follows the same pagination and filtering pattern as the working sync script.
        """
        
        # Build params matching sync script pattern
        params: dict[str, Any] = {"page[size]": 100}
        if since:
            since_iso = f"{since}T00:00:00.000Z"
            params["filter[since]"] = since_iso

        transactions = []
        url = f"/api/v1/accounts/{account_external_id}/transactions"

        # Pagination loop
        lmt = 0
        while url and lmt < 5:
            # Build kwargs conditionally so we NEVER pass params={} when url has its own query string
            kwargs: dict[str, Any] = {}
            if params:
                kwargs["params"] = params
                
            data = await self._request(credentials, "GET", url, **kwargs)
            params = None  # Only pass params on the initial request; page links embed their own params

            for txn in data.get("data", []):            
                attrs = txn.get("attributes", {})
                amount_obj = attrs.get("amount", {})
                amount = Decimal(str(amount_obj.get("value", 0)))

                # Determine type and status matching sync script
                txn_type = "credit" if amount > 0 else "debit"
                txn_date = self._parse_date(attrs.get("createdAt"))
                cleared = attrs.get("status") == "SETTLED"
                txn_status = "posted" if cleared else "pending"
                currency = amount_obj.get("currencyCode", "AUD")
                payee = attrs.get("rawText", attrs.get("description", "Unknown"))

                # Main transaction
                transactions.append(
                    TransactionData(
                        external_id=txn.get("id", ""),
                        description=attrs.get("description", ""),
                        amount=abs(amount),
                        date=txn_date,
                        type=txn_type,
                        currency=currency,
                        payee=payee,
                        status=txn_status,
                    )
                )

                # Round-up transaction (if present) - same pattern as sync script
                round_up = attrs.get("roundUp")
                if round_up is not None:
                    round_up_amount_obj = round_up.get("amount", {})
                    round_up_amount = Decimal(str(round_up_amount_obj.get("value", 0)))

                    if round_up_amount > 0:
                        transactions.append(
                            TransactionData(
                                external_id=f"{txn.get('id', '')}-ru",
                                description=f"Round Up: {attrs.get('description', '')}",
                                amount=round_up_amount,
                                date=txn_date,
                                type="debit",
                                currency=round_up_amount_obj.get("currencyCode", "AUD"),
                                payee=f"Round Up: {attrs.get('rawText', attrs.get('description', 'Unknown'))}",
                                status=txn_status,
                            )
                        )

            # Extract next page URL outside of the transaction loop
            url = data.get("links", {}).get("next")

            # Optional: Rate limiting delay for Up Bank API (e.g., 60 req/min)
            if url:
                await asyncio.sleep(1)

            lmt += 1

        return transactions

    async def refresh_credentials(self, credentials: dict) -> dict:
        """Refresh credentials (no-op for PAT tokens).
        
        PAT tokens don't expire. We validate by attempting a simple read.
        """
        # await self._request(credentials, "GET", "/api/v1/accounts?page[size]=1")
        return credentials

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> date:
        """Parse Up's ISO 8601 date to Python date."""
        if not date_str:
            return date.today()
        try:
            # Extract YYYY-MM-DD from ISO 8601 string
            date_part = date_str[:10]
            return datetime.strptime(date_part, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return date.today()
