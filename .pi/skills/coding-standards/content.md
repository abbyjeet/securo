# Coding Standards & Conventions

## Philosophy

> "We don't review the AI, we review you." — CONTRIBUTING.md

Whatever tool produced a diff doesn't matter. What matters is whether *you* understand it, can defend it in review, and will own it after merge. Use these standards as your checklist against that bar.

---

## Backend (Python)

### Linting & Type Checking Tools

| Tool | Command | Config file |
|------|---------|-------------|
| Ruff (linter) | `uv run ruff check .` | `backend/pyproject.toml` → `[tool.ruff]` |
| Ty (type checker) | `uv run ty check .` | Same `pyproject.toml` under `[tool.ty.environment]` |

Both tools read their configuration from `backend/pyproject.toml`, ensuring local and CI behavior stay in sync.

### Ruff Rules (`[tool.ruff.lint]`)

```toml
select = ["E4", "E7", "E9", "F"]  # errors, non-cognitive warnings only
ignore = ["E711", "E712"]         # None vs. empty container; True/False comparisons
target-version = "py311"          # oldest Python version we support
```

- **Only errors are checked.** Cognitive-style warnings (`W*`) are intentionally disabled to avoid noise. If a new rule needs adding, discuss it on Discord or in an issue — don't just enable it silently.
- **`E711` and `E712` are ignored** because they clash with SQLAlchemy's use of sentinel objects as default values for optional columns.

### Ty Configuration (`[tool.ty.environment]`)

```toml
python-version = "3.11"   # match ruff's target-version so both see the same type errors
```

Ty is pinned to `==0.0.75` in `pyproject.toml`. Each 0.0.x release adds new checks, and we bump together with any required annotation changes to avoid CI flakiness on unrelated PRs.

### Type Hints & Imports

- Every function parameter and return type is annotated.
- Use `from __future__ import annotations` at the top of files that need recursive types (e.g., SQLAlchemy models referencing themselves).
- Import guards with `TYPE_CHECKING:` to avoid circular imports in models:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.transaction import Transaction
```

- Use `TypedDict` or `@dataclass(frozen=True)` for nested immutable types.

### SQLAlchemy Model Conventions

```python
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.bank_connection import BankConnection

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))           # checking, savings...
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=Decimal("0.00"))

    connection: Optional["BankConnection"] = relationship(back_populates="accounts")
```

Notes from the pattern above:
- **UUID primary keys** everywhere — no autoincrement integers. Use `uuid.uuid4()` as a default factory.
- **`M[...] = mapped_column(...)`** syntax with explicit type hints on attributes, not just docstrings.
- Relationships use `back_populates=` to keep the bidirectional graph consistent in both directions.
- Columns that are truly optional have `nullable=True` and a nullable type hint (`Optional[str]`).

### Decimal Arithmetic — Never Float for Money

Money is always represented as `Decimal`, never `float`. Example:

```python
from decimal import Decimal

price = Decimal("19.99")
quantity = 2
total = price * quantity        # Decimal("39.98") ✓
# total = price * quantity      # float(39.979999...) ✗
```

In model definitions, declare money columns as `Numeric(precision=15, scale=2)` to match the database type and get full precision preserved in ORM queries.

---

## Frontend (TypeScript / React)

### TypeScript Config

Frontend uses `typescript@~5.9.x` with strict mode enabled. The build step (`npm run typecheck`) runs `tsc -b`, which checks all `.ts` and `.tsx` files in `src/`. Errors are surfaced before the bundle is emitted.

```jsonc
// frontend/tsconfig.json (relevant excerpt)
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2022",
    "module": "ESNext",
    "skipLibCheck": false   // we want type errors in our code to block the build
  }
}
```

### Component Patterns

- **Lazy-loaded route components** — each page is a separate file imported via `React.lazy()`. This keeps the initial bundle small and allows Vite to tree-shake unused chunks.

```tsx
// frontend/src/App.tsx
const DashboardPage = lazy(() => import('@/pages/dashboard'))
const TransactionsPage = lazy(() => import('@/pages/transactions'))

<Route path="/" element={<DashboardPage />} />
<Route path="/transactions" element={<TransactionsPage />} />
```

- **Providers wrap the router** — `ThemeProvider`, `QueryClientProvider`, and data providers sit outside `<Suspense>` so they initialize before any route is rendered.

```tsx
<ThemeProvider>
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <BrowserRouter>
        <AuthProvider>
          <WorkspaceProvider>
            <Suspense fallback={<LoadingFallback />}>
              <Routes> ... </Routes>
            </Suspense>
          </WorkspaceProvider>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
</ThemeProvider>
```

- **Forms use React Hook Form + Zod** — validation schemas live in `src/schemas/` and are reused across multiple forms to avoid duplication.

### Styling — Tailwind CSS v4

Utility classes are preferred over custom CSS. Animation utilities come from the `tw-animate-css` npm package. Example:

```tsx
<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
<button
  disabled={isSubmitting}
  onClick={handleSubmit}
>
  Save changes
</button>
```

---

## General Rules

### Feature Flagging — Zero-Cost by Default

Optional features (AI agents, bank sync providers) are guarded by environment variables and conditionally imported at runtime. This ensures that a user who disables `AGENTS_ENABLED` never pays for those dependencies:

- No imports of the feature's code
- No background tasks spawned
- No network calls made

The MCP server module is a good example — it lives in `app/agents/`, sits entirely inside an `if os.getenv("AGENTS_ENABLED", ...) == "true"` guard, and only gets imported when that flag is set.

### Alembic Migration Numbering

Each migration file in `backend/alembic/versions/` must be named with a unique, zero-padded integer prefix (e.g., `076_add_field.py`). The revision string inside the module must match that number:

```python
revision = "076"
down_revision = "075"  # or None for the very first migration
```

CI checks that revisions form a single linear chain against the merged branch. If two PRs propose `077` simultaneously, one will fail during CI's merge check — pick the other up and re-number.

### Pre-commit Hooks

Run locally before pushing:

```bash
prek install                 # or: pip install pre-commit && pre-commit install
prek run --all-files         # runs ruff + ty on all staged files
```

The hooks are defined in `.pre-commit-config.yaml` and configured to pass filenames through unchanged, so they always scan the entire repo rather than just staged changes.
