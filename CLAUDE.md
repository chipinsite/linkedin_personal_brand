# CLAUDE.md

## Sphiwe LinkedIn Personal Brand Autoposter

### Product Specification v1.0

---

## 1. Product Vision

This application enables a single user to build a LinkedIn personal brand by publishing one high quality post per day. The system manages content research, draft generation, approval workflows, scheduled publishing, and early comment engagement in a compliant and controlled manner.

The long term goal is to establish thought leadership in three domains: Adtech, Agentic AI in Adtech, and AI in advertising.

---

## 2. Core Outcomes

| Outcome | Acceptance Criteria |
|---------|---------------------|
| Daily posting | Exactly one post published per day when enabled |
| Randomised timing | Post time selected randomly between 08:00 and 17:00 SAST |
| Format variety | System rotates between text only, image based, and carousel or document posts |
| Tone variety | System rotates between educational, opinionated, direct, and exploratory tones |
| Learning loop | System tracks engagement metrics and adjusts format and tone weighting over time |

---

## 3. Compliance and Risk Mitigation

### 3.1 LinkedIn Terms of Service Constraints

LinkedIn prohibits automated posting, scraping, and bot driven engagement. The following constraints apply:

- No direct API access for posting without official LinkedIn Marketing API approval
- No browser automation or headless browser posting
- No automated comment generation without human approval
- No fake engagement or coordinated activity

### 3.2 Compliant Architecture

The system operates as a content preparation and approval tool with manual publishing as the default path.

**Primary approach: Manual publish with copy assistance**

1. System generates draft content
2. Draft sent to user via Telegram for approval
3. User copies approved content and publishes manually via LinkedIn app or web
4. System monitors published post via LinkedIn API read access for engagement tracking

**Secondary approach: LinkedIn Marketing API with approved access**

If official API access is granted through a LinkedIn Marketing Developer Application:

1. System generates draft content
2. Draft sent to user for approval
3. Approved content published via LinkedIn Marketing API
4. Comment monitoring via API webhooks or polling

The specification assumes the secondary approach is the target state, with the primary approach as fallback.

### 3.3 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Account suspension | Human approval gate before any publishing |
| API rate limits | Conservative polling intervals and exponential backoff |
| Content policy violation | Brand voice rules, banned phrases, and manual review |
| Comment engagement abuse | Hard limit of 5 auto replies per post, escalation for sensitive topics |

---

## 4. Content Strategy

### 4.1 Content Pyramid Structure

The content pyramid follows a Gary Vaynerchuk inspired model adapted for B2B thought leadership.

**Tier 1: Pillar Themes**

These are the three core topics that anchor all content:

1. Adtech fundamentals and market dynamics
2. Agentic AI applications in advertising technology
3. Artificial intelligence in advertising operations and strategy

**Tier 2: Sub Themes**

Each pillar breaks into four to six sub themes:

| Pillar | Sub Themes |
|--------|------------|
| Adtech fundamentals | Programmatic buying, supply path optimisation, measurement and attribution, retail media, CTV and audio, privacy and identity |
| Agentic AI in Adtech | Autonomous campaign management, AI bidding agents, creative optimisation agents, reporting and insight agents, multi agent orchestration |
| AI in advertising | Generative creative, audience modelling, media mix modelling, conversational commerce, predictive analytics, AI ethics in marketing |

**Tier 3: Daily Post Ideas**

Each sub theme generates multiple post angles:

- News commentary on recent developments
- Framework or mental model explanations
- Contrarian takes on industry consensus
- Case study breakdowns with lessons
- Tool or platform reviews
- Future predictions with reasoning
- Personal experience and lessons learned
- Questions posed to the audience

### 4.2 Format Rotation Logic

The system maintains a format distribution target:

| Format | Target Distribution | Description |
|--------|---------------------|-------------|
| Text only | 50% | Pure text posts between 150 and 300 words |
| Image based | 30% | Single image with caption, image sourced or generated |
| Carousel or document | 20% | Multi page PDF or carousel with 5 to 10 slides |

Format selection uses weighted random sampling adjusted by recent engagement performance.

### 4.3 Tone Rotation Logic

The system maintains a tone distribution target:

| Tone | Target Distribution | Characteristics |
|------|---------------------|-----------------|
| Educational | 40% | Explains concepts, frameworks, or processes clearly |
| Opinionated | 25% | Takes a clear position on industry debates |
| Direct and concise | 20% | Short, punchy observations or provocations |
| Exploratory or reflective | 15% | Asks questions, shares uncertainty, invites discussion |

Tone selection uses weighted random sampling adjusted by recent engagement performance.

### 4.4 Content Guardrails

The following content types are prohibited:

- Fluff or filler content with no substance
- Overclaims about AI capabilities without evidence
- Hype language or buzzword heavy posts
- Unverified statistics or facts presented as truth
- Promotional content for products or services without disclosure
- Controversial political or social commentary unrelated to core themes
- Personal attacks on individuals or companies

All generated content must pass guardrail validation before entering the approval queue.

### 4.5 Research Source Strategy

**Month 1: Wide source pool**

The system draws from a broad range of sources:

| Source Type | Examples |
|-------------|----------|
| Trade publications | AdExchanger, Digiday, ExchangeWire, The Drum, Campaign |
| Vendor blogs | Google Ads blog, Meta for Business, The Trade Desk blog, LiveRamp |
| Independent commentary | Benedict Evans, Stratechery, Marketing Week |
| Academic and research | IAB reports, WARC, eMarketer, academic journals |
| African market sources | Bizcommunity, Memeburn, IAB South Africa |
| AI and tech sources | MIT Technology Review, Wired, The Information |

**Month 2 onwards: Performance based narrowing**

Sources are scored by engagement outcomes of posts that referenced them. Lower performing sources are deprioritised. The system maintains a minimum of 10 active sources to avoid echo chamber effects.

---

## 5. Comment Handling and Engagement

### 5.1 Comment Monitoring

The system monitors comments on each published post for 48 hours after publication.

Polling interval:
- First 2 hours: Every 10 minutes
- Hours 2 to 12: Every 30 minutes
- Hours 12 to 48: Every 2 hours

### 5.2 Automatic Reply Rules

| Rule | Specification |
|------|---------------|
| Reply limit | Maximum 5 auto replies per post |
| Reply window | Only comments received within 24 hours of posting |
| Reply tone | Friendly, professional, appreciative |
| Reply length | 1 to 3 sentences |
| Question inclusion | AI may include a follow up question if engagement likelihood is high |

Auto replies are disabled for:
- Comments containing profanity or harassment
- Comments on sensitive topics
- Comments from accounts flagged as spam
- Comments that are purely emoji based

### 5.3 Comment Triage and Escalation

A comment is classified as high value if it meets any of the following criteria:

| Signal | Description |
|--------|-------------|
| Partnership signal | Mentions collaboration, partnership, business opportunity |
| Technical question | Asks for detailed explanation or expertise |
| Objection or challenge | Disagrees with the post or raises counterarguments |
| Influential commenter | Account has more than 10,000 followers or is a known industry figure |
| Media inquiry | Mentions interview, quote, or article |

