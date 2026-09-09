# PROJECT KNOWLEDGE BASE

**Generated:** 2025-09-08

## OVERVIEW

**Project:** Securo — Self-hosted personal finance manager  
**License:** AGPL-3.0  
**Website:** https://usesecuro.com/  

A privacy-first, self-hosted personal finance application that gives users full control over their financial data without surrendering it to third parties. Supports bank sync (Pluggy for Brazilian banks, Enable Banking for European PSD2 banks, SimpleFIN for US/international), multi-currency, budgets, goals, asset tracking, AI agents with MCP tool-use, and more.

**Tech Stack:**
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x (asyncpg driver), Celery + Redis for background tasks, Alembic for migrations, Pydantic v2 for schemas
- **Frontend:** React 19, TypeScript 5.9, Vite 8, Tailwind CSS 4, TanStack Query, Zod validation, i18n (i18next with EN + PT-BR)
- **Database:** PostgreSQL 16+ with pgvector extension
- **Queue:** Redis + Celery workers

## STRUCTURE

```
securo/                          # Repository root
├── backend/                    # FastAPI application
│   ├── alembic/               # Database migrations (versions/)
│   ├── app/                   # Main package
│   │   ├── api/              # FastAPI routers, one file per domain
│   │   ├── agents/           # Optional AI agents feature (MCP server)
│   │   ├── core/             # Config, database session factory, rate limits
│   │   ├── fiscal/           # Fiscal year logic
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic models for API request/response
│   │   ├── services/         # Business logic (budget_service, transaction_service, etc.)
│   │   ├── tasks/            # Celery task definitions
│   │   └── providers/        # Bank connection providers (pluggy, enable_banking, simplefin)
│   ├── migrations/           # Alembic migration scripts
│   ├── pyproject.toml       # Dependencies + ruff/ty config
│   └── tests/               # pytest test suite (asyncio_mode = "auto")
├── frontend/                  # Vite React app
│   ├── src/
│   │   ├── components/     # Radix UI primitives, shadcn-like components
│   │   ├── contexts/       # React Context providers (auth, workspace)
│   │   ├── lib/            # Reusable utilities (api client, date utils)
│   │   ├── pages/          # Route-level page components
│   │   └── App.tsx        # Root component with routing
│   ├── vite.config.ts      # Vite config with React plugin
│   └── package.json        # NPM deps + dev scripts
├── docker-compose.yml       # Full stack (db, redis, backend, frontend)
├── docker-compose.prod.yml  # Production compose (no volumes exposed)
├── install.sh              # One-liner installer for Linux/macOS
└── docs/                   # Design docs, RFCs, screenshots
```

### Key Directories

| Path | Purpose |
|------|---------|
| `backend/app/api/` | FastAPI routers — each file exports a single router mounted at `/api/{domain}` |
| `backend/app/models/` | SQLAlchemy ORM models with relationships defined via `relationship()` and `mapped_column()` |
| `backend/app/services/` | Pure business logic, decoupled from HTTP layers |
| `backend/app/tasks/` | Celery task definitions (sync tasks run in background workers) |
| `frontend/src/pages/` | One file per top-level route; lazy-loaded via React.lazy() |
| `docs/` | RFCs, design docs, and large screenshots for reference |

## COMMANDS

| Action | Command | Notes |
|--------|---------|-------|
| **Start dev server** | `docker compose up --build` | Builds all images; frontend mounts `/workspace:ro` for hot-reload |
| **Backend tests** | `cd backend && uv sync --all-extras && uv run pytest` | From repo root, or `mise backend:test` |
| **Frontend lint** | `cd frontend && npm run lint` | ESLint + TypeScript check |
| **Frontend build** | `cd frontend && npm run build` | Runs typecheck first via `npm run typecheck` |
| **Backend lint** | `cd backend && uv run ruff check .` | Configured in `pyproject.toml`; targets Python 3.11 |
| **Backend type check** | `cd backend && uv run ty check .` | Statically checks all modules; errors propagate across imports |
| **Regenerate lockfile** | `./scripts/lock.sh` | Re-generates `uv.lock` after changing `pyproject.toml` deps |
| **Check migration chain** | `python3 backend/scripts/check_migration_chain.py` | Ensures migrations are numbered sequentially |
| **Apply all migrations** | `alembic upgrade head` | Run from `backend/` directory |

