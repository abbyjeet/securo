---
title: Project Structure — Directory Layout & File Purposes
description: Complete reference for Securo's repository layout, explaining the purpose and contents of every major directory. Helps you locate files when asked to "check migrations," "find where budgets are calculated," or "see what changed in this PR." Includes a step-by-step checklist for adding new features end-to-end across all layers (database → backend API → frontend UI).
---

# Securo — Project Structure & File Layout

This skill explains the purpose and contents of every major directory in the repository. It helps you locate files when asked to "check the migrations," "find where budgets are calculated," or "see what changed in this PR."

---

## Repository Root (`/home/abhijit/git/securo/`)

```
securo/
├── backend/                    # Python FastAPI server (SQLAlchemy + Celery)
│   ├── alembic/               # Database migrations
│   │   └── versions/          # Migration scripts (one per schema change)
│   ├── app/                   # Main application package
│   │   ├── api/              # FastAPI routers — one file per domain endpoint
│   │   ├── agents/           # Optional AI agents feature (MCP server)
│   │   ├── core/             # App config, database session factory, rate limits
│   │   ├── fiscal/           # Fiscal year logic
│   │   ├── models/          # SQLAlchemy ORM models with relationships
│   │   ├── schemas/         # Pydantic v2 request/response models
│   │   ├── services/        # Pure business logic (decoupled from HTTP)
│   │   └── tasks/           # Celery task definitions for async work
│   ├── migrations/           # Alembic migration scripts (symlinked or copied)
│   ├── pyproject.toml      # Dependencies + ruff/ty config
│   ├── run.py              # Entry point for the API server
│   └── tests/               # Pytest test suite (asyncio_mode = "auto")
│
├── frontend/                  # Vite React app (TypeScript, Tailwind CSS v4)
│   ├── src/
│   │   ├── components/     # Radix UI primitives, shadcn-like components
│   │   ├── contexts/       # React Context providers (auth, workspace)
│   │   ├── hooks/          # Custom custom hooks
│   │   ├── lib/            # Shared utilities: API client, date utils
│   │   └── pages/         # Route-level page components (lazy-loaded)
│   ├── index.html
│   ├── vite.config.ts      # Vite config with React plugin
│   └── package.json        # NPM dependencies + scripts
│
├── docker-compose.yml       # Full stack: db, redis, backend, frontend
├── docker-compose.prod.yml  # Production compose (no volumes exposed)
├── install.sh              # One-liner installer for Linux/macOS
└── docs/                   # Design docs, RFCs, screenshots
    ├── rfc-*.md           # Formal design documents
    └── pr-*/*             # PR-level design docs with diagrams
```

---

## `backend/app/api/` — FastAPI Routers

Each file exports a single router that gets mounted at `/api/{domain}`. This keeps endpoints organized by domain rather than by HTTP method:

| File | Mount Path | Purpose |
|------|-----------|---------|
| `workspaces.py` | `/api/workspaces/` | CRUD for workspaces (list, get current, create, update, archive) |
| `members.py` | `/api/members/` | Workspace member invites and removals |
| `accounts.py` | `/api/accounts/` | Bank accounts (synced via Pluggy/Enable Banking/SimpleFIN) |
| `transactions.py` | `/api/transactions/` | Transaction list, categories, splitting |
| ... | ... | ... |

**Why one router per domain?** It makes it easy to group related routes, share middleware per-domain, and reason about a feature's full API surface in one place.

---

## `backend/app/models/` — SQLAlchemy ORM

Models live here with full docstrings explaining each field's purpose and constraints:

```python
class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str]
    default_currency: Mapped[str]
    enable_envelope_budgeting: Mapped[bool] = (  # ← newly added field
        mapped_column(Boolean, default=False, server_default="false")
    )
```

Models define the database schema. Relationships (`relationship()`) are defined in the same file to avoid circular import issues.

---

## `backend/app/schemas/` — Pydantic v2 Models

These define request/response shapes for the API. They act as the contract between frontend and backend:

| Schema | Used By |
|--------|---------|
| `WorkspaceCreate` | POST `/api/workspaces/` (user creates their primary workspace) |
| `WorkspaceUpdate` | PATCH `/api/workspaces/{id}/` (editing a workspace) |
| `WorkspaceRead`  | GET `/api/workspaces/current` and list endpoints |