High value comments trigger escalation:

1. Notification sent to user
2. Notification includes suggested reply options
3. User responds manually or selects suggested reply

### 5.4 Do Not Engage List

The system does not auto reply to comments that contain:

- Harassment, threats, or abuse
- Political content unrelated to advertising
- Religious content
- Explicit content
- Spam or promotional links

---

## 6. Notification System

### 6.1 Notification Channels

The system supports three notification channels:

| Channel | Use Case |
|---------|----------|
| Telegram | Primary channel for draft approvals and escalations |
| WhatsApp | Backup channel for high priority escalations |
| Email | Daily summary and weekly reports |

### 6.2 Notification Payloads

**Draft Approval Notification**

```
Draft Ready for Approval

Theme: [Pillar > Sub Theme]
Format: [Text | Image | Carousel]
Tone: [Educational | Opinionated | Direct | Exploratory]

---

[Draft content]

---

Actions:
✅ Approve
✏️ Edit
❌ Reject
```

**Comment Escalation Notification**

```
High Value Comment Detected

Post: [Post title or first line]
Link: [LinkedIn post URL]

Commenter: [Name]
Profile: [LinkedIn profile URL]
Followers: [Count]

Comment:
[Comment text]

Escalation Reason: [Partnership signal | Technical question | Objection | Influential | Media]

Suggested Replies:
1. [Option 1]
2. [Option 2]
3. [Option 3]

Actions:
📤 Reply with option
✍️ Custom reply
🚫 Ignore
```

**Daily Summary Email**

```
Daily LinkedIn Summary - [Date]

Post Performance:
- Post: [Title]
- Impressions: [Count]
- Reactions: [Count]
- Comments: [Count]
- Shares: [Count]

Comment Activity:
- Total comments: [Count]
- Auto replies sent: [Count]
- Escalations: [Count]
- Pending responses: [Count]

Upcoming:
- Tomorrow's draft: [Status]
- Scheduled time: [Time]
```

---

## 7. Configuration and Admin

### 7.1 Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| timezone | Africa/Johannesburg | Timezone for scheduling |
| posting_window_start | 08:00 | Earliest posting time |
| posting_window_end | 17:00 | Latest posting time |
| posting_enabled | true | Master switch for daily posting |
| comment_replies_enabled | true | Master switch for auto replies |
| max_auto_replies | 5 | Maximum auto replies per post |
| escalation_follower_threshold | 10000 | Follower count for influential commenter flag |

### 7.2 Brand Voice Rules

Configurable rules that apply to all generated content:

| Rule | Example Configuration |
|------|----------------------|
| first_person_style | Use "I" not "we" |
| sentence_structure | Complete sentences, active voice |
| opening_style | Direct, no filler phrases |
| closing_style | Clear call to action or question |
| emoji_usage | None in body, optional single emoji at end |
| hashtag_limit | Maximum 3 hashtags |

### 7.3 Banned Phrases List

A configurable list of phrases that trigger content rejection:

```
game changer
disrupt
synergy
leverage (as verb)
pivot
deep dive
unpack
double down
move the needle
low hanging fruit
```

### 7.4 Kill Switch

A hard kill switch immediately stops:

- All scheduled post publishing
- All auto comment replies
- All outbound API calls to LinkedIn

The kill switch is accessible via:
- Admin dashboard button
- Telegram command
- Direct API endpoint

Kill switch activation sends immediate notification to all configured channels.

---

## 8. Data and Storage

### 8.1 Data Model Overview

| Entity | Description | Retention |
|--------|-------------|-----------|
| Draft | Generated post content awaiting approval | 30 days |
| ApprovedPost | Approved content awaiting publication | Until published |
| PublishedPost | Content that has been published | Indefinite |
| SourceMaterial | Research articles and citations used | 90 days |
| Comment | Comments received on published posts | 90 days |
| Reply | Replies sent to comments | 90 days |
| NotificationLog | Record of all notifications sent | 30 days |
| EngagementMetric | Performance data for learning loop | Indefinite |
| Secret | API tokens and credentials | Until rotated |

### 8.2 Draft Schema

```
Draft {
  id: UUID
  created_at: Timestamp
  pillar_theme: String
  sub_theme: String
  format: Enum[TEXT, IMAGE, CAROUSEL]
  tone: Enum[EDUCATIONAL, OPINIONATED, DIRECT, EXPLORATORY]
  content_body: Text
  image_url: String (nullable)
  carousel_document_url: String (nullable)
  sources: Array[SourceReference]
  status: Enum[PENDING, APPROVED, REJECTED, EXPIRED]
  approval_timestamp: Timestamp (nullable)
  rejection_reason: String (nullable)
  guardrail_check_passed: Boolean
  guardrail_violations: Array[String]
}
```

### 8.3 PublishedPost Schema

```
PublishedPost {
  id: UUID
  draft_id: UUID
  linkedin_post_id: String
  linkedin_post_url: String
  published_at: Timestamp
  scheduled_time: Timestamp
  actual_publish_time: Timestamp
  content_body: Text
  format: Enum[TEXT, IMAGE, CAROUSEL]
  tone: Enum[EDUCATIONAL, OPINIONATED, DIRECT, EXPLORATORY]
  impressions: Integer
  reactions: Integer
  comments_count: Integer
  shares: Integer
  engagement_rate: Float
  last_metrics_update: Timestamp
}
```

### 8.4 Comment Schema

```
Comment {
  id: UUID
  published_post_id: UUID
  linkedin_comment_id: String
  commenter_name: String
  commenter_profile_url: String
  commenter_follower_count: Integer (nullable)
  comment_text: Text
  commented_at: Timestamp
  is_high_value: Boolean
  high_value_reason: String (nullable)
  auto_reply_sent: Boolean
  auto_reply_text: String (nullable)
  auto_reply_sent_at: Timestamp (nullable)
  escalated: Boolean
  escalated_at: Timestamp (nullable)
  manual_reply_sent: Boolean
  manual_reply_text: String (nullable)
}
```

### 8.5 Secrets Management

| Secret | Storage | Rotation |
|--------|---------|----------|
| LinkedIn API credentials | Environment variable or secrets manager | 90 days |
| Telegram bot token | Environment variable or secrets manager | On compromise |
| WhatsApp API credentials | Environment variable or secrets manager | 90 days |
| Email SMTP credentials | Environment variable or secrets manager | 90 days |
| OpenAI or Claude API key | Environment variable or secrets manager | 90 days |
| Database connection string | Environment variable or secrets manager | On compromise |

Secrets are never logged, never stored in code, and never transmitted in notification payloads.

---

## 9. Architecture

