# Frontend Guidelines

## Purpose
This document defines how UI is built and maintained so the interface stays coherent as the product evolves. It governs structure and behavior, not visual taste.

## Component philosophy
- Build around repeatable, named patterns (panel, list row, form grid, status banner).
- Prefer composition over special-case components.
- Keep each component responsible for one interaction context.
- Reuse existing patterns before creating new ones.

Current evidence:
- `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/Panel.jsx` establishes the base panel wrapper used across operational sections.

## UX state handling
Every user action must resolve into one of these states with explicit feedback:
- `loading`: actions disabled while request is in progress.
- `success`: concise confirmation message.
- `error`: readable error message from request failure.
- `empty`: clear zero-state text when no records exist.

Current implementation baseline:
- `loading`, `message`, and `error` are global in `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`.

Rules:
- Never leave actions without visible completion status.
- Do not hide failures behind silent retries.
- Empty state text must clarify whether data is absent or not yet loaded.

## File and component organization
Expected structure:
- `src/App.jsx`: orchestration only.
- `src/components/`: reusable UI primitives and composed sections.
- `src/services/`: API boundary and request normalization.
- `src/styles/`: global tokens and layout rules.
- `src/__tests__/`: behavior-level tests tied to user actions.

Rules:
- Move repeated section markup out of `App.jsx` once behavior starts diverging.
- Keep API calls in `services`, not inside leaf components.
- Keep styling centralized; avoid ad hoc inline styles.

## Naming conventions
- Components: `PascalCase` (`Panel`, `DraftsPanel`).
- Hooks/state: `camelCase` with intent names (`publishFilter`, `metricsInput`).
- CSS classes: semantic role names (`panel`, `list-row`, `banner`).
- API methods: verb-first and domain-specific (`generateDraft`, `confirmPublish`).

## Rules for introducing new UI components
A new component is allowed only when at least one is true:
- Existing component is reused 2+ times with conditional complexity.
- A domain section has independent state and actions.
- Accessibility or testing clarity improves materially.

Before adding:
- Confirm no existing pattern can absorb the need.
- Define component boundary, props, and state ownership.
- Add or update interaction tests.

## Styling guardrails
### Allowed
- Token-based colors, spacing, radius, and shadows.
- Semantic class names tied to purpose.
- Mobile-first media queries.
- Subtle motion that confirms interaction state.

### Forbidden
- Hardcoded one-off values when an existing token fits.
- Per-component visual themes that break dashboard consistency.
- Color-only status communication.
- Deep selector chains that couple styling to markup order.

## Responsiveness expectations (mobile first)
- Start from single-column behavior.
- Promote to multi-column only when content density requires it.
- Preserve action visibility and touch target clarity on narrow screens.
- Forms must collapse to one column without loss of label context.

Current baseline:
- Desktop-first implementation exists with breakpoint fallback at `980px` in `/Users/sphiwemawhayi/Personal Brand/Frontend/src/styles/app.css`.

Assumption (explicit):
- The app is primarily used on desktop operations screens today; mobile support is functional but not optimized for heavy multi-panel workflows.
