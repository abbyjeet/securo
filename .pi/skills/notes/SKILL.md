---
title: Critical Context & Gotchas — Securo Frontend
description: Known bugs, design decisions, migration considerations, and debugging tips for the frontend codebase. Covers the envelope budgeting persistence bug (React Query invalidation gotcha), why staleTime=0 is used on detail queries, when to use local state vs server-state, migration backward compatibility strategies, API client type safety rules, and feature flag patterns.
---

# Critical Context & Gotchas — Securo Frontend

## The Envelope Budgeting Persistence Bug (Fixed)

### Symptom
Toggle ON → Click Save → Navigate away → Come back → Toggle shows OFF.

Backend was correctly persisting the value in PostgreSQL. The frontend was displaying stale data that never updated on page reload.

### Root Cause
React Query's `invalidateQueries()` only triggers a re-fetch **if there is an active observer** listening to that query key at render time.

The Workspace Settings component originally read its data from a Context provider (`useWorkspace`), not from a React Query cache entry. When we called:

```ts
queryClient.invalidateQueries({ queryKey: ['workspaces.list'] })
```

...there was **no active observer** on `'workspaces.list'`, so the invalidation did nothing useful. The cached Context value remained stale forever.

### The Fix
Added an explicit `useQuery` observer directly in this component that observes `/workspaces/current`:

```ts
const { data: currentWorkspaceData } = useQuery({
  queryKey: ['workspace.detail', current?.id],
  queryFn: () => workspacesApi.current(),
  enabled: !!current,
  staleTime: 0,  // ← KEY: refetches from server on next render after invalidation
})

useEffect(() => {
  if (!currentWorkspaceData) return
  setEditName(currentWorkspaceData.name ?? '')
  setEnableEnvelopeBudgeting(currentWorkspaceData.enable_envelope_budgeting ?? false),
  // ... sync other fields
}, [currentWorkspaceData])
```

Now the flow is:
1. Mutation succeeds → `onSuccess` fires
2. `invalidateQueries(['workspace.detail', current?.id])` called
3. The active observer (`useQuery`) detects invalidation + `staleTime: 0` → refetches immediately
4. `currentWorkspaceData.enable_envelope_budgeting` holds the fresh value from DB
5. `useEffect` syncs it back to local state → UI re-renders with toggle ON ✅

### Why This Pattern Matters
This is a general pattern for any page that:
- Edits persisted data via mutations
- Needs to reflect server changes immediately after mutation
- May navigate away and come back (e.g., workspace switcher, browser refresh)

**Never invalidate a query key unless some component is actively observing it.** Always pair your invalidation with an active `useQuery` observer.

---

## Design Decisions & Rationale

### Why Primary Workspace Defaults to `enable_envelope_budgeting: true`
- The primary workspace is created at user registration (first-time setup).
- Envelope budgeting is a core feature of Securo's value proposition.
- Secondary workspaces (created later via "Create another") default to `false`, allowing users to opt-in per-workspace as needed.

### Why `staleTime: 0` on the Detail Query
- This page edits its own data — immediate feedback is expected.
- `staleTime: 5min` would cause a flash of stale data after mutation.
- The trade-off: we refetch slightly more often, but it's a single-page form so network cost is negligible compared to user experience.

### Why We Use Local State + Sync Effect Instead of Pure Server-State
| Scenario | Approach |
|----------|----------|
| User editing a form, needs immediate validation feedback | **Local state** (`useState`), synced from server via `useEffect` after mutation succeeds |
| Data is read-only and rarely changes (e.g., list of currencies) | Server-state with high `staleTime` (e.g., `Infinity`) |
| User navigates away and back, must see latest server value | Active observer with `staleTime: 0` + `useEffect` sync |
| Simple app state not backed by HTTP (sidebar open/closed, modal visibility) | Local state (`useState`, `Context`) is fine |

**Rule of thumb:** If the data changes via a mutation and you need to reflect that change on page reload or after navigation, it must be observable via React Query. Context alone is insufficient for that guarantee.

---

## Future Considerations

### Multi-Workspace UI (Switcher)
When you add a workspace switcher that lets users jump between workspaces:
- Each workspace detail should be a **separate active observer** or use `useSuspenseQuery` to avoid parallel fetching.
- If one page is editing Workspace A and another navigates to Workspace B, consider using `staleTime: 0` on the target only (via navigation) to avoid race conditions where both queries fire simultaneously.

### Migration for Existing Data
If you add this column after a release:
- Pre-migration rows will have `NULL`. The model's `default=False` handles new rows.
- Run a data migration script to backfill existing workspaces (e.g., set based on some heuristic, or leave as-is and let users toggle it the first time).
- In the UI: use `?? false` when syncing from server so old rows don't crash the component.

### TypeScript Strictness
When adding new fields to API responses, always update your type definitions in `frontend/src/lib/api.ts`. If you rely on raw HTTP calls without typed wrappers, runtime errors can slip through (e.g., sending a string `"true"` instead of boolean `true` for a BOOLEAN field). The backend will coerce types loosely, but the frontend client should enforce them strictly.

---

## Related Skills
- `frontend-patterns/SKILL.md` — component patterns, React Query usage, form state sync
- `coding-standards/SKILL.md` — type hints, linting rules, migration conventions
