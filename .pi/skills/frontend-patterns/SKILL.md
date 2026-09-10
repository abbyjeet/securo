---
title: Frontend Patterns — React, TypeScript & Tailwind CSS v4
description: "Reference guide for UI components, API integration patterns, state management strategies, and common anti-patterns in Securo's frontend stack. Covers WorkspaceSettingsPage, SwitchSection reusable component, section card layout rules, i18n key conventions, React Query observer/sync-effect pattern, mutation payload construction, invalidation best practices, and why staleTime: 0 matters for immediate feedback after mutations."
---

# Frontend Patterns — Securo React + TypeScript + Tailwind CSS v4

This skill documents component patterns, API integration patterns, state management strategies, and common anti-patterns encountered when building UI components in Securo's frontend stack.

## Core Principles

- **React Query is the source of truth.** Never rely on Context alone for data that changes via mutations — always pair with a React Query observer or invalidate actively observed queries.
- **`staleTime: 0`** means "refetch on every render after invalidation." Use this when you need fresh server data immediately (e.g., form fields after a save mutation).
- **Invalidations are inert without active observers.** `queryClient.invalidateQueries({ queryKey })` only does something if some component is *currently* observing that exact query key.
- **Imports matter at runtime.** TypeScript type-checking won't catch missing imports (e.g., `useEffect`) — they will cause runtime errors. Always verify the full import list matches every hook used in the file.

---

## Workspace Settings Page Pattern (`workspace-settings.tsx`)

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React Query Cache (server source of truth)              │
│     └─ useQuery('workspace.detail', staleTime: 0)       │
└──────────────┬──────────────────────────────────────────┘
               │ refetch on invalidation (staleTime=0)
               ▼
┌─────────────────────────────────────────────────────────┐
│  React Component State                                   │
│     └─ useEffect syncs currentWorkspaceData → form fields│
└──────────────┬──────────────────────────────────────────┘
               │ renders as controlled inputs + Switch
└─────────────────────────────────────────────────────────┘
```

### Key Imports (Complete List)

```ts
import { useMemo, useState, useEffect } from 'react'           // ← Must include useEffect!
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useDateLocale } from '@/hooks/use-display-locale'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { auth as authApi, currencies as currenciesApi, fiscal as fiscalApi, workspaces as workspacesApi } from '@/lib/api'
import { useAuth } from '@/contexts/auth-context'
import { useWorkspace } from '@/contexts/workspace-context'
import { useLocalAuthEnabled } from '@/hooks/use-local-auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'          // ← the toggle component
import { Skeleton } from '@/components/ui/skeleton'
import { IconPicker } from '@/components/icon-picker'
import { CategoryIcon } from '@/components/category-icon'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

// NOTE: If you use ANY of the above hooks/components and forget to import it,
// the app will crash at runtime with "Uncaught ReferenceError: X is not defined".
```

### State Variables

```ts
const [editName, setEditName] = useState('')
const [editCurrency, setEditCurrency] = useState('')
const [editLocale, setEditLocale] = useState('')
const [editJurisdiction, setEditJurisdiction] = useState('')
const [enableEnvelopeBudgeting, setEnableEnvelopeBudgeting] = useState(false)  // ← toggle state
const [editIcon, setEditIcon] = useState(DEFAULT_WORKSPACE_ICON)
const [editColor, setEditColor] = useState(DEFAULT_WORKSPACE_COLOR)

