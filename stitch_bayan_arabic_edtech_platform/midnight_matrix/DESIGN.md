---
name: Midnight Matrix
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#ca8100'
  on-tertiary-container: '#3e2400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-hero:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 60px
    letterSpacing: -0.02em
  display-hero-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 42px
    letterSpacing: -0.01em
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.01em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 36px
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 38px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.04em
  code-inline:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 20px
  code-block:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 24px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system projects a state-of-the-art, high-performance developer learning environment engineered for modern software engineers, computer science students, and tech professionals across the Arab world. The aesthetic harmonizes high-contrast dark enterprise software with cutting-edge developer ergonomics, combining deep oceanic navy depths with electric luminescent accents.

The design movement is a convergence of **Deep Surface Minimalism** and **Technical Glassmorphism**:
- Ultra-refined dark layered surfaces eliminate visual fatigue during sustained coding sessions.
- Translucent frosted containers, structural micro-borders, and targeted ambient photon glows direct visual focus to active tasks, metrics, and code sandboxes.
- Strict right-to-left (RTL) ergonomics treat Arabic typography with native architectural respect, seamlessly integrating Latin characters for code blocks, alphanumeric tokens, and terminal windows.
- The interface delivers an atmosphere of technical mastery, precision, and momentum.

## Colors

The palette leverages a structured luminance hierarchy optimized for low eye strain and high readability across diverse display hardware:

- **Canvas & Base Layers**: Deep space navy (`#0a0f1d`) anchors the primary viewport canvas, stepping upward into `#0f172a` for primary sections, sidebars, and navigation rails, and `#131d35` for inner structural grouping.
- **Elevated Surfaces**: Container tiers (`#18223c`, `#1e293b`, `#24304f`) establish clear z-index relationships without heavy shadows. Translucent glass surfaces use `rgba(24, 34, 60, 0.75)` with an `18px` backdrop blur.
- **Brand & Action (Electric Blue)**: The core active energy centers on `#3b82f6`, supported by deep action blue (`#2563eb`) for high-contrast interactive states and cyber cyan (`#00d2ff`) for focus rings, hover glows, and code syntax highlights.
- **Functional Semantics**:
  - **Success & Progress**: Emerald (`#10b981`) indicates mastery, passing test suites, and completed curriculum tracks.
  - **Achievement & Status**: Amber gold (`#f59e0b`) drives streak counts, accreditation seals, and peer ratings.
  - **Critical Signals**: Vivid coral (`#ef4444`) commands attention for compiler errors, assignment cutoffs, and destructive state actions.
- **Structural Lines & Contrast**: Borders utilize `#1e293b` for default separation and `#2e3d66` for active/hover states, preserving visual clarity against deep navy surfaces.

## Typography

The typographic engine implements a deliberate dual-script hierarchy. In Arabic execution contexts, the body and headline fallbacks target modern, highly legible geometric Arabic typography (Cairo and Tajawal) integrated through the primary system stack, paired seamlessly with Inter for Latin text, and standard monospace stacks for terminal and code rendering.

Key implementation rules:
- **Bi-directional Flow**: The overall document operates under `dir="rtl"`. Code snippets, file paths, and terminal outputs enforce an explicit `dir="ltr"` inline wrapper with isolated text orientation (`unicode-bidi: isolate`).
- **Line Heights for Arabic Script**: Arabic letterforms feature taller ascenders and deeper descenders than Latin characters. Line heights across all body and display sizes are extended by 15-20% relative to Latin-only scales to prevent diacritic clipping and maintain visual airiness.
- **Numbers and Monospace**: Monospaced tabular numerals are enforced across dashboard metrics, timers, unit tests, and terminal outputs to ensure perfect vertical alignment across RTL columns.

## Layout & Spacing

The layout is built upon an adaptive 12-column fluid grid system pinned to a maximum content boundary of 1440px, transitioning to an 8-column layout on tablet devices and a 4-column stack on mobile viewports.

- **RTL Coordinate Geometry**: Grid columns flow right-to-left. Sidebar navigation anchors firmly to the physical right edge, driving reading momentum inward toward the central content canvas, while ancillary contextual panels (lesson index, terminal, sandbox controls) reside on the physical left.
- **Rhythm & Padding**: Vertical and horizontal whitespace strictly follows an 8pt base grid. Micro-spacing within interactive controls uses 4px intervals (`space-xs` and `space-sm`), while component structural card spacing relies on `space-md` (16px) and `space-lg` (24px).
- **Responsive Transitions**:
  - **Desktop (>= 1280px)**: 12 columns, 24px gutters, fixed or persistent collapsible right-hand drawer (280px width).
  - **Tablet (768px - 1279px)**: 8 columns, 20px gutters, navigation collapses to a responsive slide-out canvas triggered from the top right.
  - **Mobile (< 768px)**: 4 columns, 16px gutters, 16px outer margin, sticky bottom-navigation or floating header bar with contextual drawer.

## Elevation & Depth

Visual hierarchy does not rely on opaque skeuomorphic casting. Instead, depth is produced through an interplay of surface luminance, translucent glass, and soft ambient chromatic glows:

