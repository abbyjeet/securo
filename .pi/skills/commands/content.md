# Commands Reference

## Starting / Running

### Full Stack (Development)

```bash
docker compose up --build
```

- Builds all images (`backend` and `frontend`) from their Dockerfiles.
- Starts PostgreSQL, Redis, backend API, frontend dev server, Celery worker, Celery beat scheduler.
- Frontend mounts the repo root read-only at `/workspace`, enabling hot-reload of any changes you make to source files in your IDE.

### Full Stack with Agents Profile

```bash
docker compose --profile agents up --build
```

Adds the MCP server container (`mcp-server`) on port 8765 so external AI agents can connect. Requires `AGENTS_ENABLED=true` and a provider connection configured via Settings → AI Agents.

### Manual Backend Only (no Docker)

```bash
# From repo root or backend/ directory
uv sync --all-extras       # First time only; builds .venv from uv.lock
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
celery -A app.worker worker --loglevel=info --concurrency=2
celery -A app.worker beat --loglevel=info
```

The MCP server can be run alongside the API on a separate port:

```bash
uvicorn mcp_server.main:app --host 127.0.0.1 --port 8765
```

Set `AGENTS_BUILTIN_MCP_URL=http://127.0.0.1:8765/mcp` so the API knows where to reach it. The MCP server is modular and zero-cost when not enabled — only imported if `AGENTS_ENABLED=true`.

## Testing

### Backend Tests

```bash
cd backend && uv sync --all-extras && uv run pytest
```

Runs all tests in `backend/tests/` using `pytest-asyncio` with auto-mode (async functions annotated with `@pytest.mark.asyncio`). Coverage can be included:

```bash
uv run pytest --cov=app --cov-report=term-missing
```

The coverage report omits CLI scripts, Celery tasks, and bank provider stubs (`backend/app/providers/pluggy.py`, etc.) since they are integration-tested end-to-end rather than unit-tested.

### Frontend Tests

```bash
cd frontend && npm run test
```

Runs Vitest with React Testing Library. Render through `renderWithProviders` from `@/test/utils` which wires up TanStack Query, the router, i18n, and import aliases.

## Linting & Type Checking

### Backend (Python)

```bash
cd backend && uv run ruff check .
uv run ty check .
```

Configured in `pyproject.toml`:

- **Ruff** targets Python 3.11 with a reduced rule set (`select = ["E4", "E7", "E9", "F"]`). The upper bound on `ruff` is pinned to `<0.17` so CI doesn't silently change formatting of historical imports (e.g., alembic migrations).
- **Ty** (pinned to 0.0.75) performs static type checking across the entire project. Errors in one module can surface in another, which is why ty checks the whole `app/` tree rather than individual files.

### Frontend (TypeScript)

```bash
cd frontend && npm run lint
```

Runs ESLint + TypeScript compiler check (`tsc`) as part of `npm run typecheck`. The build script runs this first before bundling, so a failing typecheck blocks the production artifact.

## Building

### Frontend Production Build

```bash
cd frontend && npm run build
```

This runs `npm run typecheck` first (which calls `tsc -b`), then bundles with Vite. The output is placed in `frontend/dist/`. Deploy this directory to your static host or serve it via Nginx/Apache behind the backend API.

### Backend Docker Image

```bash
cd backend && docker build -t securo-backend .
```

The Dockerfile installs dependencies from `uv.lock` (which is exported with hashes and fed to pip for determinism), then copies source files. CI rebuilds this image after every dependency change in `pyproject.toml`.

## Database Migrations

### Apply Pending Migrations

```bash
cd backend && uv run alembic upgrade head
```

Runs all pending migrations from the current database schema up to the latest revision defined in `alembic/versions/`.

### Creating a New Migration

```bash
cd backend && uv run alembic revision --autogenerate -m "Add new field to accounts"
```

The migration script is placed in `backend/alembic/versions/` with an auto-generated name like `076_add_new_field_to_accounts.py`. It must reference the previous migration via `down_revision = "075"` (or `"base"` for the first migration). CI validates that revisions form a single linear chain — two concurrent migrations with colliding numbers will cause one of them to fail.

## Environment Setup

### Initial Setup from Scratch

```bash
curl -fsSL https://usesecuro.com/install.sh | bash
```

This script checks for Docker or Podman, installs the missing runtime if needed, builds images, and starts services. It also creates an `install.log` file that records which steps it performed.

### Manual Environment Variables

Edit `.env` (or pass them on the CLI) to configure:

| Variable | Default / Example |
|----------|-------------------|
| `DEBUG` | `true` (set `false` in production) |
| `SECRET_KEY` | Change this immediately — never use the default value. |
| `FRONTEND_URL` | `http://localhost:3000` or your domain. Used for CORS and OAuth callbacks. |
| `OIDC_ENABLED` | `true` to enable SSO login via an OIDC provider. |
| `AGENTS_ENABLED` | `false` by default — set to `true` to start the MCP server. |
| `AGENTS_DEFAULT_PROVIDER` | `ollama`, `openai`, or `anthropic`. |

See `.env.example` for a full list of available variables and their descriptions.

## Utilities

### Regenerate Lockfile

After changing dependencies in `backend/pyproject.toml`:

```bash
./scripts/lock.sh
```

This re-generates `uv.lock` with hashes, which is what CI uses to verify reproducibility. Commit the updated lockfile alongside your dependency changes.

### Check Migration Chain Integrity

```bash
cd backend && python3 scripts/check_migration_chain.py
```

Walks through `alembic/versions/*.py`, sorts by revision number, and verifies that each migration references its predecessor correctly. Useful after manually editing revisions or rebasing a branch.

## Notes on `mise`

The repo ships with a `mise.toml` manifest for managing Python and Node versions per directory:

```bash
mise //...:install          # Installs all tools (Python, Node) + project deps
mise backend:test           # Runs pytest from the backend context
mise frontend:lint          # Runs ESLint from the frontend context
```

This is optional; plain `uv` and `npm` commands work just as well. The mise manifest keeps `.python-version` files in sync across machines.
