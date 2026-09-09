# Notes & Gotchas

## Optional Features Are Zero-Cost by Design

The AI agents feature is gated behind `AGENTS_ENABLED=true`. When disabled:

- No imports of the `app.agents` module occur at startup
- The MCP server container is not started (unless you explicitly use the `agents` compose profile)
- No background tasks related to agent conversations or knowledge-base embeddings run
- Users who opt out never pay for those resources

The same pattern applies to bank sync providers — they're imported only when their feature flags are set. This means a minimal deployment can be lean and secure by default.

### How the MCP server stays modular

```python
# backend/app/main.py

if os.getenv("AGENTS_ENABLED", "false").strip().lower() in ("1", "true"):
    from app.agents.api.info import router as agents_info_router
    # ... mount all agent routes at /api/agents/*
```

The MCP server lives in a separate uvicorn app (`backend/mcp_server/main.py`) and is only mounted when the flag is on. It listens on port 8765 and can be reached from external clients (Claude Desktop, n8n, custom apps) once you mint an access token via the UI's "External MCP access" panel.

## Migration Chain Validation

Every migration file in `backend/alembic/versions/` must:

1. Be named with a unique, zero-padded integer prefix (e.g., `076_add_column_to_accounts.py`)
2. Reference its predecessor via `down_revision = "075"` (or `"base"` for the first migration)

**Why this matters:** CI runs against every PR's merged branch to ensure revisions still form a single linear chain. If two developers each create `076_...` on different branches, one will fail during CI and they'll have to renumber. This prevents "merge hell" at merge time — the error surfaces immediately in your own PR.

## OIDC-Only Mode Behavior

When you set `OIDC_ENABLED=true` and disable local auth (`LOCAL_AUTH_ENABLED=false`), Securo becomes SSO-only:

| Action | Result |
|--------|---------|
| New user tries to sign up with password | Rejected (registration is rate-limited + gated by local auth flag) |
| Existing user logs in via OIDC | Auto-provisioned if `OIDC_AUTO_REGISTER=true` and email addresses match |
| Existing password-backed account gets SSO'd back into | Only if `OIDC_EXISTING_USER_LINK_MODE=verified_email` (or `email`) |
| First admin on a fresh OIDC-only instance | Must be created via the OIDC provider, with their claim including one of the roles listed in `OIDC_ADMIN_ROLES` |

The login page will show an explicit configuration error if neither local auth nor OIDC is available. If only the *client-side* request to fetch OIDC metadata fails (network glitch), the frontend still shows the password form but warns that SSO isn't responding; the backend remains authoritative and rejects password logins in OIDC-only mode regardless.

## Passkeys Require HTTPS (Except on localhost)

This is not a Securo-specific restriction — it's enforced by the WebAuthn standard itself:

- **Plain HTTP never works.** Requests from `http://192.168.1.10:3000` are rejected with an explanation in the UI instead of failing silently.
- **Localhost is exempt** because many users develop on `http://localhost:3000`.
- To pin passkeys to a single domain (e.g., you serve Securo under `app.securo.local`, `dev.securo.local`), set `WEBAUTHN_RP_ID=securo.local`. Otherwise the browser uses whatever origin it's on, and requests from unusable addresses get an explanation.

## Tesouro Direto Cache Warmup

The Brazilian government bond (Tesouro Direto) price cache is pre-loaded at startup **only** if a workspace has BRL as its default currency:

```python
async def _warm_tesouro_cache() -> None:
    # Only runs if AGENTS_ENABLED=false and tesouro_direto_enabled=true
    # AND the current workspace uses BRL as its primary currency.
    await get_tesouro_direto_provider().get_available_bonds()
```

This avoids calling Brazil's government endpoint on deployments that serve only USD/EUR users, keeping cold-start latency down and avoiding unnecessary cross-border traffic.

## Migration Numbering Strategy

When you add a new migration:

1. Find the highest revision number currently in `alembic/versions/`
2. Add 1 (use zero-padding to match existing files)
3. Run `uv run alembic revision --autogenerate -m "Short description"`
4. Commit both the new `.py` file and any changes it makes to other migration files

