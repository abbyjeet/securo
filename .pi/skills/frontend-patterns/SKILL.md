# Securo Frontend Patterns

This skill captures proven patterns, component structures, and best practices from the Securo codebase. Use this as a reference when building new UI elements or pages.

## Core Principles

- **All UI state is React state** (`useState`) — never rely on imperative DOM manipulation
- **i18n-first**: All strings must go through `t()` with keys under `workspace.*`, `common.*`, etc.
- **Shadcn/Radix primitives** under the hood: Button, Input, Select, Switch, Dialog, Popover, Badge, Skeleton, Avatar
- **Tailwind CSS v4** for all styling — use utility classes; avoid inline styles
- **Lucide React icons** via `lucide-react` — prefer named imports (e.g., `<Save />`, `<Plus />`) over generic `Icon` components
- **Form state is controlled**: Use `useState` + `onChange` for inputs, not uncontrolled inputs

## Component Structure Pattern

```tsx
export default function MyPage() {
  const { t } = useTranslation(); // i18n
  const navigate = useNavigate();   // routing
  const localeForFormat = useDateLocale(); // date formatting

  // State declarations — one per feature
  const [editName, setEditName] = useState('');
  const [enableEnvelopeBudgeting, setEnableEnvelopeBudgeting] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);

  useEffect(() => { /* initialize from server data */ }, []);

  return (
    <div className="container max-w-5xl py-8 space-y-6">
      {/* Card: Details */}
      <section className="space-y-4 rounded-xl border bg-card p-6">
        {/* Header row with title and save button */}
        <div className="flex items-center justify-between">
          <h2>{t('myPage.title')}</h2>
          <Button onClick={...}>{t('common.save')}</Button>
        </div>

        {/* Form fields — grouped in logical sections */}
        <div className="space-y-4">
          {/* Identity row: icon + color + name input */}
          <div className="flex items-end gap-2">...</div>

          {/* Region row: 3-column grid of Select inputs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">...</div>

          {/* Features section — its own card inside the same parent */}
          <section className="space-y-2 rounded-xl border bg-card p-6">
            <h3 className="text-base font-semibold text-muted-foreground">{t('workspace.featuresSectionTitle')}</h3>
            <SwitchSection label={t('myToggle')} hint={...} />
          </section>
        </div>
      </section>

      {/* Card: Members */}
      <section className="space-y-4 rounded-xl border bg-card p-6">...</section>
    </div>
  );
}
```

## SwitchSection Component Pattern

A reusable pattern for toggles with a label and optional hint. Used in the workspace settings "Features" section:

```tsx
function SwitchSection({
  label,
  hint,
  checked,
  onCheckedChange,
}: {
  label: string;
  hint?: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between group cursor-pointer select-none">
      {/* Label side — no hover effects */}
      <div className="flex-1 min-w-0 mr-4">
        <p className="text-sm font-medium text-foreground transition-colors">{label}</p>
        {hint && (
          <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{hint}</p>
        )}
      </div>
      {/* Switch toggle — shadcn/ui component */}
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </label>
  );
}
```

Key details:
- **No `group-hover:text-muted-foreground`** — the label text stays static; hover is purely visual (cursor pointer)
- **No nested `<div>` around the Switch** — it's a direct child to avoid extra DOM depth
- **`select-none` on label** prevents unwanted selection behavior

## Section Card Pattern

Every top-level section (Details, Features, Members, Danger Zone) wraps its content in:

```tsx
<section className="space-y-4 rounded-xl border bg-card p-6">
  <div className="flex items-center justify-between">...</div>
  ...
</section>
```

This gives consistent visual separation and padding across the page.

## i18n Key Naming Convention

| Category | Namespace | Example Keys |
|----------|-----------|--------------|
| Workspace settings UI | `workspace.*` | `featuresSectionTitle`, `enableEnvelopeBudgeting`, `enableEnvelopeBudgetingHint` |
| Common UI messages | `common.*` | `loading`, `save`, `cancel` |
| App-level (global) | `app.*` | `name`, `versionAriaLabel` |

**Rule:** Never nest keys under a sub-object like `workspace.features`. Keep them flat at the top level of the namespace. This avoids `{t('workspace.features')}` returning an object instead of a string.

## Common Mistakes to Avoid

- ❌ Using `<input type="checkbox">` for toggle switches — use `<Switch>` (shadcn component)
- ❌ Adding `group-hover:text-muted-foreground transition-colors` to labels that should stay static
- ❌ Nesting i18n keys under a sub-object (`workspace.features.enableEnvelopeBudgeting`) → use flat keys instead
- ❌ Putting the toggle inside the same grid container as other form fields — it breaks the visual flow; give it its own card section

## Where to Place New Sections

In `WorkspaceSettingsPage`:

1. **Details** (icon, color, name, currency, locale, jurisdiction)
2. **Features** ← new sections go here (envelope budgeting toggle is a good candidate)
3. **Members** (add/remove/role change)
4. **Danger Zone** (archive workspace)

Add new feature toggles as their own `<section>` between Details and Members, following the `SwitchSection` pattern above.
