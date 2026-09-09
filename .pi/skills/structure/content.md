# Repository Structure

## Directory Tree (Top-Level)

```
securo/                          # Repository root
├── backend/                    # FastAPI application
│   ├── alembic/               # Database migrations (versions/)
│   │   └── versions/         # Alembic migration scripts
│   ├── app/                   # Main package
│   │   ├── api/              # FastAPI routers, one file per domain
│   │   ├── agents/           # Optional AI agents feature (MCP server)
│   │   ├── core/             # Config, database session factory, rate limits
│   │   ├── fiscal/           # Fiscal year logic
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic models for API request/response
│   │   ├── services/         # Business logic (budget_service, transaction_service...)
│   │   ├── tasks/            # Celery task definitions
│   │   └── providers/        # Bank connection providers (pluggy, enable_banking, simplefin)
│   ├── migrations/           # Alembic migration scripts (legacy, kept for compatibility)
│   ├── pyproject.toml       # Dependencies + ruff/ty config
│   ├── tests/               # pytest test suite
│   └── uv.lock              # Locked dependency versions (same as CI)
├── frontend/                  # Vite React app
│   ├── src/
│   │   ├── App.tsx          # Root component with routing, providers
│   │   ├── components/      # Reusable UI components (modals, tables, dialogs)
│   │   ├── contexts/        # React Context (auth-context, workspace-context)
│   │   ├── lib/             # Utilities (api client, date formatting)
│   │   ├── locales/         # i18n translations (EN + PT-BR JSON files)
│   │   └── pages/           # Route-level page components (dashboard, login, etc.)
│   ├── vite.config.ts       # Vite config with React plugin
│   └── package.json         # NPM dependencies + dev scripts
├── docker-compose.yml        # Full stack: db, redis, backend, frontend
├── docker-compose.prod.yml   # Production compose (volumes not exposed)
├── install.sh               # One-liner installer for Linux/macOS
├── docs/                    # Design docs, RFCs, large screenshots
└── .pre-commit-config.yaml  # Lint/type check hooks (ruff, ty)
```

## Key Directories — Purpose & Ownership

| Path | Owned By | Purpose |
|------|----------|---------|
| `backend/app/api/` | Backend team | FastAPI routers. Each file exports a single router mounted at `/api/{domain}` (e.g., `/api/accounts`, `/api/transactions`). Contains route handlers, Pydantic request/response schemas, and endpoint-level logic like authentication guards. |
| `backend/app/models/` | Backend team | SQLAlchemy ORM models with relationships defined via `relationship()` and `mapped_column()`. UUID primary keys everywhere. Async sessions managed by `async_session_maker`. |
| `backend/app/services/` | Backend team | Pure business logic, decoupled from HTTP layers. Services are imported by routers and tasks independently; they have no knowledge of FastAPI or Celery. |
| `backend/app/tasks/` | Backend team | Celery task definitions (e.g., sync tasks that run on a schedule or when triggered). Tasks import services for their work but remain agnostic to the HTTP API. |
| `backend/app/providers/` | Backend team | Bank connection providers implementing the same interface. Pluggy handles Brazilian banks via OAuth, Enable Banking handles PSD2 European banks, SimpleFIN handles US banks. New providers follow the same pattern. |
| `frontend/src/components/` | Frontend team | Reusable UI components built on Radix UI primitives and shadcn-style composability. Organized by component system (data table, dropdown menu, dialog, etc.). |
| `frontend/src/pages/` | Frontend team | One file per top-level route. Rendered inside a protected route with providers (`AuthProvider`, `WorkspaceProvider`, `CollectionFilterProvider`). Lazy-loaded via React.lazy for code-splitting. |
| `docs/` | Docs team | RFCs (e.g., RFC-235 on investment ledger), design documents, and large screenshots documenting UI behavior or proposed features. |

## File Naming Conventions

- **Backend models:** `snake_case.py` — e.g., `account.py`, `transaction.py`. Each file defines one model class at the top level.
- **Frontend pages:** PascalCase filenames matching route paths, e.g. `DashboardPage.tsx`, `LoginPage.tsx`.
- **Alembic migrations:** Numbered sequentially as zero-padded strings (e.g. `076_...`). A new migration must reference its predecessor via `down_revision` to maintain a single linear chain.

## Environment Files

| File | Purpose |
|------|---------|
| `.env` | Local development overrides (not committed) |
| `.env.example` | Template of all configurable environment variables with defaults |
| `backend/pyproject.toml` | Python dependencies, ruff/ty configuration |
| `frontend/package.json` | NPM packages and scripts |