If you're unsure what number to use, check the latest revision in the migration chain or ask a human reviewer — they can tell you whether your PR is being reviewed concurrently with another migration PR.

## Frontend: `renderWithProviders`

When writing tests for components that depend on TanStack Query, React Router, i18n, or any of the Context providers, always render through `renderWithProviders`:

```tsx
import { renderWithProviders } from '@/test/utils'

const { getByText } = renderWithProviders(<MyComponent />)
expect(getByText('Loading...')).toBeInTheDocument()
```

This helper wires up:

- TanStack Query's provider with a real client (so server state is properly tracked)
- The React Router history context
- i18n with the correct locale
- Any other providers that the component tree needs

Without it, your tests will pass in dev but break after a deploy where the providers aren't mounted.

## Frontend: `frontend/.npmrc` Nuance

The `.npmrc` file at the repo root contains:

```toml
# This line prevents npm from running install scripts (pre/postinstall)
# during dependency installation, which is useful for CI safety.
fund=false
audit=true
also-update-lockfile=false
always-spawn=false
bin-links=false
color=auto
depth=0
engine-strict=false
foreground-scripts=false
ignore-scripts=true   # ← the important one here
no-audit=false
no-fund=false
package-lock=true
prefer-offline=false
progress=false
dry-run=false
omit=false
use-bin-links=false
workspace=false

# Skip releases younger than 7 days so a compromised publish has time to be caught.
# This is an additional defense layer against supply-chain attacks.
save-exact=true
```

The `ignore-scripts=true` directive means that even if a package's `package.json` specifies `"scripts"` like `"preinstall: install-hooks"`, those scripts will not execute when you run `npm install`. The second line (`save-exact`) adds a 7-day cooldown on newly published packages, giving maintainers time to respond if something goes wrong.

## Backend: Celery Worker Concurrency

In production (or any non-trivial deployment), the Celery worker is started with `--concurrency=2`:

```bash
celery -A app.worker worker --loglevel=info --concurrency=2
```

This limits CPU and memory usage so that other services (the API server, the frontend dev server) aren't starved. The default concurrency in Celery is "number of CPUs", which would be fine for a bare-metal server but not when you're sharing resources with Docker containers or shared hosting.

## Database: pgvector Extension

The PostgreSQL image used (`pgvector/pgvector:pg16`) ships the `vector` extension built-in, which Securo needs for the AI agents' RAG knowledge base. If you replace that image with a vanilla `postgres:16`, migrations will fail when they try to create embeddings tables. The Docker Compose file uses `${DB_IMAGE:-docker.io/pgvector/pgvector:pg16}`, so if you override it, remember to also add the extension in your startup script.

## Frontend: Lazy-Loaded Routes with `<Suspense>`

Every route component is wrapped in a `React.lazy` call and rendered inside a `<Suspense fallback={<LoadingFallback />}>`. This means that when a user navigates from `/dashboard` to `/transactions`, they'll see a spinner before the new page fully renders. The fallback is deliberately kept small — just a spinning border — so it doesn't distract users while their browser fetches and compiles the module.

If your lazy-loaded component throws an error during its `import()` call, the entire app will show that error instead of the fallback. Wrap heavy computations or network calls in your own try/catch and re-throw with a user-friendly message if something goes wrong at import time.

## Environment Variables: Never Commit Secrets to Git

The `.env` file is listed in `.gitignore`. The production compose file (`docker-compose.prod.yml`) never mounts that directory into containers, so secrets are only available on the host machine where you run `docker compose up --build`. If you accidentally commit a `.env`, revoke any tokens it contains (for bank sync providers, OIDC clients, etc.) immediately.

## TypeScript: `@typescript/native` Points to TS 7.0

In `frontend/package.json`:

```json
"@typescript/native": "npm:typescript@7.0.2"
```

This tells Vite's React plugin to use the TypeScript compiler from that package instead of the global one, which is important if you're using a Node version whose bundled TS differs from what the project expects. The version is pinned because 7.0.2 has known regressions with JSX and JSX fragments — upgrading will require a code change in `src/App.tsx` to avoid breaking type inference for components that return multiple elements.
