# Design System

## Design philosophy
This product is an operations console first: information must be legible, prioritized, and actionable under time pressure. Visual language should reduce uncertainty, not add personality noise. Every token exists to support scanning, decision-making, and operational safety.

## Token strategy
- Use semantic tokens, not one-off values.
- Token count is intentionally small to prevent drift.
- Current token values are derived from the existing UI in `/Users/sphiwemawhayi/Personal Brand/Frontend/src/styles/app.css`.

## Color system
### Core surface and text
- `--color-bg-canvas`: `#f2efe8` (primary app background)
- `--color-bg-accent`: `#e4dac6` (subtle radial accent)
- `--color-bg-surface`: `#fffdf8` (panel/card surface)
- `--color-bg-surface-strong`: `#ffffff` (inputs, list rows)
- `--color-text-primary`: `#1f1f1f`
- `--color-text-secondary`: `#555046`
- `--color-border-default`: `#d8cfbe`

### Brand and action
- `--color-action-primary`: `#d95f2a`
- `--color-action-primary-strong`: `#a53f16`
- Rationale: one clear action hue keeps the interface behaviorally consistent.

### Semantic feedback
- `--color-semantic-success`: `#1f7a3f`
- `--color-semantic-error`: `#a11f2f`
- `--color-semantic-success-bg`: success mixed with white (existing `color-mix` behavior)
- `--color-semantic-error-bg`: error mixed with white (existing `color-mix` behavior)

### Color rules
- No additional brand hues without a documented state or meaning.
- Never communicate status by color alone; pair with text labels.

## Typography system
### Font roles
- Sans UI font: `Manrope, sans-serif` for all UI controls and body copy.
- Monospace support font: `IBM Plex Mono, monospace` for metadata labels and JSON/code blocks.

### Type hierarchy
- Display: page title (`h1`, clamp-based scaling)
- Section heading: panel titles (`h2`)
- Body: operational instructions and labels
- Caption/meta: secondary data, timestamps, pills
- Mono meta: eyebrow and structured output blocks

### Usage rules
- One display size per screen.
- Limit emphasis to weight changes; avoid decorative typography.
- Monospace only for machine-like content (IDs, config JSON, logs, metrics dumps).

## Spacing scale
Use an 8px base rhythm with one compact step for tight controls.

- `--space-1`: 4px (micro gaps)
- `--space-2`: 8px (control spacing)
- `--space-3`: 12px (intra-component spacing)
- `--space-4`: 16px (default block spacing)
- `--space-5`: 24px (section spacing)
- `--space-6`: 32px (major separation)

Rules:
- Compose layouts from this scale only.
- Keep vertical rhythm consistent within each panel.

## Layout grid rules
- Global content container max width: 1280px.
- Primary grid: 12 columns.
- Default panel span: 12 columns.
- Priority panels (top four in current app): 6 columns on desktop, 12 on <=980px.
- Gap token: 12px (`--space-3`).

## Border radius rules
- `--radius-control`: 8px (inputs/buttons)
- `--radius-item`: 10px (list rows)
- `--radius-panel`: 14px (cards/panels)
- `--radius-hero`: 16px (hero container)
- `--radius-pill`: 999px (status pills)

Rule: radius scales with containment level; deeper containers have larger radius.

## Elevation and shadow rules
- `--shadow-hero`: `0 18px 40px rgba(22, 16, 8, 0.12)`
- `--shadow-panel`: `0 6px 18px rgba(40, 24, 2, 0.06)`

Rules:
- Use elevation only to separate layers (hero > panels > rows).
- No decorative multi-shadow stacks.

## Interaction states
- Default: clear border and fill contrast.
- Hover (buttons): slight upward shift (`translateY(-1px)`), no color jump.
- Focus: visible ring required (current CSS needs explicit `:focus-visible`; see Accessibility baseline).
- Disabled: opacity reduction and blocked pointer action.
- Loading: disable actionable controls and show global status message.

## Accessibility baseline
- Target WCAG 2.1 AA contrast for text and controls.
- All interactive elements must have a visible focus indicator.
- Form fields require programmatic labels (current app already uses `<label>` wrappers).
- Error/success messages must be readable as text, not color-only.

Known gap (current UI):
- Explicit keyboard focus styling is not defined in `/Users/sphiwemawhayi/Personal Brand/Frontend/src/styles/app.css`; this must be treated as a required baseline constraint for future UI changes.