### 9.1 High Level System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Telegram   │  │  WhatsApp   │  │  Email                  │  │
│  │  Bot        │  │  Integration│  │  (Daily Summary)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Core                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Content    │  │  Scheduling │  │  Engagement             │  │
│  │  Engine     │  │  Service    │  │  Service                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Approval   │  │  Learning   │  │  Notification           │  │
│  │  Workflow   │  │  Loop       │  │  Service                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  LinkedIn   │  │  LLM API    │  │  Research               │  │
│  │  API        │  │  (Claude)   │  │  Sources                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  PostgreSQL │  │  Redis      │  │  Object Storage         │  │
│  │  Database   │  │  Queue      │  │  (Images, Carousels)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Component Responsibilities

**Content Engine**
- Research aggregation from configured sources
- Content pyramid planning and topic selection
- Draft generation using LLM
- Format and tone selection
- Guardrail validation
- Image and carousel generation coordination

**Scheduling Service**
- Random time selection within posting window
- Queue management for pending publications
- Timezone handling
- Publishing execution or manual publish notification

**Engagement Service**
- Comment polling and ingestion
- Comment classification and triage
- Auto reply generation and sending
- Escalation detection and routing

**Approval Workflow**
- Draft queue management
- Telegram interaction handling
- Edit processing
- Approval and rejection recording

**Learning Loop**
- Engagement metric collection
- Format performance analysis
- Tone performance analysis
- Source performance analysis
- Weight adjustment for future selections

**Notification Service**
- Multi channel message routing
- Payload formatting
- Delivery confirmation
- Retry handling

### 9.3 End to End Workflows

#### 9.3.1 Research and Ideation Workflow

```
1. Daily at 02:00 SAST, Research Job runs
2. Fetch latest articles from configured sources (RSS, API, scraping)
3. Filter articles by relevance to pillar themes
4. Summarise each article using LLM
5. Store summaries with source citations
6. Score articles by novelty and relevance
7. Select top 10 articles for potential content
8. Pass to Content Pyramid Planning
```

#### 9.3.2 Draft Generation Workflow

```
1. Daily at 04:00 SAST, Draft Generation Job runs
2. Select pillar theme based on rotation schedule
3. Select sub theme based on recent coverage gaps
4. Select format using weighted random (adjusted by performance)
5. Select tone using weighted random (adjusted by performance)
6. Generate draft using LLM with selected parameters
7. Run guardrail validation
8. If guardrails fail, regenerate with stricter constraints (max 3 attempts)
9. If still failing, escalate for manual creation
10. Store draft with PENDING status
11. Send approval notification via Telegram
```

#### 9.3.3 Telegram Approval Workflow

```
1. User receives draft notification
2. User selects action:
   - APPROVE: Draft status set to APPROVED, scheduled for publishing
   - EDIT: Bot prompts for edited content, stores update, re-validates
   - REJECT: Draft status set to REJECTED, reason recorded, new draft generated
3. If APPROVE, calculate random publish time within window
4. Store scheduled time
5. Confirm to user with scheduled time
```

#### 9.3.4 Scheduling and Publishing Workflow

```
1. Scheduler checks for posts due in next 5 minutes
2. For each due post:
   a. Retrieve approved content
   b. If LinkedIn API available:
      - Publish via API
      - Store LinkedIn post ID and URL
      - Update status to PUBLISHED
   c. If manual publish mode:
      - Send notification with content and "Ready to publish" message
      - User publishes manually
      - User confirms publication with post URL
      - Store URL and update status
3. Start comment monitoring job for published post
4. Send confirmation notification
```

#### 9.3.5 Comment Monitoring Workflow

```
1. For each post in monitoring window (48 hours):
   a. Poll LinkedIn API for new comments
   b. For each new comment:
      - Store comment record
      - Run triage classification
      - If high value: escalate
      - If auto reply eligible: generate and send reply
      - If do not engage: mark as ignored
2. Update polling interval based on post age
3. After 48 hours, stop monitoring
```

#### 9.3.6 Escalation Workflow

```
1. Comment flagged as high value
2. Generate 3 suggested reply options
3. Build escalation notification payload
4. Send to Telegram (primary) and WhatsApp (backup if configured)
5. Wait for user action:
   - SELECT OPTION: Send selected reply via API
   - CUSTOM REPLY: Prompt for text, send via API
   - IGNORE: Mark comment as manually ignored
6. Log action taken
7. Update comment record
```

### 9.4 Error Handling and Retries

| Operation | Retry Strategy | Max Retries | Backoff |
|-----------|----------------|-------------|---------|
| Research fetch | Exponential | 3 | 1min, 2min, 4min |
| LLM generation | Exponential | 3 | 30sec, 1min, 2min |
| LinkedIn API publish | Exponential | 5 | 1min, 2min, 4min, 8min, 16min |
| LinkedIn API read | Exponential | 3 | 30sec, 1min, 2min |
| Notification send | Exponential | 5 | 10sec, 30sec, 1min, 2min, 4min |

Failed operations after max retries trigger:
- Alert notification to admin
- Entry in error log with full context
- Graceful degradation where possible

### 9.5 Rate Limiting Strategy

| API | Limit | Strategy |
|-----|-------|----------|
| LinkedIn Marketing API | 100 calls per day | Batch operations, cache aggressively |
| LinkedIn comment polling | 1 call per post per interval | Respect intervals defined in 5.1 |
| LLM API | Model dependent | Queue requests, track token usage |
| Research sources | Varies | Respect robots.txt, 1 request per second minimum |

### 9.6 Security

| Concern | Mitigation |
|---------|------------|
| API credential exposure | Secrets manager, environment variables, no logging |
| Unauthorised access | Single user model, no public endpoints |
| Data breach | Encryption at rest, TLS in transit |
| Prompt injection | Input sanitisation, output validation |
| LinkedIn account compromise | Approval workflow, kill switch, audit log |

### 9.7 Observability

**Logs**

| Log Type | Retention | Content |
|----------|-----------|---------|
| Application logs | 30 days | All operations, errors, warnings |
| Audit log | 90 days | All approvals, publications, configuration changes |
| API call log | 14 days | All external API calls with response codes |

**Metrics**

| Metric | Description |
|--------|-------------|
| posts_generated_total | Counter of drafts generated |
| posts_approved_total | Counter of approved posts |
| posts_published_total | Counter of published posts |
| comments_received_total | Counter of comments |
| auto_replies_sent_total | Counter of auto replies |
| escalations_total | Counter of escalations |
| llm_tokens_used_total | Counter of LLM token consumption |
| api_errors_total | Counter of API errors by service |

**Alerts**

| Alert | Trigger | Severity |
|-------|---------|----------|
| Publishing failed | Post not published within 30 min of scheduled time | High |
| LinkedIn API error | 3 consecutive API failures | High |
| LLM generation failed | Draft generation fails after retries | Medium |
| Kill switch activated | Kill switch triggered | Critical |
| High escalation volume | More than 5 escalations in 24 hours | Low |

---

## 10. AI Behaviour and Prompts

### 10.1 Research Summarisation Prompt

```
You are a research assistant for a thought leader in Adtech and AI in advertising.

Summarise the following article in 3 to 5 sentences. Focus on:
- Key insight or finding
- Why it matters for advertising professionals
- Any contrarian or novel perspectives

Article:
{article_text}

Source: {source_name}
Published: {publish_date}

Respond in plain text. Do not include opinions. Only state what the article claims.
If the article makes claims without evidence, note this.
```

