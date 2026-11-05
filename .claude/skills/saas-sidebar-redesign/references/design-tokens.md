# Design tokens and component recipes

Starting point for step 2 and 3 of the workflow. Adapt the values to the app's existing palette; keep the structure (scales, semantic names) so the system stays consistent.

## Contents
- Token block
- Page layout and spacing rules
- Component recipes (card, table, button, badge, stat tile, form controls)
- Consistency checklist

## Token block

Put this on `:root` in the global stylesheet (or the unscoped style block of the shell).

```css
:root {
  /* Spacing: 4px base. Use these everywhere; avoid one-off values. */
  --space-1: 0.25rem;  /* 4  */
  --space-2: 0.5rem;   /* 8  */
  --space-3: 0.75rem;  /* 12 */
  --space-4: 1rem;     /* 16 */
  --space-5: 1.5rem;   /* 24 */
  --space-6: 2rem;     /* 32 */
  --space-7: 3rem;     /* 48 */

  /* Neutrals (slate shown; swap for the app's own gray ramp) */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-text-subtle: #94a3b8;

  /* Accent: one brand color with hover and soft tint */
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-soft: #eff6ff;

  /* Status */
  --color-success: #059669;  --color-success-soft: #ecfdf5;
  --color-warning: #d97706;  --color-warning-soft: #fffbeb;
  --color-danger:  #dc2626;  --color-danger-soft:  #fef2f2;
  --color-info:    #2563eb;  --color-info-soft:    #eff6ff;

  /* Sidebar (dark sidebar on light content is the classic SaaS look) */
  --sidebar-width: 15rem;
  --sidebar-width-collapsed: 4.25rem;
  --sidebar-bg: #0f172a;
  --sidebar-text: #cbd5e1;
  --sidebar-text-active: #ffffff;
  --sidebar-item-hover: rgba(255, 255, 255, 0.06);
  --sidebar-item-active: rgba(37, 99, 235, 0.22);
  --topbar-height: 3.5rem; /* mobile top bar only */

  /* Shape and depth */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.16);

  /* Type */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.5rem;

  --transition: 150ms ease;
}
```

A light sidebar (white surface, subtle border, accent-soft active item) is equally valid and sometimes fits an app's existing look better. Pick one and apply it consistently; if the app has a dark mode, derive the sidebar tokens from the theme instead of hardcoding.

## Page layout and spacing rules

- Main column: `margin-left: var(--sidebar-width)` (or `display: flex` with the sidebar as a fixed-width child), `min-width: 0` so wide tables and charts cannot push the page sideways.
- Content container: `padding: var(--space-5) var(--space-6)`, `max-width` around 90rem, centered. On mobile reduce to `var(--space-4)`.
- Vertical rhythm: `--space-5` between sections and cards, `--space-4` inside cards, `--space-2`/`--space-3` between related inline items. Stick to these three; most inconsistency comes from inventing a fourth.
- Page header: title `--text-xl` weight 600, subtitle `--text-sm` muted, `--space-5` below.

## Component recipes

Keep existing class names; change only declarations.

**Card**
```css
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--space-5);
  margin-bottom: var(--space-5);
}
```
Card header: flex, space-between, `margin-bottom: var(--space-4)`, title `--text-lg` weight 600.

**Table**
- Wrap in a container with `overflow-x: auto`.
- `th`: `--text-xs`, uppercase, letter-spacing 0.05em, muted, background `--color-bg`, bottom border; `td`: `--text-sm`, `padding: var(--space-3) var(--space-4)`, bottom border `--color-border`.
- Row hover: `background: var(--color-bg)`. Numeric columns right-aligned with tabular numerals (`font-variant-numeric: tabular-nums`).

**Buttons** (define `.btn`, `.btn-primary`, `.btn-secondary` if the app has none)
- Height about 2.25rem, `padding: 0 var(--space-4)`, radius `--radius-md`, `--text-sm` weight 500.
- Primary: accent background, white text, hover `--color-accent-hover`. Secondary: surface background, border, hover `--color-bg`. Disabled: 0.5 opacity, `cursor: not-allowed`.
- Visible focus: `outline: 2px solid var(--color-accent); outline-offset: 2px`.

**Badge**
- Pill: `padding: 2px var(--space-2)`, `--text-xs` weight 500, radius 999px. Map semantic variants to `--color-*-soft` background with the matching `--color-*` text. Map app-specific variants (e.g. trend or priority names) onto those same four semantics instead of inventing colors.

**Stat tile**
- Same surface as card, label `--text-xs` muted uppercase, value `--text-xl` weight 600, optional colored left or top accent for status. Grid: `repeat(auto-fit, minmax(14rem, 1fr))` with `gap: var(--space-4)`.

**Form controls (selects, inputs, range)**
- Height 2.25rem, border `--color-border-strong`, radius `--radius-md`, `--text-sm`, focus ring same as buttons. Labels `--text-xs` weight 500 muted above the control.
- Filter/toolbar strip: surface background, bottom border, `padding: var(--space-3) var(--space-6)`, flex-wrap with `gap: var(--space-4)`.

**Modals**
- Overlay `rgba(15, 23, 42, 0.5)`, panel `--radius-lg` with `--shadow-lg`. Give modals a z-index above the sidebar and mobile drawer (sidebar about 40, drawer backdrop about 50, modals 100+), otherwise they open underneath.

**Loading / error states**
- Centered, muted text with `--space-6` padding; error uses `--color-danger` on `--color-danger-soft` with a border.

## Consistency checklist

Run through before finishing:
- No raw hex colors or pixel spacings left in the shell and shared components (grep for `#` and `px` in the files you touched).
- Same card radius, shadow and padding on every page.
- One primary button style; one badge style per status.
- Tables and charts never overflow the main column; only their own container scrolls.
- Text contrast is at least 4.5:1 for body text, including muted text on the sidebar background.
