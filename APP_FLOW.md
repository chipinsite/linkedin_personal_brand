# App Flow

## Primary user
A single operator managing personal brand publishing operations end to end: draft intake, publish confirmation, engagement tracking, quality control, and system safety checks.

## Job to be done
Keep a reliable publishing and engagement loop running with minimal ambiguity, while making safe decisions quickly when quality or platform risk appears.

## Entry points
- App load into the `Execution Console`.
- Optional one-click seeded run via `Playground > Bootstrap demo`.

## Primary flows (happy path)
### Flow 1: Draft to publish confirmation
1. User checks system health and readiness in the hero header.
2. User generates or creates a draft in `Drafts`.
3. User reviews and approves draft.
4. User opens `Manual Publish Assistant` and checks guardrails.
5. User copies draft body and publishes manually on LinkedIn.
6. User confirms publish in `Publishing` with LinkedIn URL.

### Flow 2: Post-performance loop
1. User selects published post in `Publishing`.
2. User submits metrics update.
3. User reviews `Learning` weights and `Reports` summary.

### Flow 3: Engagement loop
1. User runs `Engagement > Poll`.
2. User inspects escalated items in `Escalations`.
3. User logs/validates comments.

## Secondary flows
- Bulk demonstration flow via `Bootstrap demo` (creates, approves, confirms publish, updates metrics, creates comment, ingests sources, sends report).
- Content input refresh via `Sources > Ingest`.
- Operations control toggles in `Controls` (kill switch and posting state).
- Alignment and audit inspection in `Algorithm Alignment` and `Audit Trail`.

## Failure paths
- API/network failure on any action: global error banner shown.
- Clipboard unavailable when copying draft body: explicit error shown.
- No draft content available for publishing assistant: checklist shows blocking message.
- Empty datasets (drafts, posts, comments): panels render counts/empty lists without crash.
- Invalid or unavailable post IDs for metrics/comments: action is blocked by disabled button or backend error.

## Decision points
- Approve vs reject each pending draft.
- Whether checklist violations are acceptable before manual publish.
- Which posts to focus using queue filter (`all`, `due now`, `unpublished`, `published`).
- Whether to activate kill switch or disable posting.

## Waiting points
- Initial dashboard refresh (`refreshAll`) loads all operational datasets.
- Every action waits on API completion, then triggers a full refresh.

Assumption (explicit):
- The current UI is a single-page command center with no route-level navigation; panel order defines workflow priority.