### 10.2 Content Pyramid Planning Prompt

```
You are a content strategist planning LinkedIn posts for a thought leader.

Given the following research summaries from the past week:
{research_summaries}

And the following post history from the past 30 days:
{post_history}

Recommend the next 7 days of content:
- For each day, specify: pillar theme, sub theme, angle, format suggestion
- Ensure variety in themes and formats
- Avoid repeating angles used in the past 14 days
- Prioritise timely topics when relevant

Respond in structured format:
Day 1: [Pillar] > [Sub Theme] | Angle: [description] | Format: [TEXT/IMAGE/CAROUSEL]
...
```

### 10.3 Daily Post Generation Prompt

```
You are writing a LinkedIn post for Sphiwe, a Head of Sales with 19 years of commercial experience in Sub-Saharan Africa, specialising in Adtech and AI in advertising.

Post parameters:
- Pillar theme: {pillar_theme}
- Sub theme: {sub_theme}
- Format: {format}
- Tone: {tone}
- Research context: {research_summary}

Writing rules:
- Use South African English
- Write in first person singular (I, my)
- No hype language or buzzwords
- No unverified claims presented as fact
- If making predictions, label them as such
- Maximum 300 words for text posts
- Include a clear takeaway or question at the end
- Maximum 3 hashtags
- No emojis in the body

Banned phrases: {banned_phrases_list}

Generate the post now.
```

### 10.4 Tone and Format Selection Prompt

```
You are selecting the optimal tone and format for today's LinkedIn post.

Current performance data:
- TEXT format: {text_engagement_rate}% average engagement
- IMAGE format: {image_engagement_rate}% average engagement  
- CAROUSEL format: {carousel_engagement_rate}% average engagement

- EDUCATIONAL tone: {edu_engagement_rate}% average engagement
- OPINIONATED tone: {opinion_engagement_rate}% average engagement
- DIRECT tone: {direct_engagement_rate}% average engagement
- EXPLORATORY tone: {explore_engagement_rate}% average engagement

Recent posts (last 7 days):
{recent_posts_format_tone}

Today's topic: {topic_summary}

Select format and tone that:
1. Balances performance optimisation with variety
2. Matches the nature of today's topic
3. Avoids repetition from recent posts

Respond:
FORMAT: [TEXT/IMAGE/CAROUSEL]
TONE: [EDUCATIONAL/OPINIONATED/DIRECT/EXPLORATORY]
REASONING: [1-2 sentences]
```

### 10.5 Comment Reply Generation Prompt

```
You are writing a reply to a LinkedIn comment on Sphiwe's post.

Original post summary: {post_summary}

Comment:
Author: {commenter_name}
Text: {comment_text}

Reply rules:
- Friendly and professional tone
- 1 to 3 sentences maximum
- Acknowledge the commenter's point
- Add value where possible
- May include a follow up question if it would genuinely advance the conversation
- No promotional language
- No excessive gratitude or flattery

Generate a reply.
```

### 10.6 Comment Triage Prompt

```
You are triaging a comment on a LinkedIn post for escalation.

Post summary: {post_summary}

Comment:
Author: {commenter_name}
Follower count: {follower_count}
Text: {comment_text}

Classify this comment:

1. Is this a high value comment? (YES/NO)
2. If YES, what is the reason?
   - PARTNERSHIP_SIGNAL: Mentions collaboration, business opportunity
   - TECHNICAL_QUESTION: Asks for detailed expertise
   - OBJECTION: Disagrees or challenges the post
   - INFLUENTIAL: High profile commenter (>10,000 followers or known figure)
   - MEDIA_INQUIRY: Mentions interview, quote, article
   - NONE: Not high value

3. Should auto reply be sent? (YES/NO)
   - NO if: harassment, spam, sensitive topic, emoji only, or high value

4. If escalating, generate 3 suggested reply options.

Respond in structured format:
HIGH_VALUE: [YES/NO]
REASON: [category or NONE]
AUTO_REPLY: [YES/NO]
SUGGESTED_REPLIES:
1. [reply option 1]
2. [reply option 2]
3. [reply option 3]
```

### 10.7 Grounding Rules

All AI generated content must adhere to:

1. No claim is presented as fact unless it can be traced to a source
2. Predictions and opinions are clearly labelled as such
3. Statistical claims include source attribution
4. When uncertain, use hedging language: "Some argue...", "Evidence suggests...", "One perspective is..."
5. Never fabricate quotes, statistics, or case studies
6. If asked to generate content outside core themes, decline

---

## 11. Tech Stack

### 11.1 Recommended MVP Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| Backend runtime | Python 3.11+ | Strong ecosystem for AI, APIs, scheduling |
| Web framework | FastAPI | Async support, automatic OpenAPI docs |
| Task queue | Celery with Redis | Reliable scheduling and background jobs |
| Database | PostgreSQL | Robust, good JSON support, well understood |
| Cache | Redis | Also serves as Celery broker |
| LLM | Claude API (Anthropic) | Strong reasoning, controllable output |
| Object storage | AWS S3 or Cloudflare R2 | Image and document storage |
| Hosting | Railway or Render | Simple deployment, managed Postgres and Redis |
| Telegram bot | python-telegram-bot | Mature library, good documentation |
| WhatsApp | WhatsApp Business API via Twilio | Reliable, documented |
| Email | Resend or SendGrid | Simple transactional email |

### 11.2 Local Development Workflow

```
1. Clone repository
2. Copy .env.example to .env and configure secrets
3. docker-compose up -d (PostgreSQL, Redis)
4. python -m venv venv && source venv/bin/activate
5. pip install -r requirements.txt
6. alembic upgrade head (database migrations)
7. python manage.py seed_config (load default configuration)
8. celery -A app.worker worker --loglevel=info (background worker)
9. celery -A app.worker beat --loglevel=info (scheduler)
10. uvicorn app.main:app --reload (API server)
```

### 11.3 Deployment Approach

**Option A: Railway (recommended for MVP)**

- Single repository deployment
- Managed PostgreSQL and Redis add-ons
- Environment variable management
- Automatic HTTPS
- GitHub integration for CI/CD

**Option B: Self-hosted on VPS**

- DigitalOcean or Hetzner droplet
- Docker Compose for all services
- Nginx reverse proxy
- Let's Encrypt for SSL
- Systemd for process management

### 11.4 Monthly Cost Estimates

| Service | Estimated Cost (USD) |
|---------|---------------------|
| Railway hosting (Pro) | $20 |
| PostgreSQL (Railway) | Included |
| Redis (Railway) | Included |
| Claude API (Anthropic) | $30 to $50 |
| Cloudflare R2 storage | $5 |
| Twilio WhatsApp | $15 |
| Resend email | $0 (free tier) |
| Domain and DNS | $1 |
| **Total** | **$71 to $91** |

### 11.5 Third Party Dependencies and Risks

