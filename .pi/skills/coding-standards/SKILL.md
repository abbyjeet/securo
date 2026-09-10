---
title: Coding Standards — Python, TypeScript & Database Migrations
description: Linting rules, type conventions, formatting guidelines, migration best practices, and architectural patterns for Securo's backend (Python/FastAPI/SQLAlchemy) and frontend (TypeScript/React). Covers API contract discipline, partial type usage rules, migration strategies with server_default, import ordering, feature flagging patterns, and debug logging conventions.
---

# Securo — Coding Standards & Best Practices

This skill codifies the linting rules, type conventions, and architectural patterns used across Securo's codebase. It captures lessons learned from real bugs (like the envelope budgeting persistence issue) and design decisions that have been validated in production.

---

## Type Safety & API Contracts

### Always Define Full Shapes in Your API Client Types

```ts
// ❌ BAD: Missing fields lead to runtime errors when backend adds a new column
export interface Workspace {
  id: string
  name: string
}

// ✅ GOOD: Full, explicit type that includes optional/nullable fields
export interface Workspace {
  id: string
  name: string
  default_currency?: string | null
  locale?: string | null
  tax_jurisdiction?: string | null
  icon?: IconName | null
  color?: string | null
  enable_envelope_budgeting: boolean  // ← always include it, even if optional on write
}
```

**Why:** The backend may add a new column with `DEFAULT false`. If your TypeScript client doesn't know about it, you'll never validate its presence or type. A mutation might silently send `{ name: "foo" }` when the server expects `{ name: "foo", enable_envelope_budgeting: true/false }`, and the backend will either reject it or silently ignore it.

### Use `Partial<YourType>` Only at Call Sites, Not in Interface Definitions

```ts
// ❌ BAD: Hides required fields from callers
export interface UpdateWorkspaceRequest {
  name?: string
  enable_envelope_budgeting?: boolean
}

// ✅ GOOD: Keep the full shape; partial-ness is handled by the function signature
export const workspaces = {
  update: async (id: string, payload: Partial<Workspace>) => {
    // If you want stricter validation, specify exactly what gets sent:
    return api.patch(`/workspaces/${id}`, {
      name: editName,
      default_currency: editCurrency,
      locale: editLocale || null as unknown as string,
      enable_envelope_budgeting: enableEnvelopeBudgeting,
    })
  }
}
```

---

## React Query Anti-Patterns (and Their Fixes)

| Pattern | Why It's Wrong | Fix |
|---------|----------------|-----|
| Calling `invalidateQueries({ queryKey })` without an active observer on that key | The invalidation fires but no component re-fetches → UI stays stale forever | Add a `useQuery` with the same `queryKey` to this component, set `staleTime: 0`, and invalidate that key |
| Using `initialData` without a fallback to server fetch | On mount, you render cached (possibly stale) data; on refresh you never see updates | Combine `initialData` for fast first-load with `refetchOnWindowFocus: true` or `staleTime: 0` for correctness-critical fields |
| Invalidating all queries (`invalidateQueries({})`) in every mutation | Unnecessary network round-trips; wastes bandwidth and CPU on background queries that don't need refreshing | Invalidate only the specific keys that changed (e.g., `'workspace.detail'`, not `'workspaces.list'`) |

---

## State Management: When to Use Local vs. Server-State

| Scenario | Recommended Approach |
|----------|---------------------|
| User editing a form, needs immediate validation feedback | **Local state** (`useState`), synced from server via `useEffect` after mutation succeeds |
| Data is read-only and rarely changes (e.g., list of currencies) | Server-state with high `staleTime` (e.g., `Infinity`) |
| User navigates away and back, must see latest server value | Active observer with `staleTime: 0` + `useEffect` sync |
| Simple app state not backed by HTTP (sidebar open/closed, modal visibility) | Local state (`useState`, `Context`) is fine |

**Rule of thumb:** If the data changes via a mutation and you need to reflect that change on page reload or after navigation, it must be observable via React Query. Context alone is insufficient for that guarantee.

---

## Migration & Backward Compatibility

### Database Migrations

Always include `server_default` when adding a new column:

```python
# alembic/versions/e2b76c4208cb_add_enable_envelope_budgeting_to_workspaces.py
op.add_column('workspaces', sa.Column("enable_envelope_budgeting", sa.Boolean(), nullable=False, server_default="false"))
```

- `server_default="false"` ensures existing rows (pre-migration) get a sensible default without needing a backfill script.
- `nullable=False` is fine because we provide the default — Alembic generates an `ALTER TABLE ... ADD COLUMN DEFAULT false NOT NULL;` which PostgreSQL accepts even if some rows are `NULL`.

### Model Field Defaults

```python
enable_envelope_budgeting: Mapped[bool] = mapped_column(
    Boolean,
    default=False,           # ← used when SQLAlchemy inserts a NEW row (no server_default)
    server_default="false",  # ← this is what the DB uses for existing rows on migration
)
```

The Python-side `default=False` is only used when SQLAlchemy creates a **new** row (no INSERT happening yet). The `server_default` is what fills in old rows on migration.

---

## Imports Checklist

Before committing any `.tsx` or `.py` file, verify:

1. All hooks/components you use are imported at the top of the file.
2. No runtime errors from missing imports (TypeScript type-checking won't catch this).
3. Import order matches a consistent convention (e.g., React APIs first, then third-party deps, then local paths).

---

## Formatting & Linting

- **Python:** Ruff linter with `pyproject.toml` configured for Python 3.11. Warnings like `E711`, `E712` (comparing to `None`) are ignored intentionally — they're noise in our codebase and not worth auto-formatting away.
- **TypeScript:** TypeScript compiler runs on build (`npm run typecheck`). Errors propagate across imports, so a missing export can break the whole project's type-check pass. Fix errors before committing.

---

## Feature Flags & Zero-Cost Defaults

Optional features (AI agents, bank sync providers) are gated behind environment variables:

```ts
if (!AGENTS_ENABLED) {
  // never import this module; zero cost for users who don't enable it
} else {
  import('...mcp-server').then(...)
}
```

This keeps the default install lightweight and privacy-focused. Users opt-in to AI features by setting `AGENTS_ENABLED=true` before starting the server.

---

## Debug Logging Guidelines

Add `console.log` (or structured logs) at strategic points:

```ts
const updateMutation = useMutation({
  mutationFn: () => {
    console.log('[updateMutation] sending payload:', JSON.stringify({
      name: editName,
      enable_envelope_budgeting: enableEnvelopeBudgeting,
    }))
    return workspacesApi.update(current.id, ...)
  },
  onSuccess: () => {
    console.log('[updateMutation.onSuccess] mutation succeeded')
    // ... invalidation logic
  },
})
```

This helps you quickly confirm whether the frontend is actually sending what it thinks it's sending. The backend logs (`logger.info(...)`) tell you what the server received. Correlate the two to find mismatches (e.g., `"true"` vs `true`).

---

## Related Skills

- `frontend-patterns/SKILL.md` — component patterns, React Query usage, form state sync
- `structure/SKILL.md` — directory layout and purpose of each major folder
- `overview/SKILL.md` — high-level mission, tech stack, feature list
