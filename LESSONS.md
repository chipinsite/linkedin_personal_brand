# Lessons

## Known UX/design weaknesses visible now
- The interface concentrates many workflows in one screen, which increases cognitive load.
- Feedback is global rather than panel-local, so action provenance can be unclear after rapid operations.
- Visual hierarchy between critical actions and routine actions is limited.
- Long-form operational data is shown as raw JSON blocks, which increases scanning effort.

## Patterns to avoid repeating
- Adding new actions directly into the top-level screen without clear grouping boundaries.
- Introducing one-off styles that bypass shared tokens.
- Shipping new states without explicit empty/error/loading behavior.
- Expanding forms without preserving label clarity and mobile collapse behavior.

## Early assumptions that need validation
- Assumption: one primary operator persona is sufficient for current UX decisions.
- Assumption: desktop-first density is acceptable for most real usage sessions.
- Assumption: global refresh-after-action behavior is operationally acceptable for scale.

## Areas that currently feel unclear or heavy
- Relationship between manual publish assistant output and publishing panel actions can feel split.
- Controls panel contains high-risk actions near routine controls.
- System status data (health/readiness/deep) is visible but not deeply contextualized for recovery steps.
- Escalation triage is visible, but next action pathways are not explicit inside the same panel.

## How to use this file
- Update after each meaningful frontend iteration.
- Add only observed evidence, not preference-based commentary.
- Keep entries short, specific, and tied to real interaction outcomes.