**Important:** `WorkspaceRead.enable_envelope_budgeting: bool` has **no default**, so the server must always provide a value. This ensures clients never see an undefined field and always get a boolean (either `true` or `false`).

---

## `backend/app/services/` — Business Logic

Pure functions that encapsulate domain rules, independent of FastAPI:

```python
def create_personal_workspace_for_user(
    user_id: str,
    name: str,
    currency: str,
    tax_jurisdiction: Optional[str],
) -> Workspace:
    """Create the primary workspace for a user.
    
    Defaults to enable_envelope_budgeting=True because envelope budgeting
    is a core feature of Securo and we want it opt-in per-workspace rather
    than opt-out globally.
    """
```

This keeps HTTP handlers thin — they just parse, validate, call the service, then serialize the response.

---

## `backend/app/tasks/` — Celery Background Jobs

Tasks like bank sync runs, report generation, or email notifications live here:

```python
@celery_app.task(bind=True)
def sync_accounts(self: "SyncTask", workspace_id: str) -> Dict[str, Any]:
    """Background task to fetch transactions from connected bank accounts."""
```

---

## `frontend/src/pages/` — Page Components

Each page is a lazy-loaded React component. They receive props (often the current user and workspace context) and render their own subcomponents:

| File | Route | Description |
|------|-------|-------------|
| `dashboard.tsx` | `/` | Overview of budgets, goals, recent transactions |
| `workspace-settings.tsx` | `/workspace/:id/settings` | Edit workspace name/icon + feature toggles |
| `transactions-page.tsx` | `/transactions` | Transaction list with category filtering |
| ... | ... | ... |

---

## `frontend/src/components/ui/` — Reusable UI Components

Built on top of Radix UI primitives:

```tsx
// @/components/ui/switch.tsx
export const Switch = React.forwardRef<HTMLButtonElement, { checked: boolean; onChange: () => void }>(...)
```

These are composed into pages and sections. The `SwitchSection` pattern wraps a label + switch in a consistent card layout.

---

## `frontend/src/lib/api.ts` — Typed API Client

A typed wrapper around the raw HTTP client that maps paths to functions with full type safety:

```ts
export interface Workspace {
  id: string
  name: string
  default_currency: string
  enable_envelope_budgeting: boolean  // ← always present on read
}

export const workspaces = {
  list: async (): Promise<Workspace[]> => { ... },
  current: async (): Promise<Workspace> => { ... },
  update: async (id: string, payload: Partial<Workspace>) => { ... },
}
```

TypeScript will catch missing fields at build time. The `Partial<Workspace>` type ensures you can omit optional fields when creating/updating a workspace.

---

## `frontend/src/locales/{lang}.json` — i18n Files

All text in the app is extracted into JSON files per language. When adding a new string, add it to every locale file with a native translation:

```json
{
  "workspace": {
    "enableEnvelopeBudgeting": "Orçamento de envelope ativado",
    "enableEnvelopeBudgetingHint": "Desmarque para desativar."
  }
}
```

---

## `frontend/src/contexts/workspace-context.tsx` — Context Provider

Provides the current workspace ID to all components deep in the tree. Used for routing and permissions:

```tsx
const WorkspaceProvider = ({ children }: { children: React.ReactNode }) => {
  const [currentId, setCurrent] = useWorkspace()
  // ...
}
```

The `useWorkspace` hook inside a page component returns `{ id?: string | null }`. If it's null (no workspace selected), the app redirects or shows a fallback view.

---

## How to Add a New Feature End-to-End

1. **Database:** Write an Alembic migration (`backend/alembic/versions/xxxx_add_*.py`)
2. **Model:** Add column + docstring in `backend/app/models/workspace.py`
3. **Service:** Decide defaults (e.g., primary=`true`, secondary=`false`) and implement in `backend/app/services/workspace_service.py`
4. **Schema:** Add the field to all three Pydantic models (`WorkspaceRead`, `WorkspaceCreate`, `WorkspaceUpdate`)
5. **API Router:** Implement the PATCH endpoint handler + debug logging in `backend/app/api/workspaces.py`
6. **Frontend API client:** Extend types and implement request/response functions in `frontend/src/lib/api.ts`
7. **Page component:** Add state, observer, sync effect, UI components, mutations to the relevant page (e.g., `workspace-settings.tsx`)
8. **i18n:** Add translations to all 13 locale files

This checklist ensures consistency across layers and prevents bugs like "backend saves it but frontend never reads it."