| Dependency | Risk | Mitigation |
|------------|------|------------|
| LinkedIn API | Access may be revoked, terms may change | Manual publish fallback, conservative usage |
| Claude API | Rate limits, pricing changes | Usage tracking, budget alerts, fallback to GPT-4 |
| Telegram | Service availability | WhatsApp as backup channel |
| Research sources | Paywalls, blocking, format changes | Multiple source pool, graceful degradation |

---

## 12. Acceptance Checklist

### 12.1 Core Functionality

- [ ] System generates exactly one draft per day
- [ ] Draft includes pillar theme, sub theme, format, and tone
- [ ] Format rotation follows target distribution
- [ ] Tone rotation follows target distribution
- [ ] Guardrail validation rejects banned phrases
- [ ] Guardrail validation flags unverified claims
- [ ] Draft sent to Telegram with approve/edit/reject options
- [ ] Approved drafts scheduled within posting window
- [ ] Scheduled time is randomised within window
- [ ] Published posts tracked with LinkedIn URL

### 12.2 Comment Handling

- [ ] Comments polled according to defined intervals
- [ ] Comments classified for triage
- [ ] Auto replies sent to eligible comments
- [ ] Auto reply limit of 5 per post enforced
- [ ] High value comments trigger escalation
- [ ] Escalation notification includes suggested replies
- [ ] Do not engage comments are ignored

### 12.3 Notifications

- [ ] Telegram receives draft approvals
- [ ] Telegram receives escalations
- [ ] WhatsApp receives high priority escalations
- [ ] Email receives daily summary
- [ ] All notifications include required payload fields

### 12.4 Configuration

- [ ] Timezone configurable
- [ ] Posting window configurable
- [ ] Posting can be enabled/disabled
- [ ] Comment replies can be enabled/disabled
- [ ] Brand voice rules configurable
- [ ] Banned phrases list configurable
- [ ] Kill switch immediately stops all activity

### 12.5 Learning Loop

- [ ] Engagement metrics collected for all posts
- [ ] Format performance tracked
- [ ] Tone performance tracked
- [ ] Source performance tracked
- [ ] Weights adjusted based on performance data

### 12.6 Security and Compliance

- [ ] No secrets logged or exposed
- [ ] All API calls use encrypted transport
- [ ] Approval required before any publication
- [ ] Audit log captures all sensitive operations
- [ ] Kill switch accessible via multiple channels

---

## 13. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-02-01 | Initial specification |
| 0.1 | 2026-02-06 | First runnable MVP slice implemented in backend with passing smoke tests |
| 0.2 | 2026-02-06 | Added source ingestion pipeline, Claude-backed generation path, and grounded draft citations with passing tests |
| 0.3 | 2026-02-06 | Added write auth, audit logging, stricter claim guardrails, and LinkedIn read polling scaffold with passing tests |
| 0.4 | 2026-02-06 | Added persisted comment monitoring windows, interval-based due polling, and LinkedIn mock-contract polling tests |
| 0.5 | 2026-02-06 | Added learning-loop persistence, metrics ingestion, adaptive weights, and nightly recompute with passing tests |
| 0.6 | 2026-02-06 | Added LinkedIn adapter contract with pagination, retries, and error taxonomy plus tests |
| 0.7 | 2026-02-06 | Added read/write auth profiles with optional enforced read access and compatibility mode |
| 0.8 | 2026-02-06 | Added daily reporting endpoints and scheduled summary delivery workflow |
| 0.9 | 2026-02-06 | Added operational readiness layer: deep health checks, readiness endpoint, Makefile, and CI workflow |
| 1.1 | 2026-02-08 | Added frontend automated smoke testing harness (Vitest + Testing Library) and integrated tests into unified smoke execution |
| 1.2 | 2026-02-08 | Expanded frontend automated tests to cover draft generate/reject action workflows and API call-path assertions |
| 1.3 | 2026-02-08 | Expanded frontend automated tests to cover draft approve and manual publish confirmation action workflows |

---

*End of specification*

---

## 14. Implementation Update (2026-02-06)

This section records what is now implemented in code for the MVP scaffold.

### 14.1 Delivered in Backend

- FastAPI routes for core lifecycle:
  - `POST /drafts/generate`
  - `POST /drafts/{id}/approve`
  - `POST /drafts/{id}/reject`
  - `POST /posts/publish-due`
  - `POST /posts/{id}/confirm-manual-publish`
  - `POST /comments`
  - `GET /admin/config`
  - `POST /admin/kill-switch/on`
  - `POST /admin/kill-switch/off`
- Data models in place for `Draft`, `PublishedPost`, `Comment`, and `NotificationLog`.
- Guardrail validator implemented with:
  - banned phrase checks
  - hashtag limit (max 3)
  - post length limit (max 300 words)
  - automatic rejection when fallback regeneration still fails guardrails
- Draft generation pipeline implemented:
  - weighted format and tone selection using target distributions
  - pillar/sub-theme rotation from configured pools
  - compliant fallback post template when guardrails fail
- Scheduling logic implemented:
  - random scheduled time inside configured window (`08:00` to `17:00` by default)
  - timezone-aware scheduling with `Africa/Johannesburg` config
- Manual publish flow implemented:
  - one-time due post reminder via Telegram (idempotent reminder state tracked)
  - post publication confirmation endpoint with LinkedIn URL recording
- Telegram integration implemented:
  - outbound approval/reminder notifications via bot HTTP API
  - command bot with `/start`, `/pending`, `/approve`, `/reject`
  - optional chat-id authorization gate
- Celery jobs and beat schedule implemented:
  - daily draft generation (04:00)
  - due-post checks every 5 minutes
  - comment polling placeholder every 10 minutes

### 14.2 Current Constraints

- LinkedIn write/read API integration remains intentionally disabled in MVP and uses manual publish mode.
- LLM provider integration is currently template-driven and does not yet call external Claude APIs.
- Comment polling task is a placeholder until LinkedIn read API access is available.
- Runtime config changes via admin endpoints are in-memory and not persisted to database yet.

### 14.3 Accepted Compliance Position

The system currently enforces a compliant posture by default:

- Human approval before publication remains mandatory.
- No browser automation or unauthorized posting automation is used.
- Manual posting path is primary until official LinkedIn API approval exists.

---

## 15. Recommended Next Build Priorities

1. Add persistent configuration storage (DB-backed settings) so kill switch and feature toggles survive restarts.
2. Add Alembic migration generation and remove dev-only auto table creation for production parity.
3. Integrate Claude API for draft generation and summarization with strict source attribution payloads.
4. Add source ingestion pipeline (RSS/API fetch + relevance filtering + citation storage).
5. Add a lightweight frontend/admin dashboard for:
   - pending approvals
   - post queue and publish confirmations
   - comment escalations
   - kill switch state
6. Add authentication and audit trails on all mutating endpoints.
7. Add unit and integration tests for guardrails, scheduling, approval state transitions, and comment triage.

---

## 16. v0.1 Readiness (2026-02-06)

### 16.1 v0.1 Scope Locked