## CODING STANDARDS

### Backend (Python)

- **Linter:** Ruff 0.16–0.17 (pinned upper bound to avoid reformats of historical imports like alembic migrations)
  - `select = ["E4", "E7", "E9", "F"]` — only errors, non-cognitive warnings ignored (`ignore = ["E711", "E712"]`)
- **Type checker:** Ty (pinned to 0.0.75)
- **Formatting:** Ruff format is *not* used; existing formatting preserved intentionally
- **Style:**
  - Type hints on all function parameters and return types
  - `TYPE_CHECKING` guards for circular imports in models
  - SQLAlchemy models use `Mapped[...] = mapped_column(...)` pattern with explicit `relationship()` backlinks
  - Decimal arithmetic (never float) for money; use `Decimal("0.00")` literals
  - UUIDs as primary keys everywhere (`uuid.uuid4()` default)
  - Async sessions via context managers: `async with async_session_maker() as session:`

### Frontend (TypeScript/React)

- **Type checker:** TypeScript ~5.9, checked on every build via `npm run typecheck`
- **Styling:** Tailwind CSS v4 utility classes + `tw-animate-css` for animations
- **Components:** Radix UI primitives under the hood; shadcn-style composability
- **State:** TanStack Query for server state (`@tanstack/react-query`)
- **Routing:** React Router DOM with lazy-loaded route components via `React.lazy()`
- **Forms:** React Hook Form + Zod schemas for validation
- **Testing:** Vitest + Testing Library; render through `renderWithProviders` helper (wires up QueryClient, router, i18n)

### General Rules

- **Feature flagging:** Optional features (e.g., AI agents) are guarded by environment flags and conditionally imported to avoid cost for users who opt out
- **Migration numbering:** Each alembic revision in `backend/alembic/versions/` must be a unique sequential string (CI validates this against merged branches)
- **Pre-commit hooks** run on commit (via pre-commit or prek): `ruff check`, `ty check`, migration chain validation

## WHERE TO LOOK

| Concern | Location |
|---------|----------|
| API routes & request/response shapes | `backend/app/api/` + `backend/app/schemas/` |
| Database schema | `backend/app/models/` + `backend/alembic/versions/` |
| Business logic | `backend/app/services/` |
| Celery tasks | `backend/app/tasks/` |
| Bank sync providers | `backend/app/providers/{pluggy,enable_banking,simplefin,...}` |
| Frontend routes | `frontend/src/pages/*.tsx` |
| Shared UI components | `frontend/src/components/` |
| i18n translations | `frontend/src/locales/*.json` (EN + PT-BR) |
| Design docs & RFCs | `docs/rfc-*.md`, `docs/pr-*/*` |

## NOTES

- **Optional features are zero-cost by default:** AI agents, bank sync providers, and other opt-in features are fully gated behind environment variables. Users who don't enable them incur no imports, no network calls, no background tasks.
- **The MCP server is modular:** It lives in `backend/mcp_server/` as a separate uvicorn app that can be run alongside the API on port 8765. Only starts under the `agents` compose profile or when `AGENTS_ENABLED=true`.
- **Database migrations must be chained:** Every new migration file (`alembic/versions/*.py`) is numbered sequentially and references its predecessor via `down_revision`. CI checks this by inspecting the merged branch — a clash between two PRs will fail on one of them.
- **The Tesouro Direto cache warmup** runs at startup but only for workspaces whose default currency is BRL (Brazilian Real). It avoids unnecessary calls to Brazil's government API for deployments serving other regions.
- **OIDC-only mode:** When `OIDC_ENABLED=true` and local auth disabled, Securo becomes SSO-only. Existing password-backed accounts remain; they simply cannot log in unless linked via the OIDC identity or re-provisioned through the provider.
- **Passkeys require HTTPS (except localhost):** Follows WebAuthn spec — plain HTTP is never valid for credential generation. `WEBAUTHN_RP_ID` should be set to a parent domain when Securo is served under multiple subdomains.