// Also keep track of workspace relationships for the switcher:
const [inviteOpen, setInviteOpen] = useState(false)
const [removeTarget, setRemoveTarget] = useState<WorkspaceMember | null>(null)
const [archiveOpen, setArchiveOpen] = useState(false)
```

### React Query Observer (The Active Listener)

```ts
// This is what makes invalidation work. Without this observer,
// invalidateQueries() does nothing useful in this component.
const { data: currentWorkspaceData } = useQuery({
  queryKey: ['workspace.detail', current?.id],
  queryFn: () => (current ? workspacesApi.current() : Promise.resolve(null)),
  enabled: !!current,
  staleTime: 0,  // ← KEY: refetches from server on next render after invalidation
  initialData: current || null,
})
```

### Sync Effect (Bridges Server → Local State)

```ts
useEffect(() => {
  if (!currentWorkspaceData) return
  setEditName(currentWorkspaceData.name ?? '')
  setEditCurrency(currentWorkspaceData.default_currency ?? '')
  setEditLocale(currentWorkspaceData.locale ?? '')
  setEditJurisdiction(currentWorkspaceData.tax_jurisdiction ?? '')
  setEditIcon(currentWorkspaceData.icon ?? DEFAULT_WORKSPACE_ICON)
  setEditColor(currentWorkspaceData.color ?? DEFAULT_WORKSPACE_COLOR)
  // For the toggle: use the fresh data from server, not local state.
  // If enable_envelope_budgeting is undefined (pre-migration rows), default to false.
  const savedValue = currentWorkspaceData.enable_envelope_budgeting ?? false
  setEnableEnvelopeBudgeting(savedValue)
}, [currentWorkspaceData])
```

### Mutation with Full Payload

```ts
const updateMutation = useMutation({
  mutationFn: () => {
    if (!current) throw new Error('No workspace')
    console.log('[updateMutation] sending payload:', JSON.stringify({
      name: editName,
      default_currency: editCurrency,
      locale: editLocale || null as unknown as string,
      tax_jurisdiction: editJurisdiction || null,
      icon: editIcon,
      color: editColor,
      enable_envelope_budgeting: enableEnvelopeBudgeting,  // ← MUST be sent!
    }))
    return workspacesApi.update(current.id, {
      name: editName,
      default_currency: editCurrency,
      locale: editLocale || (null as unknown as string),
      tax_jurisdiction: editJurisdiction || null,
      icon: editIcon,
      color: editColor,
      enable_envelope_budgeting: enableEnvelopeBudgeting,  // ← sent here too
    })
  },
  onSuccess: () => {
    toast.success(t('workspace.saveSuccess'))
    console.log('[updateMutation.onSuccess] mutation succeeded, enableEnvelopeBudgeting:', enableEnvelopeBudgeting)

    // Invalidate the query we are ACTUALLY observing.
    // If you invalidate a key that no component is listening to, nothing happens!
    void queryClient.invalidateQueries({ queryKey: ['workspace.detail', current?.id] })

    void authApi.me().then(updateUser).catch(() => {})
  },
  onError: (e) => {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || (e instanceof Error ? e.message : t('workspace.saveError'))
    toast.error(detail)
  },
})
```

### SwitchSection Component (Reusable UI)

```tsx
function SwitchSection({ name, checked, onChange }: { name: string; checked: boolean; onChange: () => void }) {
  return (
    <div className="flex items-center justify-between py-2">
      <Label htmlFor={name}>{t('workspace.' + name)}</Label>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  )
}

