# Product Requirements Document (Current State)

## Product purpose
This product is an operational console for running a LinkedIn personal-brand workflow with AI-assisted drafting and human-controlled publishing. It centralizes draft generation, approval decisions, publish confirmation, engagement monitoring, source ingestion, learning feedback, reporting, and operational controls in one interface so the operator can keep the system reliable and aligned.

## Target user definition
- Primary user: an individual operator responsible for day-to-day brand publishing and engagement execution.
- User context: high-frequency decisions, low tolerance for ambiguity, preference for clear operational feedback.
- Not currently multi-role in the frontend (no visible role-based UX partitioning).

## Core features (as implemented today)
- Health and readiness status visibility.
- Draft lifecycle: generate, manual create, approve, reject with reason.
- Manual publish assistant with checklist (hashtags, links, word count, topical hint) and clipboard copy.
- Publish queue management: due processing, filter, manual publish confirmation, metrics updates.
- Engagement operations: poll status, add comment records, monitor escalations.
- Source ingestion from feed URLs.
- Learning weights visibility and recompute action.
- Daily report visibility and send action.
- Control toggles: kill switch and posting state.
- Alignment and audit data visibility.

## Non-goals
- Not a public-facing content consumption product.
- Not a full social media scheduler across multiple platforms.
- Not a visual post editor or rich media design tool.
- Not an analytics exploration suite with custom dashboards.
- Not an autonomous no-human-in-the-loop publisher from the frontend alone.

## Constraints and limitations
- Single-page frontend architecture; no route-based separation.
- Global loading/message/error model affects all panels at once.
- Heavy dependence on backend endpoint availability and response quality.
- Manual publishing remains a required step before confirmation.
- Frontend currently optimized for desktop density; mobile is supported but secondary.

Unknowns (explicit):
- No explicit front-end role/permission model is visible.
- No documented SLA or performance budget is present in frontend docs.

## Success criteria (user perspective)
- User can execute the full publish loop without switching tools excessively.
- User can see what is pending, failed, or completed at any moment.
- User can make approve/reject/publish decisions quickly and confidently.
- User can identify and react to escalations without ambiguity.
- User can recover from API failures with clear feedback and retry path.