v0.1 is defined as the first testable vertical slice with:

- Persistent runtime control flags in database (`posting_enabled`, `comment_replies_enabled`, `kill_switch`)
- Migration-first schema management via Alembic
- Automated smoke test covering core lifecycle:
  - generate draft
  - approve draft
  - schedule due post notification path
  - manual publish confirmation
  - comment triage behavior
  - posting toggle enforcement

### 16.2 v0.1 Implementation Added

- New DB-backed config model: `app_config`
- New config service: `app/services/config_state.py`
- Admin endpoints now persist to DB:
  - `POST /admin/kill-switch/on`
  - `POST /admin/kill-switch/off`
  - `POST /admin/posting/on`
  - `POST /admin/posting/off`
- Workflow runtime gates now use persistent config state
- Comment auto-reply logic now respects:
  - kill switch
  - comment replies enabled flag
  - max auto reply cap
- Added Alembic assets:
  - `alembic/script.py.mako`
  - `alembic/versions/0001_initial.py`
- Added smoke test suite:
  - `Backend/tests/test_v01_smoke.py`

### 16.3 First Test Execution Status

- Smoke test command prepared:
  - `python3 -m unittest discover -v -s tests -p 'test_*.py'`
- Executed successfully on 2026-02-06 after dependency compatibility updates:
  - `psycopg2-binary` replaced with `psycopg[binary]>=3.2,<4`
  - `pydantic` and `pydantic-settings` moved to Python 3.14-compatible ranges
  - `SQLAlchemy` moved to `>=2.0.39,<2.1` for Python 3.14 typing compatibility
- Current smoke result:
  - 2 tests passed (`OK`)
  - Remaining non-blocking warning from Starlette on Python 3.14 deprecation path
- Migration validation result:
  - `alembic upgrade head` executed successfully against SQLite test database

### 16.4 Definition of Done for v0.1

v0.1 is now marked runnable. The smoke suite passes in the local environment.

Validated commands:

- `alembic upgrade head`
- `python3 -m unittest discover -v -s tests -p 'test_*.py'`

---

## 17. v0.2 Readiness (2026-02-06)

### 17.1 v0.2 Scope

v0.2 extends v0.1 with research grounding and LLM-assisted generation:

- RSS source ingestion and storage
- Article summarisation path for source material
- Claude generation path for drafts with deterministic fallback
- Source citation capture on generated drafts
- New smoke tests for ingestion and grounded generation behavior

### 17.2 v0.2 Implementation Added

- New model and migration support:
  - `source_materials` table
  - `drafts.source_citations`
  - `alembic/versions/0002_sources_and_citations.py`
- New services:
  - `app/services/research_ingestion.py`
  - `app/services/llm.py`
- New API routes:
  - `POST /sources/ingest`
  - `GET /sources`
- Worker update:
  - `ingest_research_sources` Celery task
  - beat schedule at 02:00 for research ingestion
- Draft generation update:
  - selects research context from `source_materials`
  - stores citations JSON in draft record
  - includes source preview in Telegram approval payload
- Dependency updates for runtime compatibility and feed ingestion:
  - `feedparser`
  - Python 3.14-compatible `pydantic`, `pydantic-settings`, `SQLAlchemy`, and `psycopg`

### 17.3 v0.2 Test Status

Executed on 2026-02-06:

- `alembic upgrade head` (validated upgrades through `0002_sources_and_citations`)
- `python3 -m unittest discover -v -s tests -p 'test_*.py'`

Result:

- 4 tests passed (`OK`)
  - `test_v01_smoke.py` (2 tests)
  - `test_v02_research_and_generation.py` (2 tests)

### 17.4 Remaining Constraints

- Claude usage requires valid `LLM_API_KEY`; without it, system uses deterministic fallback generation/summarisation.
- LinkedIn API publish/read integration remains manual-first and compliant by design in current version.
- Comment polling job is still placeholder pending LinkedIn read integration.

---

## 18. v0.3 Readiness (2026-02-06)

### 18.1 v0.3 Scope

v0.3 extends v0.2 with security and observability hardening:

- optional API key auth for all mutating endpoints
- persistent audit logs for API and worker writes
- stricter guardrails against unsourced/overconfident claims
- LinkedIn read polling scaffold wired into API and worker paths

### 18.2 v0.3 Implementation Added

- New auth service:
  - `app/services/auth.py`
  - `APP_API_KEY` + `x-api-key` header support
- New audit service and model:
  - `app/services/audit.py`
  - `AuditLog` model and `audit_logs` table
  - migration: `alembic/versions/0003_audit_logs.py`
- Mutating route protection and auditing added to:
  - drafts, posts, comments, sources, admin
- New admin read endpoint:
  - `GET /admin/audit-logs`
- Guardrails strengthened in `app/services/guardrails.py`:
  - `UNVERIFIED_CLAIM_LANGUAGE`
  - `STAT_WITHOUT_SOURCE`
  - `QUOTE_WITHOUT_SOURCE`
- LinkedIn read scaffold:
  - `app/services/linkedin.py`
  - `app/services/engagement.py`
  - `POST /engagement/poll`
  - Celery `poll_comments` now executes scaffolded polling flow

### 18.3 v0.3 Test Status

Executed on 2026-02-06:

- `alembic upgrade head` (validated through `0003_audit_logs`)
- `python3 -m unittest discover -v -s tests -p 'test_*.py'`

Result:

- 6 tests passed (`OK`)
  - `test_v01_smoke.py` (2)
  - `test_v02_research_and_generation.py` (2)
  - `test_v03_security_and_audit.py` (2)

### 18.4 Remaining Constraints

- `APP_API_KEY` enforcement is optional by design for local/dev compatibility; set it in production.
- LinkedIn comment polling remains scaffold-only until official read API contract is implemented.
- Framework deprecation warning persists from Starlette/Python 3.14 compatibility path but is non-blocking.

---

## 19. v0.4 Readiness (2026-02-06)

### 19.1 v0.4 Scope

v0.4 extends v0.3 with robust comment monitoring execution:

- persistent monitoring window fields on published posts
- interval-based due polling logic aligned to post age
- monitoring state initialization at publish confirmation
- monitoring observability endpoint
- deterministic LinkedIn mock contract support for polling tests

### 19.2 v0.4 Implementation Added

- Data model updates on `published_posts`:
  - `comment_monitoring_started_at`
  - `comment_monitoring_until`
  - `last_comment_poll_at`
- Migration added:
  - `alembic/versions/0004_comment_monitoring_windows.py`
- Publish confirmation behavior updated:
  - starts 48-hour monitoring window automatically
  - extracts/stores `linkedin_post_id` from confirmed URL when missing
- Engagement service updates:
  - `polling_interval_for_post_age()` implementing:
    - 0 to 2 hours: 10m
    - 2 to 12 hours: 30m
    - 12 to 48 hours: 2h
  - due-post filtering using `last_comment_poll_at`
  - timezone normalization for SQLite naive datetimes
- New endpoint:
  - `GET /engagement/status` with monitored/active/due counts
