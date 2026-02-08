# Tech Stack Constraints

## Frontend framework
- React 18 (`react`, `react-dom`) with functional components and hooks.
- Build and dev server via Vite 5.

Evidence:
- `/Users/sphiwemawhayi/Personal Brand/Frontend/package.json`
- `/Users/sphiwemawhayi/Personal Brand/Frontend/src/main.jsx`

## Styling approach
- Global CSS file (`/Users/sphiwemawhayi/Personal Brand/Frontend/src/styles/app.css`).
- CSS custom properties define core visual tokens.
- No CSS-in-JS, utility framework, or design token compiler currently present.

## Component system
- Lightweight internal component pattern.
- `Panel` is the only explicit reusable shell component in current code.
- Most screen structure is composed directly in `App.jsx`.

## Animation and motion constraints
- Current motion is minimal (button hover translate).
- No animation library is installed.
- Motion should remain subtle and state-driven to avoid adding interaction latency.

## Responsiveness constraints
- Layout uses a 12-column CSS grid at desktop widths.
- Collapse behavior at `max-width: 980px` moves priority panels to full width and forms to one column.
- No dedicated mobile navigation model exists because the app is single-page and panel-based.

## Accessibility support level
Current support in code:
- Semantic headings and sections.
- Labels wrapping form controls.
- Clear text banners for success/error states.

Current gaps:
- No explicit `:focus-visible` styling in CSS.
- No dedicated accessibility test suite in frontend tests.

## What this stack does well
- Fast iteration and local development.
- Predictable component rendering model.
- Straightforward API integration and testing via mocked `fetch`.
- Simple deployment artifact through Vite build.

## What this stack should not be forced to do
- Do not treat a single giant `App.jsx` as infinitely scalable architecture.
- Do not rely on unstructured global CSS growth for long-term design consistency.
- Do not introduce complex visual systems without a tokenized component foundation.
- Do not assume backend latency can be hidden purely with frontend animation.

Assumption (explicit):
- Frontend remains intentionally light and operational; design decisions should prioritize clarity and maintainability over visual complexity.
