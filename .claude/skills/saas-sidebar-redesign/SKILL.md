---
name: saas-sidebar-redesign
description: Redesign a Vue 3 app's UI into a modern SaaS-style interface - a vertical left sidebar instead of a top nav bar, a shared design-token system (consistent spacing, color, radius, shadow, type) and restyled global cards, tables, buttons and badges. Use this skill whenever the user wants to modernize, restyle, polish or "make it look professional" for a Vue 3 / Vite app, asks for a sidebar or side navigation, wants to replace a top navbar or tabs, or mentions SaaS dashboard look, admin-panel layout, or consistent spacing across pages - even if they do not say "redesign".
---

# SaaS sidebar redesign for Vue 3

Turn a Vue 3 app with a top navigation bar into a modern SaaS-style interface: a left sidebar, one consistent design system, and a calm, professional look. The goal is a coherent result across every page with the smallest possible change to individual views, so the redesign is cheap to review and hard to regress.

## Why the work is ordered this way

Pages look inconsistent when each view hardcodes its own spacing and colors. If you restyle views one at a time you create a second inconsistency. So: define tokens first, restyle the shared global classes second, build the shell third, and only then touch individual views for things that still look wrong. Most pages should need zero edits because they already use the shared classes.

## Workflow

### 1. Discover (read before you change anything)
- Find the app shell (usually `App.vue`): the top nav markup, router links, header widgets (language switcher, profile menu, search), any filter bar, and the `<router-view>` container.
- List the global classes pages rely on (cards, tables, badges, stat tiles, page headers, loading/error states) and where they live. In many apps they are unscoped styles in `App.vue`; in others a `styles/` folder. Restyle them where they live.
- Note hardcoded colors/spacing, and any existing design rules in `CLAUDE.md` or similar (palette, "no emojis", icon conventions, i18n requirements). Those rules win over the defaults in this skill.
- Check whether routes are declared in `main.js`/`router/` and whether nav labels go through an i18n helper. Keep using it.

Report a short summary of what you found before editing, so mistakes in your understanding surface early.

### 2. Define design tokens
Add CSS custom properties on `:root` using `references/design-tokens.md` as the starting point: a 4px-based spacing scale, neutral + one accent color ramp, semantic status colors, radii, shadows, type scale, sidebar and header dimensions. Adapt the accent and neutrals to the app's existing palette rather than imposing new brand colors; the app should still feel like itself, just consistent.

Why tokens: a single spacing/color vocabulary is what makes the result look designed instead of patched, and it makes later tweaks one-line changes.

### 3. Restyle the shared components
Rewrite the global card, table, button, badge, stat tile, page header and form-control styles to use the tokens. Keep class names and the DOM they style unchanged so existing views keep working. Recipes are in `references/design-tokens.md`.

### 4. Build the sidebar shell
Replace the top bar with a fixed left sidebar and a main column, following `references/sidebar-patterns.md`. Required behavior:
- Brand/title at the top, nav items grouped under small section labels, language and profile widgets in the footer.
- Active item clearly highlighted via the router's active state, not string comparison of paths.
- Collapsible to an icon-only rail, with the state persisted in `localStorage`; tooltips (`title`) on icons while collapsed.
- Responsive: below the tablet breakpoint the sidebar becomes an off-canvas drawer opened from a menu button in a slim top bar, with a backdrop, Escape to close, and close-on-navigate.
- Icons are inline SVG using `currentColor`. Do not add an icon library dependency and do not use emoji or emoji-like glyphs.
- Keyboard and screen-reader support: real `<nav aria-label>`, `aria-current="page"`, visible focus rings, `aria-expanded` on the toggle.
- The existing filter bar (or other global toolbar) moves into the main column, above page content, and keeps working.

Keep nav labels on the existing i18n keys; if a label is hardcoded (a common leftover), move it to the locale files in every supported language instead of adding another hardcoded string. Remember that translated labels can be much longer than English; the sidebar width and text truncation must cope.

### 5. Touch views only where needed
After the shell and shared styles are in, look at every route in a browser. Fix only what is visibly broken or inconsistent (for example hardcoded widths that assumed a full-width header, one-off paddings, charts sized to the old container). Prefer replacing a hardcoded value with a token over adding new CSS.

### 6. Verify
- Run the production build (`npm run build`) to catch template and import errors. Send build output to a scratch directory, not the repo.
- Open each route in a real browser (Playwright MCP if available) at a desktop width and a mobile width. Check: active highlight, collapse and expand, drawer open/close, no horizontal page scroll, tables still scroll inside their container, modals still layer above the sidebar, no console errors you introduced.
- Switch locale if the app has one and confirm long labels do not break the layout.
- Take before/after screenshots when the user may want to review them.

## Working rules
- Follow the project's own conventions for who edits `.vue` files. If the project mandates a specialist agent for Vue changes, delegate to it and give it the sections of this skill that apply.
- Do not commit unless asked, and never add dependencies for icons, CSS frameworks or UI kits unless the user asks. The point is a design system the project owns.
- Preserve behavior: routes, data loading, filters and modals must work exactly as before. This is a visual change.
- Leave pre-existing unrelated bugs alone, but mention them in the summary.

## Final summary to the user
List the files changed, the token decisions (accent color, spacing base), what was verified and at which widths, anything not verified, and any unrelated issues you noticed.
