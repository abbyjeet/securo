# Where To Look — File Index by Domain

## Authentication & Authorization

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Custom login/logout + 2FA | `backend/app/api/custom_auth.py` | JWT-based auth with TOTP support via pyotp |
| Passkeys (WebAuthn) | `backend/app/api/passkeys.py` | Handles registration, verification, credential deletion |
| OIDC callbacks | `backend/app/api/oidc_auth.py` + `frontend/src/pages/oauth-callback.tsx`, `frontend/src/pages/oidc-callback.tsx` | Two separate pages depending on provider flow |
| Admin user management (passwords, passkeys, 2FA) | `backend/app/api/admin.py` | Requires admin role (`is_superuser`) to access |

## Accounts & Transactions

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Account model | `backend/app/models/account.py` | UUID primary key; relationship to `Transaction`, `BankConnection` |
| Transaction model | `backend/app/models/transaction.py` | Belongs to one account via foreign key; fiscal year aware |
| Balance computation | `backend/app/services/balance_service.py` | Calculates running balance from the transaction ledger |
| Accounts API (CRUD) | `backend/app/api/accounts.py` | List, create, update, close accounts |
| Transactions API | `backend/app/api/transactions.py` | Create, list, filter by category/date/payee |

## Budgets & Goals

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Budget model + service | `backend/app/models/budget.py`, `backend/app/services/budget_service.py` | Supports monthly and custom-period budgets with progress tracking |
| Goal model + service | `backend/app/models/goal.py`, `backend/app/services/goal_service.py` | Savings goals with target dates, progress bars |

## Rules Engine (Auto-Categorization)

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Rule models | `backend/app/models/rule.py` | Conditions: amount ranges, payee patterns, category tags; actions: assign category, move date |
| Rules API | `backend/app/api/rules.py` | Create, list, delete rules |
| Engine evaluation | `backend/app/services/rules_engine.py` | Matches transactions against rules in priority order |

## Categories & Grouping

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Category + category_group models | `backend/app/models/category.py`, `backend/app/models/category_group.py` | Hierarchical groups (e.g., "Food" → "Groceries") |
| Categories API | `backend/app/api/categories.py` | CRUD on categories and their group membership |

## Collections & Reports

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Collection model + service | `backend/app/models/collection.py`, `backend/app/services/collection_service.py` | "Collections" are user-curated groups of transactions (e.g., "My Vacations") |
| Collections API | `backend/app/api/collections.py` | Create, list, add/remove transactions from collections |
| Net Worth report | `backend/app/reports/net_worth_report.py` | Combines cash accounts + assets - liabilities |
| Income vs Expenses sparkline | `backend/app/reports/income_expenses_chart.py` | Renders a month-over-month bar chart with category sparklines |

## Import / Reconciliation

| Concept | File / Path | Notes |
|---------|-------------|--------|
| OFX/QIF/CSV import parsing | `backend/app/services/import_service.py` | Parses CSV, QIF, and OFX files; deduplicates by date+counterparty |
| Import logs API | `backend/app/api/import_logs.py` | View past import runs and their results |

## Bank Sync Providers (Enable Banking)

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Enable Banking integration | `backend/app/providers/enable_banking.py` | OAuth flow with PSD2 consent; handles refresh tokens |
| Account linking logic | `backend/app/services/bank_sync_service.py` | Orchestrates the sync across all providers |

## Bank Sync Providers (SimpleFIN)

| Concept | File / Path | Notes |
|---------|-------------|--------|
| SimpleFIN integration | `backend/app/providers/simplefin.py` | Uses setup tokens from bridge.simplefin.org; no API key needed |

## Bank Sync Providers (Pluggy — Brazil)

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Pluggy integration | `backend/app/providers/pluggy.py` | OAuth 2.0 flow with pluggy.ai; supports Itaú, Bradesco, Nubank, etc. |

## Tesouro Direto (Brazilian Gov Bonds)

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Bond price cache + fetching | `backend/app/providers/tesouro_direto.py` | Downloads CSV from tesourodirecto.gov.br; caches in PostgreSQL |
| Asset model extensions | `backend/app/models/treasury_bond.py` (if present) | Tracks holdings and unrealized gains |

## Assets

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Asset model | `backend/app/models/asset.py` | Stocks, funds; supports cost basis tracking |
| Asset groups | `backend/app/models/asset_group.py` | Group assets by category (e.g., "ETFs", "Crypto") |

## Invoices & Sharing

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Invoice model + PDF generation | `backend/app/models/invoice.py`, `backend/app/services/invoice_service.py` | Uses ReportLab to generate PDF invoices from selected transactions |
| Shared invoice page | `frontend/src/pages/shared-invoice.tsx` | Renders an invoice by token without requiring login |

## AI Agents & MCP Server

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Built-in MCP server routes | `backend/app/agents/api/info.py`, `/api/agents`, `/api/connections`, `/api/conversations`, `/api/chat` | Handles agent registration, connection management, chat streams |
| Knowledge base (RAG) | `backend/app/agents/services/knowledge_service.py` | Embeds documents into pgvector; supports per-agent knowledge stores |
| Built-in MCP server app | `backend/mcp_server/main.py` | Standalone uvicorn app mounted at `/mcp`; separate port 8765 |
| External MCP servers | Configured via `AGENTS_EXTRA_MCP_SERVERS` env var and listed in the UI's "External MCP access" panel |

## Workspaces & Multi-Tenancy

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Workspace model | `backend/app/models/workspace.py` | Users belong to workspaces; each workspace has its own currency and settings |
| User lookup (admin) | `backend/app/api/user_lookup.py` | Admins can look up a user by email across all workspaces |

## Settings & Configuration

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Workspace settings API | `backend/app/api/settings.py` | Default currency, fiscal year start month, etc. |
| System-wide settings (from `.env`) | `backend/app/core/config.py` | Reads from environment variables; never commit secrets to git |

## Database & Migrations

| Concept | File / Path | Notes |
|---------|-------------|--------|
| SQLAlchemy engine factory | `backend/app/core/database.py` | Async session maker with connection pooling via asyncpg |
| Migration scripts | `backend/alembic/versions/*.py` | Each file is a revision; check `down_revision` to find the predecessor |

## Frontend Pages (React)

| Concept | File / Path | Notes |
|---------|-------------|--------|
| Dashboard | `frontend/src/pages/dashboard.tsx` | Summary cards, recent transactions feed |
| Transactions page | `frontend/src/pages/transactions.tsx` | Table with filters, search, pagination |
| Accounts page | `frontend/src/pages/accounts.tsx` | List + create account forms |
| Import page | `frontend/src/pages/import.tsx` | File picker for OFX/QIF/CSV |
| Rules page | `frontend/src/pages/rules.tsx` | Rule builder UI |

## Frontend Components (Reusable)

| Concept | Path | Notes |
|---------|------|--------|
| Data table | `src/components/data-table.tsx` | Sortable, filterable columns; pagination |
| Dialog / Modal | `src/components/ui/dialog.tsx` | Radix UI primitives wrapper |
| Tooltip | `src/components/ui/tooltip.tsx` | Context-aware tooltips (e.g., on category names) |

## Translation Files

| Concept | Path | Notes |
|---------|------|--------|
| English translations | `frontend/src/locales/en.json` | All user-facing strings |
| Portuguese-BR translations | `frontend/src/locales/pt-BR.json` | Full translation of UI strings |