- LinkedIn contract enhancement:
  - `LINKEDIN_MOCK_COMMENTS_JSON` supports deterministic testable comment payloads by post id

### 19.3 v0.4 Test Status

Executed on 2026-02-06:

- `alembic upgrade head` (validated through `0004_comment_monitoring_windows`)
- `python3 -m unittest discover -v -s tests -p 'test_*.py'`

Result:

- 9 tests passed (`OK`)
  - `test_v01_smoke.py` (2)
  - `test_v02_research_and_generation.py` (2)
  - `test_v03_security_and_audit.py` (2)
  - `test_v04_monitoring_and_polling.py` (3)

### 19.4 Remaining Constraints

- Live LinkedIn read API endpoint mapping is still stubbed and requires approved API contract credentials.
- Polling logic is production-ready for scheduling/state handling but currently depends on mock/empty read source when API integration is absent.

---

## 20. v0.5 Readiness (2026-02-06)

### 20.1 v0.5 Scope

v0.5 extends v0.4 with learning-loop persistence and adaptive selection:

- per-post engagement metric snapshot ingestion
- persisted adaptive weights for format and tone selection
- recompute pipeline from historical post performance
- API and worker controls for learning recomputation

### 20.2 v0.5 Implementation Added

- New data models:
  - `engagement_metrics`
  - `learning_weights`
- Migration added:
  - `alembic/versions/0005_learning_metrics.py`
- New learning service:
  - `app/services/learning.py`
  - records metrics and computes blended adaptive weights
- Draft generation updated:
  - uses `learning_weights` via `get_effective_weight_maps()` in workflow
- New endpoints:
  - `POST /posts/{id}/metrics`
  - `GET /learning/weights`
  - `POST /learning/recompute`
- Worker schedule update:
  - `recompute_learning` task
  - nightly beat schedule at `23:30`

### 20.3 v0.5 Test Status

Executed on 2026-02-06:

- `alembic upgrade head` (validated through `0005_learning_metrics`)
- `python3 -m unittest discover -v -s tests -p 'test_*.py'`

Result:

- 10 tests passed (`OK`)
  - `test_v01_smoke.py` (2)
  - `test_v02_research_and_generation.py` (2)
  - `test_v03_security_and_audit.py` (2)
  - `test_v04_monitoring_and_polling.py` (3)
  - `test_v05_learning_loop.py` (1)

### 20.4 Remaining Constraints

- Current weight computation uses average engagement snapshots and simple blending; no confidence intervals or decay yet.
- Learning inputs depend on post metrics being submitted (`/posts/{id}/metrics`) or equivalent automated ingestion.
- LinkedIn live metrics/comment read integrations still need production API contract mapping.

---

## 21. v0.6 Readiness (2026-02-06)

### 21.1 v0.6 Scope

v0.6 hardens external comment ingestion via a concrete LinkedIn adapter contract:

- retry-aware LinkedIn fetch logic
- pagination handling for comment pages
- typed error taxonomy for auth/rate-limit/API failures
- deterministic mock contract for test and local simulation

### 21.2 v0.6 Implementation Added

- `app/services/linkedin.py` now includes:
  - `LinkedInApiError`
  - `LinkedInAuthError`
  - `LinkedInRateLimitError`
  - pagination parser and dedupe handling
  - retry loop for transient request errors
  - mock-page ingestion via `LINKEDIN_MOCK_COMMENTS_JSON`
- Engagement polling now handles adapter failures per-post without crashing batch execution.

### 21.3 v0.6 Test Status

- Added: `Backend/tests/test_v06_linkedin_adapter.py`
- Validated:
  - mock paging + dedupe behavior
  - pagination contract with transport mock
  - auth error propagation path

### 21.4 Remaining Constraints

- Real LinkedIn endpoint field mapping still depends on approved production API schema.
- Retry strategy is conservative and does not yet include jitter/backoff tuning.

---

## 22. v0.7 Readiness (2026-02-06)

### 22.1 v0.7 Scope

v0.7 introduces auth profiles beyond single-key mode:

- optional read endpoint protection
- separate read and write key controls
- compatibility with legacy single-key setup

### 22.2 v0.7 Implementation Added

- Config keys added:
  - `APP_READ_API_KEY`
  - `APP_WRITE_API_KEY`
  - `AUTH_ENFORCE_READ`
- `app/services/auth.py` now supports:
  - `require_read_access`
  - `require_write_access` with write-key precedence and fallback to `APP_API_KEY`
- Read endpoint protection applied to:
  - drafts list, posts list/detail, comments list, sources list, learning weights
  - engagement status, admin config, admin audit logs

### 22.3 v0.7 Test Status

- Added: `Backend/tests/test_v07_auth_profiles.py`
- Validated:
  - read key grants read only
  - write key required for mutating admin operation
  - unauthorized access returns HTTP 401

### 22.4 Remaining Constraints

- Key rotation endpoint is not yet implemented.
- Auth model is static-key based and not tied to user identities.

---

## 23. v0.8 Readiness (2026-02-06)

### 23.1 v0.8 Scope

v0.8 adds daily reporting and outbound summary workflow:

- on-demand daily summary aggregation
- delivery trigger endpoint
- scheduled daily summary task

### 23.2 v0.8 Implementation Added

- New reporting service:
  - `app/services/reporting.py`
- New endpoints:
  - `GET /reports/daily`
  - `POST /reports/daily/send`
- Worker task and schedule:
  - `send_daily_summary_report`
  - beat schedule at `18:30`
- Audit trail added for report sends (`report.daily.send` action).

### 23.3 v0.8 Test Status

- Added: `Backend/tests/test_v08_reporting.py`
- Validated:
  - report aggregation includes published/metric data
  - send endpoint executes and returns delivery state

### 23.4 Remaining Constraints

- Telegram remains primary report channel; email/WhatsApp delivery adapters are still not implemented.
- Report persistence history is currently represented via notification/audit logs, not a dedicated report table.

---

## 24. v0.9 Readiness (2026-02-06)

### 24.1 v0.9 Scope

v0.9 focuses on operational and release readiness:

- deeper health diagnostics
- readiness signal for deployment checks
- local automation shortcuts
- baseline CI workflow

### 24.2 v0.9 Implementation Added

- Health endpoints:
  - `GET /health/deep` (DB + Redis dependency checks)
  - `GET /health/readiness` (DB readiness gate)
- Added `Backend/Makefile` with:
  - `setup`, `test`, `migrate`, `lint`
- Added CI workflow:
  - `.github/workflows/backend-ci.yml`
  - installs deps, runs migrations, executes tests on PR/push affecting backend

### 24.3 v0.9 Validation Status

Executed on 2026-02-06:

- `python3 -m unittest discover -v -s tests -p 'test_*.py'`
- `alembic upgrade head`

Result:

- 17 tests passed (`OK`)
  - v0.1 through v0.9 suites combined
- migrations validated through `0005_learning_metrics`

### 24.4 Remaining Constraints