- **Level 0 (Canvas Base)**: `#0a0f1d` with zero blur or elevation. Raw background for the primary workspace.
- **Level 1 (Sub-panels & Structural Rails)**: `#0f172a` bordered with 1px solid `#1e293b`. Serves sidebars, footer sections, and static course indexes.
- **Level 2 (Cards & Content Modules)**: `#18223c` with 1px solid `#2e3d66`. Backed by an ultra-diffuse ambient shadow: `0 8px 32px -4px rgba(2, 6, 23, 0.6)`.
- **Level 3 (Interactive Modals, Dropdowns & Popovers)**: Translucent surface `rgba(30, 41, 59, 0.85)` with `backdrop-filter: blur(16px)`, secured with a 1px perimeter border of `rgba(59, 130, 246, 0.25)` and an ambient shadow: `0 20px 48px -8px rgba(0, 0, 0, 0.85)`.
- **Level 4 (Active Focus & Glow States)**: Emits a targeted directional or perimeter luminescent halo. Active primary cards or running code sandboxes project `box-shadow: 0 0 24px -4px rgba(59, 130, 246, 0.2)`. Completed milestone items glow with `rgba(16, 185, 129, 0.2)`.

## Shapes

The geometric grammar emphasizes controlled modernity with rounded corners that feel architectural rather than toy-like:

- **Small Components (Chips, Inputs, Buttons)**: Utilize a base radius of `0.5rem` (8px), establishing crisp alignment and tactile click targets.
- **Medium Modules (Cards, Sandbox Panels, Video Players)**: Utilize `rounded-lg` at `1rem` (16px) for balanced containment.
- **Large Shells (Main Modals, Feature Banners, Onboarding Viewports)**: Implement `rounded-xl` at `1.5rem` (24px).
- **Status Pills & Progress Counters**: Utilize full pill geometry (`9999px`) to visually differentiate fluid metadata tags from rigid architectural cards.

## Components

### Buttons
- **Primary**: Gradient fill `linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)`, text `#ffffff`, radius 8px (`rounded`), subtle top highlight `inset 0 1px 0 rgba(255, 255, 255, 0.2)`. Hover triggers a brightness bump and a cyan halo (`box-shadow: 0 0 16px rgba(0, 210, 255, 0.35)`). Active state applies a `scale(0.98)` transform.
- **Secondary**: Elevated dark background `#1e293b`, text `#e2e8f0`, border 1px solid `#2e3d66`. Hover state shifts border to `#3b82f6` with text `#ffffff`.
- **Ghost/Tertiary**: Transparent fill, text `#94a3b8`. Hover transitions background to `rgba(30, 41, 59, 0.6)` and text to `#ffffff`.
- **Icon Placers**: In RTL mode, action icons sit to the left of Arabic text labels for forward progression arrows, and to the right for categorizing icons (e.g., terminal icons, code brackets).

### Cards & Stat Widgets
- **Course & Lesson Cards**: Surface `#18223c`, border 1px solid `#1e293b`, border-radius 16px (`rounded-lg`). Top edge includes an optional 2px accent progress bar. Hover introduces a smooth lift (`translateY(-2px)`) and border illumination via `#2e3d66`.
- **Stat Cards**: Surface `#131d35`, containing large tabular numerical figures in Inter, accompanied by an Arabic micro-label. Includes an icon badge tinted with emerald (`#10b981`), amber (`#f59e0b`), or electric blue (`#3b82f6`).

### Input Fields & Search Bars
- Background `#0f172a`, border 1px solid `#2e3d66`, text `#f8fafc`, placeholder `#64748b`, radius 8px.
- Focus state activates a distinct ring: `border-color: #3b82f6` with `box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25)`.
- Input elements maintain right-aligned text and placeholders for Arabic script; clear buttons or trailing icons anchor to the physical left.

### Badges, Chips & Progress Indicators
- **Completed / Success**: Background `rgba(16, 185, 129, 0.12)`, border 1px solid `rgba(16, 185, 129, 0.3)`, text `#10b981`, pill-shaped (`rounded-full`).
- **In Progress / Active**: Background `rgba(59, 130, 246, 0.12)`, border 1px solid `rgba(59, 130, 246, 0.3)`, text `#3b82f6`, pill-shaped.
- **Certification / Rating**: Background `rgba(245, 158, 11, 0.12)`, border 1px solid `rgba(245, 158, 11, 0.3)`, text `#f59e0b`, accompanied by an amber star glyph.
- **Progress Track**: Deep track `#0f172a` with an electric blue or emerald progress fill, featuring an animated shimmer highlight on active compilation or upload.

### Code Editor & Terminal Windows
- Surface `#0a0f1d` with 1px solid `#1e293b`, radius 12px. Window controls (close, minimize, expand dots) placed according to native platform standards.
- Explicit left-to-right (`dir="ltr"`) container with monospaced syntax highlights: keywords in `#00d2ff`, strings in `#10b981`, warnings in `#f59e0b`, and errors highlighted with `#ef4444`.

### Tables & Leaderboards
- Dark elevated background `#18223c`. Header cells rendered in `#94a3b8` with a subtle bottom border (`#2e3d66`). Alternating rows utilize a faint zebra tint `rgba(255, 255, 255, 0.01)`.
- Row hover triggers an illuminated background `rgba(59, 130, 246, 0.05)` with an electric blue right-border accent marking the active row.