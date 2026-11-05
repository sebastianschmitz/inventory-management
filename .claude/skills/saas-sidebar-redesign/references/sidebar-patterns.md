# Sidebar shell patterns

Implementation guidance for step 4. The snippets show structure and the non-obvious parts; adapt names to the app (and to its Options/Composition API style, `<script setup>` vs `setup()`).

## Contents
- Layout skeleton
- Nav data and grouping
- Collapse state
- Mobile drawer
- Styling essentials
- Accessibility
- Pitfalls

## Layout skeleton

Extract the sidebar into its own component (for example `components/AppSidebar.vue`) so the shell file stays small. The shell becomes:

```vue
<div class="app-shell" :class="{ 'is-collapsed': collapsed }">
  <AppSidebar
    :collapsed="collapsed"
    :mobile-open="mobileOpen"
    @toggle-collapse="toggleCollapse"
    @close-mobile="mobileOpen = false"
    <!-- forward the app's existing events, e.g. profile modals -->
  />
  <div class="app-main">
    <header class="mobile-topbar">
      <button class="icon-btn" aria-label="Open navigation" :aria-expanded="mobileOpen" @click="mobileOpen = true">
        <!-- menu SVG -->
      </button>
      <span class="mobile-title">{{ t('nav.companyName') }}</span>
    </header>
    <FilterBar />            <!-- existing global toolbar, now inside the main column -->
    <main class="main-content"><router-view /></main>
  </div>
</div>
```

Sidebar internals, top to bottom: brand block, scrollable nav area, footer (language switcher, profile menu, collapse toggle). Header widgets that used to sit in the top bar (language switcher, profile menu) move to the footer; they usually open dropdowns, so make sure those open upward or sideways and are not clipped by `overflow: hidden` on the sidebar. If a widget's dropdown is positioned downward with absolute positioning, flip it with a prop or CSS override in the sidebar context.

## Nav data and grouping

Drive the links from an array so grouping, icons and labels live in one place, and use `router-link` so active state comes from the router.

```js
const navGroups = [
  { labelKey: 'nav.groupMain', items: [
    { to: '/', labelKey: 'nav.overview', icon: 'home' },
    // ...
  ]},
]
```

```vue
<router-link :to="item.to" class="nav-item" :title="collapsed ? t(item.labelKey) : null">
  <svg class="nav-icon" ...><!-- icon path, stroke="currentColor" --></svg>
  <span class="nav-label">{{ t(item.labelKey) }}</span>
</router-link>
```

- `router-link` adds `router-link-active` and `router-link-exact-active` automatically. Use exact-active for the root `/` route so it is not highlighted on every page (or set `exact` styling via `active-class`/`exact-active-class`). Add `aria-current="page"` via the exact-active class styling and, if needed, `custom` slot.
- Group labels need i18n keys in every locale file. Hide group labels when collapsed, or replace them with a thin divider.
- Define icons as a small map of inline SVG paths (24x24 viewBox, `fill="none"`, `stroke="currentColor"`, `stroke-width="1.75"`, round caps) so color follows text color. Pick icons that match meaning (box for inventory, clipboard for orders, trend line for forecast). No emoji, no icon-library dependency.

## Collapse state

```js
const COLLAPSE_KEY = 'sidebar-collapsed'
const collapsed = ref(localStorage.getItem(COLLAPSE_KEY) === 'true')
const toggleCollapse = () => {
  collapsed.value = !collapsed.value
  localStorage.setItem(COLLAPSE_KEY, String(collapsed.value))
}
```

Read `localStorage` defensively (it can throw in private modes). Animate `width` with the `--transition` token and hide labels with `opacity`/`display` so text does not wrap mid-animation (`white-space: nowrap; overflow: hidden`). Collapse only applies on desktop; on mobile the drawer is always full width.

## Mobile drawer

Breakpoint around 768px (pick one and use it for every layout rule).

- Desktop: sidebar is `position: fixed; inset: 0 auto 0 0;` with the main column offset by its width.
- Mobile: sidebar is `transform: translateX(-100%)` and slides to `0` when `mobileOpen`; main column margin is 0; a `.mobile-topbar` (height `--topbar-height`) shows the menu button.
- Render a backdrop (`position: fixed; inset: 0; background: rgba(15,23,42,.5)`) only when open; clicking it closes the drawer.
- Close on route change (`watch(() => route.path, ...)` or `router.afterEach`), and on Escape (`keydown` listener added in `onMounted`, removed in `onBeforeUnmount`).
- Lock body scroll while open (`document.body.style.overflow = 'hidden'`, restore on close and on unmount).
- Move focus into the drawer when it opens and back to the menu button when it closes.

## Styling essentials

- Sidebar: width `var(--sidebar-width)` (collapsed `var(--sidebar-width-collapsed)`), background `var(--sidebar-bg)`, `display: flex; flex-direction: column`, `z-index` below modals.
- Nav item: flex, `gap: var(--space-3)`, `padding: var(--space-2) var(--space-3)`, radius `--radius-md`, color `--sidebar-text`; hover `--sidebar-item-hover`; active `--sidebar-item-active` background with `--sidebar-text-active` text (a 3px accent bar on the left edge is a nice cue).
- Collapsed: center the icon, hide `.nav-label`, keep a 2.5rem square hit target.
- Nav area: `flex: 1; overflow-y: auto;` so many items scroll rather than overflow; footer stays pinned.
- Long labels (translations): `.nav-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }` and a `title` attribute with the full text.
- Focus: `:focus-visible` outline with the accent color; on a dark sidebar use a light ring if the accent has low contrast.
- Main column: `min-width: 0`; `transition: margin-left var(--transition)` to match the sidebar animation.

## Accessibility

- `<aside>` containing `<nav aria-label="Main navigation">` (label through i18n).
- Toggle buttons are `<button type="button">` with `aria-label` and `aria-expanded`; give them tooltips in collapsed state.
- Respect `prefers-reduced-motion`: disable the width and slide transitions.
- Contrast: check muted sidebar text against the sidebar background.

## Pitfalls

- A fixed sidebar plus unscoped `body`/`.app` styles from the old layout (for example `max-width`, centered containers, `padding-top` for the old header) will misplace content. Remove those old rules.
- Old sticky headers: anything with `position: sticky; top: <old header height>` (filter bars, table headers) needs its offset updated to 0 or the new top bar height.
- Full-width assumptions: views with `width: 100vw` or fixed pixel widths overflow once the sidebar takes 15rem. Use `100%` and `min-width: 0`.
- `100vh` heights on mobile browsers: prefer `100dvh` for the drawer.
- Dropdowns inside the sidebar footer get clipped if an ancestor has `overflow: hidden`; apply overflow to the nav area only, not the whole sidebar.
- Route-based `v-if` on the old nav (for example hiding it on certain pages) must be carried over to the sidebar.
- Pages with pre-existing unrouted views or broken endpoints are not part of this task; mention them, do not fix them silently.