- Deep health currently reports degraded when Redis is unreachable, which is expected in minimal local setups.
- CI currently targets Python 3.12; production pinning strategy across environments should be finalized.

---

## 25. linkedinAlgos Alignment Validation (2026-02-08)

`linkedinAlgos.md` was reviewed in full and implementation was checked against its constraints on:

- feed ranking mechanics
- engagement quality signals
- anti-spam quality filters
- hashtag/keyword behavior
- early engagement (golden hour) dynamics

### 25.1 Alignment Changes Applied

- Guardrails strengthened to block behavior associated with downranking:
  - engagement bait phrases
  - excessive mentions
  - excessive hashtags
  - external links in post body
- Golden-hour author participation support added:
  - engagement reminder pushed on publish confirmation
- Topic and dwell optimization instructions reinforced in LLM generation prompt:
  - niche consistency requirement
  - short-structure/dwell guidance
- Production posting frequency guard added to avoid burst behavior.
- Algorithm alignment visibility endpoint added:
  - `GET /admin/algorithm-alignment`

### 25.2 Alignment Test and Validation Status

Executed on 2026-02-08:

- `python3 -m unittest discover -v -s tests -p 'test_*.py'`
- `alembic upgrade head`

Result:

- 18 tests passed (`OK`)
- migrations validated to current head (`0005_learning_metrics`)

### 25.3 Enforcement Rule for Future Versions

All future versions must preserve alignment with `/Users/sphiwemawhayi/Personal Brand/linkedinAlgos.md`.
Any new feature affecting content generation, publishing cadence, distribution, comments, or profile relevance must be evaluated against these algorithm constraints before release.

---

## 26. v1.0 Baseline (2026-02-08)

### 26.1 v1.0 Scope

v1.0 establishes a runnable baseline with complete backend workflow coverage and a functional frontend operations console:

- backend APIs covering content lifecycle, engagement, reporting, controls, and alignment visibility
- frontend console for operators to execute all primary workflows from one interface
- repeatable full-stack smoke validation command

### 26.2 v1.0 Implementation Added

- Frontend app scaffold and dashboard:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/services/api.js`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/Panel.jsx`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/styles/app.css`
- Project-level runbook:
  - `/Users/sphiwemawhayi/Personal Brand/README.md`
- Full-stack smoke script:
  - `/Users/sphiwemawhayi/Personal Brand/scripts/v1_smoke.sh`
- Repo hygiene updates:
  - `/Users/sphiwemawhayi/Personal Brand/.gitignore` now excludes frontend build/dependency artifacts

### 26.3 v1.0 Validation Status

Executed on 2026-02-08:

- `Backend/.venv/bin/python -m unittest discover -v -s tests -p 'test_*.py'`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- backend full suite passed (`18` tests, `OK`)
- frontend production build passed
- consolidated smoke flow passed

### 26.4 Algorithm Alignment Confirmation

v1.0 remains subject to section 25 enforcement. No frontend behavior bypasses backend content guardrails or posting controls; all publish and generation actions continue to flow through backend-aligned constraints.

---

## 27. Documentation and Execution Governance (2026-02-08)

### 27.1 Mandatory Build Logging

All builds must be logged in:

- `/Users/sphiwemawhayi/Personal Brand/AGENT_BUILD_LOG.md`

Using the fixed entry template exactly as defined in that file.

### 27.2 Execution Gate

Before any code change:

1. Create a `Pre Build` entry with Goal, Scope, and Planned Changes.
2. Do not modify code until the Pre Build entry exists.

After build execution:

1. Update the same entry to `Post Build`.
2. Fill Actual Changes, Files Touched, Tests and Validation, Result, Confidence Rating, and Known Gaps.
3. A build is incomplete until this Post Build update is done.

### 27.3 Uncertainty Handling

If a detail cannot be confidently determined, record `Unknown`.
No guessing is allowed.

### 27.4 Rules File

Repository-level rules are also defined in:

- `/Users/sphiwemawhayi/Personal Brand/DOCUMENTATION_RULES.md`

---

## 28. v1.1 Frontend Test Harness (2026-02-08)

### 28.1 v1.1 Scope

v1.1 closes the frontend validation gap by adding automated smoke testing and integrating it into the root smoke workflow:

- frontend test runner and DOM test environment
- baseline UI/data-load smoke test
- unified smoke command now runs frontend tests before build

### 28.2 v1.1 Implementation Added

- Frontend test tooling:
  - `vitest`
  - `@testing-library/react`
  - `@testing-library/jest-dom`
  - `jsdom`
- Frontend test config and setup:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/vite.config.js` (`test` block)
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/test/setup.js`
- Frontend smoke test:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - covers initial render and API-backed dashboard refresh using mocked `fetch`
- Frontend script update:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/package.json`
  - added `npm test` command
- Unified smoke script update:
  - `/Users/sphiwemawhayi/Personal Brand/scripts/v1_smoke.sh`
  - now runs frontend tests and then production build

### 28.3 v1.1 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend test files passed (`1/1`)
- frontend production build passed
- unified smoke run passed (backend tests + frontend tests + frontend build)

### 28.4 Remaining Constraints

- Frontend test coverage is intentionally minimal (smoke-level) and does not yet include user-flow interaction matrix or visual regression checks.
- Vulnerability warnings reported by `npm` remain to be triaged separately.

---

## 29. v1.2 Frontend Action Workflow Coverage (2026-02-08)

### 29.1 v1.2 Scope

v1.2 extends frontend test confidence from render-only smoke to action workflow coverage:

- validate draft generation action path
- validate draft rejection action path
- assert correct backend API endpoint invocations from UI actions

### 29.2 v1.2 Implementation Added

- Expanded frontend test suite:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
- Added deterministic mock API state harness for test scenarios:
  - method/path call capture
  - mutable draft state transitions for generate/reject flows
- Added tests:
  - `Generate` click triggers `POST /drafts/generate`
  - `Reject` click triggers `POST /drafts/{id}/reject`

### 29.3 v1.2 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`3/3`)
- frontend production build passed
- unified smoke run passed (backend tests + frontend tests + frontend build)

### 29.4 Remaining Constraints

- Tests still run at component/unit level with mocked network calls and do not yet validate full browser/runtime integration against a live backend.

---

## 30. v1.3 Approve and Publish Action Coverage (2026-02-08)

### 30.1 v1.3 Scope

v1.3 extends frontend action workflow test coverage to core approval and publish-confirmation paths:

- approve draft action path
- confirm manual publish action path

### 30.2 v1.3 Implementation Added

- Expanded frontend test suite in:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
- Added mock handlers and assertions for:
  - `POST /drafts/{id}/approve`
  - `POST /posts/{id}/confirm-manual-publish`
- Test suite now validates five key UI behaviors:
  - initial render/data load
  - generate
  - reject
  - approve
  - confirm publish

### 30.3 v1.3 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`5/5`)
- frontend production build passed
- unified smoke run passed (backend tests + frontend tests + frontend build)

### 30.4 Remaining Constraints

- Frontend action tests still run against mocked network responses and do not replace full end-to-end runtime verification.