// Usage in JSX:
<SwitchSection name="enableEnvelopeBudgeting" checked={enableEnvelopeBudgeting} onChange={() => setEnableEnvelopeBudgeting(v => !v)} />
```

---

## Migration Checklist (Adding a New Field)

When adding a new persisted field to workspaces (or any other resource):

1. **Database migration** → add column with `DEFAULT` and `server_default`.
2. **Model** → add the typed field with docstring explaining its purpose and default behavior.
3. **Service** → decide which entities get what default value (e.g., primary workspace = `true`, secondary = `false`).
4. **Schema read** → include the field in `WorkspaceRead` schema (**no default**) so API returns server value.
5. **API endpoint** → add to PATCH handler; optionally log for debugging (`logger.info(...)`).
6. **Frontend type** → update your API client types or use a typed API wrapper that includes the field.
7. **Form state** → add `useState(false)` (or appropriate default) to your component.
8. **UI component** → add `<Switch checked={state} onChange={...} />` inside its own section card, NOT merged into another form grid.
9. **Sync effect** → if the field comes from server, sync it via a `useEffect` that depends on the active observer's data.
10. **i18n keys** → add translations to ALL locale files (en, de, es, fr, pt-BR, etc.).

---

## Common Mistakes & How to Avoid Them

| # | Mistake | Why It Fails | Fix |
|---|---------|--------------|-----|
| 1 | Forgetting `useEffect` in imports | Runtime crash: `Uncaught ReferenceError: useEffect is not defined` | Always check your import list against every hook you use. |
| 2 | Invalidating a query key nobody observes | `invalidateQueries()` silently does nothing; old cached value persists forever | Add an active observer (`useQuery({ queryKey, ... })`) before calling `invalidateQueries`. Set `staleTime: 0` so refetch happens on next render immediately. |
| 3 | Merging two sections into one grid | UI looks broken, fields get merged unexpectedly | Use `<section className="space-y-4 rounded-xl border bg-card p-6">` for each logical group (Details vs Features). Keep them as siblings, not nested inside the same inner form grid. |
| 4 | Using a checkbox instead of `Switch` | Accessibility and UX mismatch with design system | Use `<Switch>` from `@/components/ui/switch`. |
| 5 | Changing label text on hover (`group-hover:text-muted-foreground`) | Confusing user; looks like broken state | Never change text content based on hover or any pseudo-class. Keep labels static. |
| 6 | Using `null` instead of `""` for string fields in state | React treats them differently; can cause unexpected re-renders or incorrect comparisons | Normalize: strings → `''`, booleans → `false/true`, numbers → `0`. |
| 7 | Not syncing form state from server after mutation | UI shows stale values (e.g., toggle stays OFF after enabling) | Use a `useEffect` that watches the active observer's data and syncs all fields back to local state. |

---

## API Client Type Safety (`frontend/src/lib/api.ts`)

```ts
export interface Workspace {
  id: string
  name: string
  default_currency: string
  locale?: string | null
  tax_jurisdiction?: string | null
  icon?: IconName | null
  color?: string | null
  enable_envelope_budgeting: boolean  // ← new field must be typed here!
}

export const workspaces = {
  list: async (): Promise<Workspace[]> => { /* ... */ },
  current: async (): Promise<Workspace> => { /* ... */ },
  update: async (id: string, payload: Partial<Workspace>) => {
    // NOTE: TypeScript will complain if you omit enable_envelope_budgeting here.
    const res = await api.patch(`/workspaces/${id}`, payload)
    return res.data as Workspace
  },
}
```

If your typed client is missing a field, **TypeScript will catch it on build**. If you rely on raw HTTP calls without types, runtime errors can slip through (e.g., sending `"true"` instead of `true` for a BOOLEAN field). Always prefer the typed wrapper.

---

## Performance Notes

- **`staleTime: 0`** is fine for a single-form page like Workspace Settings where we expect immediate feedback after mutation. If you have dozens of components observing the same query with `staleTime: 0`, consider a compromise (e.g., `50ms`) to avoid thrashing.
- The `useEffect` that syncs server → local state re-runs on every successful fetch. That's intentional and only triggers once per mutation anyway (because we invalidate, then the observer refetches immediately).

---

## Environment Variables for Optional Features

Securo gates optional features behind env flags so they don't import or run unless enabled:

```bash
# Enable AI agents MCP server
export AGENTS_ENABLED=true

# Enable bank sync providers
export PLUGGY_API_KEY=...
export ENABLE_BANKING_CLIENT_ID=...
```

When `AGENTS_ENABLED=false` (the default), the entire `agents/` module is never imported, so users who don't need AI features incur zero overhead. This pattern applies to any optional feature: wrap its imports and usage in a runtime guard.
