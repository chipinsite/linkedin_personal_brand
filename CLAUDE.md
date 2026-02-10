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
You are writing a LinkedIn post for Sphiwe, a Head of Sales with over 20 years of commercial experience in Sub-Saharan Africa, specialising in Adtech and AI in advertising.

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
| 1.4 | 2026-02-08 | Expanded frontend automated tests to cover source ingest and daily report send action workflows |
| 1.5 | 2026-02-08 | Added interactive frontend workflows for manual draft creation, post metrics updates, and comment creation with expanded action tests |
| 1.6 | 2026-02-08 | Completed frontend core control action test coverage for publish-due, poll, recompute, and admin kill/posting toggles |
| 1.7 | 2026-02-08 | Added local play-mode startup scripts and frontend interaction checklist for hands-on testing |
| 1.8 | 2026-02-08 | Added one-click frontend demo bootstrap workflow for seeded end-to-end interaction flow and expanded tests |
| 1.9 | 2026-02-08 | Added live API walkthrough script for local runtime verification across core backend endpoints |
| 2.0 | 2026-02-08 | Added frontend manual publish assistant checks and escalations panel aligned to linkedinAlgos guidance |
| 2.1 | 2026-02-08 | Added publishing queue filters and queue-state summaries in frontend with expanded tests |
| 2.3 | 2026-02-08 | Added persisted operator UI preferences (active view and queue filter) with reload-state tests |
| 2.4 | 2026-02-08 | Added Settings control to reset persisted UI preferences with coverage for reset behavior |
| 2.5 | 2026-02-08 | Restored algorithm alignment and audit trail visibility in Settings with coverage |
| 2.6 | 2026-02-08 | Added Settings audit filter controls and filtering test coverage |
| 2.7 | 2026-02-08 | Added dashboard operational alerts for kill switch, posting state, due posts, and escalations with test coverage |
| 2.8 | 2026-02-08 | Added play-mode E2E runner for critical dashboard/settings flows with sandbox-safe execution mode |
| 2.9 | 2026-02-08 | Added per-alert dashboard snooze controls with local persistence and expiry coverage |
| 3.0 | 2026-02-08 | Added alert snooze countdown visibility and clear-snoozes controls with expanded tests |
| 3.1 | 2026-02-08 | Added minute-level live countdown ticking for snoozed alerts with interval test coverage |
| 4.0 | 2026-02-08 | Finalised single-user operational release with full-state backup export and completion status |
| 4.1 | 2026-02-08 | Hardened local startup: alembic DB fallback, CORS enablement, and reduced preflight requests |
| 4.5 | 2026-02-09 | Added startup self-check for DB schema completeness and GET /health/db diagnostic endpoint with regression tests |
| 4.6 | 2026-02-09 | Frontend component decomposition: shared loading/error/empty states, OperationalAlerts extraction, and expanded test coverage |
| 4.7 | 2026-02-09 | Structured JSON logging, request ID tracing middleware, deploy profile separation, and aggregated /health/full endpoint |
| 4.8 | 2026-02-09 | Accessibility: skip-to-content link, ARIA landmarks, role attributes on shared components, focus indicators, and 7 new a11y tests |
| 4.9 | 2026-02-09 | JWT authentication module with user registration, login, logout, token refresh, and hybrid API-key/JWT auth support |
| 5.0 | 2026-02-09 | AI content generation engine with content pyramid, weighted format/tone selection, LLM client mock mode, and guardrail validation |
| 5.1 | 2026-02-09 | Enhanced Telegram approval workflow with inline keyboards, /preview and /help commands, callback query handlers, and short-ID draft lookup |
| 5.2 | 2026-02-09 | LinkedIn read integration with post metrics fetching, mock metrics support, engagement service polling, and metrics endpoint |
| 5.3 | 2026-02-09 | Comment handling with LLM-powered auto-replies, MEDIA_INQUIRY triage, Telegram escalation notifications, and resolution endpoints |
| 5.4 | 2026-02-09 | Railway deployment infrastructure: Backend/Frontend Dockerfiles, docker-compose.prod.yml, production env template, nginx SPA config, and deployment docs |
| 5.4.1 | 2026-02-10 | PostgreSQL migration fixes: sa.String + raw SQL enum strategy, lowercase enum values, nginx dynamic PORT for Railway |
| 5.5 | 2026-02-10 | Zapier webhook integration: webhook_service with retries, HMAC signing, post.publish_ready/draft.approved/post.published events, admin status/test endpoints, migration 0007, and 10 tests |

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

---

## 31. v1.4 Source and Report Action Coverage (2026-02-08)

### 31.1 v1.4 Scope

v1.4 extends frontend action workflow testing to source ingestion and report sending paths:

- source ingest action path
- daily report send action path

### 31.2 v1.4 Implementation Added

- Expanded frontend test suite in:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
- Added mock handlers and assertions for:
  - `POST /sources/ingest`
  - `POST /reports/daily/send`
- Added async stabilization in report send test by waiting for initial refresh completion before click.
- Frontend test suite now covers 7 behaviors:
  - render/load
  - generate
  - reject
  - approve
  - confirm publish
  - ingest
  - report send

### 31.3 v1.4 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`7/7`)
- frontend production build passed
- unified smoke run passed (backend tests + frontend tests + frontend build)

### 31.4 Remaining Constraints

- Action coverage remains mock-network component testing and does not yet include full browser/live-backend end-to-end coverage.

---

## 32. v1.5 Interactive Frontend Workflows (2026-02-08)

### 32.1 v1.5 Scope

v1.5 upgrades the operations console from action buttons to a richer interactive playground for core backend workflows:

- manual draft creation
- post metrics submission
- manual comment creation

### 32.2 v1.5 Implementation Added

- Frontend API client additions:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/services/api.js`
  - added:
    - `createDraft(payload)`
    - `createComment(payload)`
- Frontend UI additions:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`
  - added forms and actions for:
    - `POST /drafts` (manual draft)
    - `POST /posts/{id}/metrics` (metrics update)
    - `POST /comments` (comment creation)
  - improved publish panel with explicit URL input and metrics target selection
- Styling support:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/styles/app.css`
  - added form-grid and select styling for new controls
- Test coverage expansion:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - suite expanded to `10` tests, now asserting endpoint calls for:
    - create draft
    - update metrics
    - create comment

### 32.3 v1.5 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`10/10`)
- frontend production build passed
- unified smoke run passed (backend tests + frontend tests + frontend build)

### 32.4 Remaining Constraints

- Frontend now covers most daily operator actions, but some spec-level capabilities from `CLAUDE.md` remain backend-limited or not yet implemented end-to-end (e.g., WhatsApp/email operational channels and full external LinkedIn API write mode).

---

## 33. v1.6 Core Control Action Test Coverage (2026-02-08)

### 33.1 v1.6 Scope

v1.6 closes remaining high-frequency control action gaps in frontend automated testing:

- publish due trigger
- engagement poll trigger
- learning recompute trigger
- admin kill switch and posting toggles

### 33.2 v1.6 Implementation Added

- Expanded `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx` with endpoint assertions for:
  - `POST /posts/publish-due`
  - `POST /engagement/poll`
  - `POST /learning/recompute`
  - `POST /admin/kill-switch/on`
  - `POST /admin/kill-switch/off`
  - `POST /admin/posting/on`
  - `POST /admin/posting/off`
- Extended test mock handlers for those paths.
- Stabilized action tests by waiting for initial app refresh before clicking controls.

### 33.3 v1.6 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`17/17`)
- frontend production build passed
- unified smoke run passed (backend tests + frontend tests + frontend build)

### 33.4 Remaining Constraints

- Frontend test suite is now broad at component/action level but still not a substitute for full end-to-end browser tests against live services.

---

## 34. v1.7 Local Play Mode Enablement (2026-02-08)

### 34.1 v1.7 Scope

v1.7 adds a direct local run mode so the user can interact with the frontend immediately without manual process orchestration.

### 34.2 v1.7 Implementation Added

- Added startup scripts:
  - `/Users/sphiwemawhayi/Personal Brand/scripts/run_backend.sh`
  - `/Users/sphiwemawhayi/Personal Brand/scripts/run_frontend.sh`
  - `/Users/sphiwemawhayi/Personal Brand/scripts/run_play_mode.sh`
- `run_backend.sh`:
  - validates venv and env file
  - applies migrations
  - starts FastAPI on `127.0.0.1:8000`
- `run_frontend.sh`:
  - ensures deps and `.env`
  - starts Vite on `127.0.0.1:5173`
- `run_play_mode.sh`:
  - starts backend in background with log capture
  - performs health check
  - starts frontend and handles cleanup on exit
- Updated `/Users/sphiwemawhayi/Personal Brand/README.md` with a play checklist across major UI actions.

### 34.3 v1.7 Validation Status

Executed on 2026-02-08:

- `./scripts/v1_smoke.sh`

Result:

- backend tests passed (`18/18`)
- frontend tests passed (`17/17`)
- frontend build passed

### 34.4 Remaining Constraints

- Full spec parity still depends on backend/external-integration capabilities not yet implemented end-to-end (e.g., full WhatsApp/email operational channels and official LinkedIn write API mode).

---

## 35. v1.8 Demo Bootstrap Interaction Flow (2026-02-08)

### 35.1 v1.8 Scope

v1.8 introduces one-click demo bootstrap inside the frontend so users can populate and explore the product quickly.

### 35.2 v1.8 Implementation Added

- Frontend workflow enhancement:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`
  - added `bootstrapDemoData()` and `Playground` panel action `Bootstrap demo`
- Bootstrap sequence composes existing APIs:
  1. create manual draft
  2. approve draft
  3. confirm publish
  4. update metrics
  5. create comment
  6. ingest sources
  7. send daily report
- Frontend test expansion:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added bootstrap workflow test and mock behavior support
  - suite expanded to `18` tests

### 35.3 v1.8 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`18/18`)
- frontend production build passed
- unified smoke run passed (backend tests + frontend tests + frontend build)

### 35.4 Remaining Constraints

- Some spec-level capabilities remain dependent on backend/external integrations not yet implemented end-to-end (e.g., full WhatsApp/email channels and official LinkedIn write API mode).

---

## 36. v1.9 Live API Walkthrough Utility (2026-02-08)

### 36.1 v1.9 Scope

v1.9 adds a lightweight local runtime verification script to complement unit tests and frontend interaction checks.

### 36.2 v1.9 Implementation Added

- Added:
  - `/Users/sphiwemawhayi/Personal Brand/scripts/live_api_walkthrough.sh`
- Script capabilities:
  - checks core read endpoints (`/health`, `/health/readiness`, `/admin/config`, `/drafts`, `/posts`, `/engagement/status`, `/reports/daily`)
  - supports optional mutating checks via `RUN_MUTATING=1`
  - supports optional API key auth via `API_KEY` env variable
- Updated `/Users/sphiwemawhayi/Personal Brand/README.md` with usage examples.

### 36.3 v1.9 Validation Status

Executed on 2026-02-08:

- `./scripts/v1_smoke.sh`

Result:

- backend tests passed (`18/18`)
- frontend tests passed (`18/18`)
- frontend production build passed

### 36.4 Remaining Constraints

- Walkthrough script validates API responsiveness and basic flow execution but does not replace full integration/E2E orchestration.

---

## 37. v2.0 Frontend Manual Publish Alignment (2026-02-08)

### 37.1 v2.0 Scope

v2.0 improves operator guidance in the frontend so manual publishing and engagement handling stay aligned with `linkedinAlgos.md`:

- pre-publish quality checklist for draft body risks
- explicit visibility of escalated/high-value comments
- copy-ready manual publish handoff from UI

### 37.2 v2.0 Implementation Added

- Updated frontend console:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`
- New `Manual Publish Assistant` panel:
  - draft focus indicator
  - quality checks for:
    - hashtag count (warn if above 3)
    - external links in body (warn)
    - 300-word ceiling (warn)
    - topic consistency hint vs pillar/sub-theme
  - one-click `Copy draft body` helper for manual publish flow
  - golden-hour engagement reminder (60-90 minutes)
- New `Escalations` panel:
  - surfaced escalated comments count
  - high-value reason and commenter visibility for quick follow-up
- Expanded frontend tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - suite now covers checklist warnings, escalation rendering, and clipboard copy behavior

### 37.3 v2.0 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`21/21`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)

### 37.4 Remaining Constraints

- Checklist logic is advisory UI guidance and does not replace backend guardrails.
- Full LinkedIn live API publishing remains intentionally disabled in MVP compliant manual-first mode.

---

## 38. v2.1 Publishing Queue Filtered Operations (2026-02-08)

### 38.1 v2.1 Scope

v2.1 improves operational execution speed in the publishing workflow by adding queue-state visibility and filtering:

- queue summary counts for due/unpublished/published
- publish list filtering to prioritize urgent actions

### 38.2 v2.1 Implementation Added

- Updated frontend publishing logic in:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`
- New publishing queue features:
  - derived due-now state from `scheduled_time` and `published_at`
  - summary metrics: `Due now`, `Unpublished`, `Published`
  - queue filter selector:
    - `All`
    - `Due now`
    - `Unpublished`
    - `Published`
  - filtered publishing list rendering with due-now marker
- Expanded tests in:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added queue summary test
  - added queue filter behavior test

### 38.3 v2.1 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`23/23`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)

### 38.4 Remaining Constraints

- Due-now classification is UI-side guidance and may differ from backend timezone edge handling.
- Backend remains source of truth for execution and cadence enforcement.

---

## 39. v2.3 Persisted Operator Preferences (2026-02-08)

### 39.1 v2.3 Scope

v2.3 improves daily operator ergonomics by preserving common UI state across reloads:

- active sidebar view persistence
- publishing queue filter persistence

### 39.2 v2.3 Implementation Added

- Updated app shell:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`
  - reads/writes `app.activeView` via `localStorage` with safe fallback behavior
- Updated dashboard view:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/DashboardView.jsx`
  - reads/writes `app.dashboard.publishFilter` via `localStorage` with safe fallback behavior
- Updated sidebar release marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version label set to `v2.3`
- Expanded frontend tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added active-view restore test
  - added queue-filter restore test

### 39.3 v2.3 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`25/25`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)

### 39.4 Remaining Constraints

- Preferences are browser-local only and do not sync across devices/sessions.

---

## 40. v2.4 Preferences Reset Recovery Control (2026-02-08)

### 40.1 v2.4 Scope

v2.4 adds a direct recovery action for persisted UI state:

- reset persisted active view
- reset persisted publish queue filter

### 40.2 v2.4 Implementation Added

- Updated app shell:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`
  - added `handleResetUiPreferences()` to clear:
    - `app.activeView`
    - `app.dashboard.publishFilter`
  - reset action routes UI back to `dashboard`
- Updated settings view:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/SettingsView.jsx`
  - added `Reset UI Preferences` control in `System Controls`
- Updated sidebar marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version label set to `v2.4`
- Expanded tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added reset-preferences behavior test (storage keys + default view/filter)

### 40.3 v2.4 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`26/26`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)

### 40.4 Remaining Constraints

- Reset applies only to browser-local UI preferences and does not affect backend runtime state.

---

## 41. v2.5 Settings Operations Visibility (2026-02-08)

### 41.1 v2.5 Scope

v2.5 restores operations observability in the redesigned UI:

- algorithm alignment visibility
- recent audit trail visibility

### 41.2 v2.5 Implementation Added

- Updated settings view:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/SettingsView.jsx`
  - fetches and renders:
    - `GET /admin/algorithm-alignment`
    - `GET /admin/audit-logs`
  - limits displayed audit entries to recent records for readability
- Updated sidebar version marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - set to `v2.5`
- Expanded frontend tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - fixed mock override support for `auditLogs`
  - added visibility test for alignment/audit sections

### 41.3 v2.5 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`27/27`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)

### 41.4 Remaining Constraints

- Alignment/audit panels are read-only visibility views and rely on backend as source of truth.

---

## 42. v2.6 Settings Audit Filtering (2026-02-08)

### 42.1 v2.6 Scope

v2.6 improves Settings audit usability with quick client-side filtering:

- filter audit entries by action/actor/resource
- maintain compact, recent-entry audit panel

### 42.2 v2.6 Implementation Added

- Updated settings view:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/SettingsView.jsx`
  - added `Audit filter` input
  - added case-insensitive client-side matching across:
    - `action`
    - `actor`
    - `resource_type`
  - added empty-filter result message (`No entries match this filter.`)
- Updated sidebar marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version set to `v2.6`
- Expanded tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added audit filter behavior test

### 42.3 v2.6 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`28/28`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)

### 42.4 Remaining Constraints

- Filtering is local to the currently fetched audit subset and does not perform backend search/pagination.

---

## 43. v2.7 Dashboard Operational Alerts (2026-02-08)

### 43.1 v2.7 Scope

v2.7 improves dashboard operability by adding a dedicated operational alert surface:

- show high-priority conditions without navigating away from Dashboard
- summarize active alert count for rapid situational awareness

### 43.2 v2.7 Implementation Added

- Updated dashboard view:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/DashboardView.jsx`
  - loads `adminConfig` during dashboard refresh
  - computes alert list from:
    - kill switch enabled
    - posting disabled
    - due-now posts in queue
    - escalated comments requiring follow-up
  - renders `Operational Alerts` panel with severity styling and clear-state fallback
- Expanded tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added alert-positive and alert-clear tests
  - updated queue filter assertion for text ambiguity introduced by alert messaging
- Updated sidebar marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version set to `v2.7`

### 43.3 v2.7 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`30/30`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)

### 43.4 Remaining Constraints

- Alerts are derived from current dashboard payload and do not yet include historical trend context.

---

## 44. v2.8 Play-Mode E2E Runner (2026-02-08)

### 44.1 v2.8 Scope

v2.8 adds a single-command play-mode validation runner:

- boot local services and validate readiness
- execute critical Dashboard/Settings checks in one path
- support restricted environments where local port binding is unavailable

### 44.2 v2.8 Implementation Added

- Added runner script:
  - `/Users/sphiwemawhayi/Personal Brand/scripts/play_mode_e2e.sh`
  - performs health/readiness polling with timeout and cleanup traps
  - runs live API walkthrough when servers are enabled
  - runs targeted frontend flow tests covering Dashboard + Settings critical checks
  - supports `PLAY_E2E_SKIP_SERVERS=1` for sandbox/CI environments
  - bootstraps `Backend/.env` from `.env.example` when missing
  - sets fallback local SQLite `DATABASE_URL` when unset for deterministic startup
- Updated sidebar marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version set to `v2.8`
- Updated usage docs:
  - `/Users/sphiwemawhayi/Personal Brand/README.md`
  - added play-mode E2E command and restricted-environment invocation

### 44.3 v2.8 Validation Status

Executed on 2026-02-08:

- `PLAY_E2E_SKIP_SERVERS=1 ./scripts/play_mode_e2e.sh`
- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- play-mode E2E targeted checks passed (`4 passed`, `26 skipped`)
- frontend tests passed (`30/30`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)

### 44.4 Remaining Constraints

- Full server-start branch of the runner could not be executed in this sandbox because binding local ports is blocked (`operation not permitted`), but remains enabled for normal local runs.

---

## 45. v2.9 Alert Snooze Controls (2026-02-08)

### 45.1 v2.9 Scope

v2.9 adds temporary dashboard alert suppression controls:

- snooze individual operational alerts for 2 hours
- persist snooze state locally for operator continuity
- automatically restore alerts after snooze expiry

### 45.2 v2.9 Implementation Added

- Updated dashboard alerts:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/DashboardView.jsx`
  - added localStorage-backed alert snooze map (`app.dashboard.alertSnoozes`)
  - added `Snooze 2h` action per alert
  - active count and visible list now reflect only unsnoozed or expired alerts
- Updated shared button component:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/ui/Button.jsx`
  - forwards passthrough props (for accessibility labels and control hooks)
- Expanded tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added snooze action test
  - added snooze expiry restoration test
- Updated sidebar marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version set to `v2.9`

### 45.3 v2.9 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`
- `PLAY_E2E_SKIP_SERVERS=1 ./scripts/play_mode_e2e.sh`

Result:

- frontend tests passed (`32/32`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)
- play-mode E2E targeted checks passed (`4 passed`, `28 skipped`)

### 45.4 Remaining Constraints

- Snooze state is local to one browser profile and not shared across devices/operators.

---

## 46. v3.0 Alert Countdown and Clear Controls (2026-02-08)

### 46.1 v3.0 Scope

v3.0 improves snooze observability and recovery:

- show how many alerts are snoozed and their remaining snooze time
- provide one-click clearing of all alert snoozes

### 46.2 v3.0 Implementation Added

- Updated dashboard alerts:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/DashboardView.jsx`
  - added compact snoozed-alert summary row with per-alert remaining time
  - added `Clear Snoozes` control when snoozed alerts exist
  - added helper formatting for minute/hour countdown display
- Expanded tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added countdown summary visibility test
  - added clear-snoozes behavior and storage reset test
- Updated sidebar marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version set to `v3.0`

### 46.3 v3.0 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`
- `PLAY_E2E_SKIP_SERVERS=1 ./scripts/play_mode_e2e.sh`

Result:

- frontend tests passed (`33/33`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)
- play-mode E2E targeted checks passed (`4 passed`, `29 skipped`)

### 46.4 Remaining Constraints

- Countdown display updates on render/refresh rather than real-time ticking.

---

## 47. v3.1 Live Snooze Countdown Tick (2026-02-08)

### 47.1 v3.1 Scope

v3.1 upgrades snooze countdown behavior from static to live-updating:

- refresh countdown labels every minute automatically
- keep alert visibility and snoozed metadata in sync with current time

### 47.2 v3.1 Implementation Added

- Updated dashboard timer behavior:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/DashboardView.jsx`
  - added `nowMs` state and single 60-second interval tick with cleanup
  - switched snoozed/visible alert calculations to use `nowMs` (instead of one-off `Date.now()` calls)
  - added optional test override hook `window.__APP_ALERT_TICK_MS__` for deterministic interval testing
- Expanded tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - added interval-driven countdown update test (`2m` to `1m`)
  - adjusted expiry test to assert automatic reappearance via tick
- Updated sidebar marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version set to `v3.1`

### 47.3 v3.1 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`
- `PLAY_E2E_SKIP_SERVERS=1 ./scripts/play_mode_e2e.sh`

Result:

- frontend tests passed (`34/34`)
- frontend production build passed
- unified smoke run passed (`18` backend tests + frontend tests + frontend build)
- play-mode E2E targeted checks passed (`4 passed`, `30 skipped`)

### 47.4 Remaining Constraints

- Tick granularity remains minute-level by design; sub-minute countdown precision is intentionally not implemented.

---

## 48. v4.0 Single-User Completion Release (2026-02-08)

### 48.1 v4.0 Scope

v4.0 marks completion of the single-user operational tool scope:

- all daily operational flows are runnable from the UI
- single-command validation workflows are in place
- full operational state backup export is available

### 48.2 v4.0 Implementation Added

- Added backup/export endpoint:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/routes/admin.py`
  - `GET /admin/export-state` returns full single-user operational snapshot:
    - config
    - drafts/posts/comments/sources
    - audit logs and learning weights
    - engagement metrics and notifications
  - switched export timestamp generation to timezone-aware UTC datetime
- Added backup export control in settings:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/SettingsView.jsx`
  - `Export Backup` downloads formatted JSON snapshot
- Added API client support:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/services/api.js`
  - `api.exportState()`
- Expanded tests:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v10_state_export.py`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - includes frontend export action call-path + download behavior coverage
- Updated sidebar marker:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - version set to `v4.0`

### 48.3 v4.0 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`
- `PLAY_E2E_SKIP_SERVERS=1 ./scripts/play_mode_e2e.sh`

Result:

- frontend tests passed (`35/35`)
- frontend production build passed
- backend tests passed (`19/19`)
- unified smoke run passed (backend + frontend + build)
- play-mode E2E targeted checks passed (`4 passed`, `31 skipped`)

### 48.4 Remaining Constraints

- Completion status applies to single-user operational scope; multi-user collaboration and official LinkedIn write automation remain intentionally out of scope.

---

## 49. v4.1 Local Startup Hardening (2026-02-08)

### 49.1 v4.1 Scope

v4.1 addresses reported local startup friction:

- prevent migration failure when `DATABASE_URL` is missing
- allow browser preflight/CORS for local frontend usage
- reduce unnecessary preflight traffic from frontend API calls

### 49.2 v4.1 Implementation Added

- Alembic fallback URL:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/alembic/env.py`
  - if `DATABASE_URL` is unset, use local SQLite fallback (`Backend/local_dev.db`)
- CORS middleware in backend app:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/main.py`
  - local allowed origins from config
- Config support for CORS origins:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/config.py`
  - added `cors_allowed_origins` with localhost defaults
  - `/Users/sphiwemawhayi/Personal Brand/Backend/.env.example`
  - added `CORS_ALLOWED_ORIGINS` example value
- Frontend request header hardening:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/services/api.js`
  - sets `Content-Type: application/json` only when request body exists
  - avoids triggering browser preflight for simple GET requests
- Setup guidance update:
  - `/Users/sphiwemawhayi/Personal Brand/README.md`
  - documented SQLite fallback `DATABASE_URL` for local non-Postgres setup

### 49.3 v4.1 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- frontend tests passed (`35/35`)
- frontend production build passed
- backend tests passed (`19/19`)
- unified smoke run passed (backend + frontend + build)

### 49.4 Remaining Constraints

- If a user already has an outdated local `.env` missing `DATABASE_URL`, they should either set SQLite fallback there or recreate from `.env.example` for predictable behavior.

---

## 50. v4.2 Runtime DB Fallback and Local CORS Stabilization (2026-02-08)

### 50.1 v4.2 Scope

v4.2 resolves local runtime failures when `.env` points to unavailable PostgreSQL and broadens local browser compatibility:

- runtime DB fallback in dev if PostgreSQL target is unreachable
- migration fallback in dev if configured PostgreSQL target cannot be opened
- SQLite-first default in backend `.env.example`
- local CORS handling for localhost/127.0.0.1 on arbitrary dev ports

### 50.2 v4.2 Implementation Added

- Runtime DB fallback:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/db.py`
  - if `APP_ENV=dev` and configured non-SQLite DB connection fails at startup, backend falls back to `sqlite+pysqlite:///./local_dev.db`
- Settings default for DB URL:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/config.py`
  - `database_url` default set to `sqlite+pysqlite:///./local_dev.db`
- Migration fallback hardening:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/alembic/env.py`
  - in dev, if configured online migration connection fails, falls back to local SQLite migration target
- Local CORS stabilization:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/main.py`
  - allows localhost/127.0.0.1 origins across dev ports via `allow_origin_regex`
- Backend env defaults:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/.env.example`
  - default `DATABASE_URL` switched to local SQLite
- Version/docs updates:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx` set to `v4.2`
  - `/Users/sphiwemawhayi/Personal Brand/README.md` updated local setup note

### 50.3 v4.2 Validation Status

Executed on 2026-02-08:

- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`
- `cd Backend && env -u DATABASE_URL ./.venv/bin/alembic upgrade head`

Result:

- frontend tests passed (`35/35`)
- frontend production build passed
- backend tests passed (`19/19`)
- unified smoke run passed (backend + frontend + build)
- alembic online migration fallback path works in local mode

### 50.4 Remaining Constraints

- Existing local `.env` files that hard-code Postgres may still require explicit update to SQLite if users prefer deterministic non-fallback behavior.

---

## 51. v4.3 Engagement Status Timezone Hotfix (2026-02-08)

### 51.1 v4.3 Scope

v4.3 fixes a runtime regression on local SQLite operation:

- `/engagement/status` no longer fails on naive/aware datetime comparisons
- adds regression coverage for engagement status endpoint in monitored-post flow

### 51.2 v4.3 Implementation Added

- Engagement status comparison normalization:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/routes/engagement.py`
  - route now normalizes `comment_monitoring_until` via UTC conversion before comparing against current UTC time
- Regression test:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v04_monitoring_and_polling.py`
  - adds endpoint-level check that `/engagement/status` returns `200` and expected shape after publish confirmation flow
- Version/docs updates:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx` set to `v4.3`
  - `/Users/sphiwemawhayi/Personal Brand/README.md` updated version status

### 51.3 v4.3 Validation Status

Executed on 2026-02-08:

- `cd Backend && ./.venv/bin/python -m unittest -v tests/test_v04_monitoring_and_polling.py`
- `./scripts/v1_smoke.sh`

Result:

- v0.4 monitoring/polling test suite passed (including new timezone regression test)
- backend tests passed (`20/20`)
- frontend tests passed (`35/35`)
- frontend production build passed
- unified smoke run passed (backend + frontend + build)

### 51.4 Remaining Constraints

- Existing data written with mixed timezone representations in other routes may still warrant a broader normalization sweep if similar comparisons are added elsewhere.

---

## 52. v4.4 Deterministic SQLite Path Resolution (2026-02-08)

### 52.1 v4.4 Scope

v4.4 removes local SQLite path ambiguity that caused migrated schema and runtime queries to target different DB files:

- deterministic normalization of relative SQLite URLs to backend-root absolute paths
- shared normalization behavior between runtime engine initialization and Alembic migration URL resolution

### 52.2 v4.4 Implementation Added

- Added DB URL normalization utility:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/db_url.py`
  - normalizes `sqlite+pysqlite:///./...` and `sqlite:///./...` to backend-root absolute file URLs
  - provides canonical local DB URL helper for fallback paths
- Runtime engine URL normalization:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/db.py`
  - normalizes configured SQLite URLs before engine creation
  - local fallback now uses canonical backend-root absolute SQLite URL
- Settings default alignment:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/config.py`
  - default `database_url` sourced from canonical local DB URL helper
- Alembic URL normalization:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/alembic/env.py`
  - applies same normalization for configured URLs and fallback target
- Regression coverage:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v11_sqlite_url_resolution.py`
  - validates relative SQLite URL normalization and no-op behavior for already-absolute URLs
- Version/docs updates:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx` set to `v4.4`
  - `/Users/sphiwemawhayi/Personal Brand/README.md` updated version and local DB note

### 52.3 v4.4 Validation Status

Executed on 2026-02-08:

- `cd Backend && ./.venv/bin/python -m unittest -v tests/test_v11_sqlite_url_resolution.py tests/test_v04_monitoring_and_polling.py`
- `./scripts/v1_smoke.sh`
- `cd Backend && ./.venv/bin/python - <<'PY' ... print(engine.url) ... PY`
- `cd Backend && ./.venv/bin/alembic upgrade head`
- `cd Backend && ./.venv/bin/python - <<'PY' ... TestClient GET /health,/posts,/comments,/engagement/status ... PY`

Result:

- sqlite URL normalization regression tests passed
- v0.4 monitoring tests passed
- backend tests passed (`22/22`)
- frontend tests passed (`35/35`)
- frontend production build passed
- unified smoke run passed
- runtime and alembic confirmed to use `/Users/sphiwemawhayi/Personal Brand/Backend/local_dev.db`
- key endpoints return `200` after migration (`/health`, `/posts`, `/comments`, `/engagement/status`)

### 52.4 Remaining Constraints

- Existing local SQLite files created in other directories are not auto-migrated or merged; run migrations against the canonical backend DB path after pulling this change.

---

## 53. End-of-Day Handover (2026-02-08)

### 53.1 Handover Artifact

- Created handover package for next-agent continuity:
  - `/Users/sphiwemawhayi/Personal Brand/HANDOVER.md`

### 53.2 Handover Coverage

- Includes:
  - completed build summary through `v4.4`
  - outstanding work and known scope gaps
  - first-30-min takeover checklist
  - troubleshooting for recurring local backend issues

---

## 54. v4.5 Startup Self-Check and DB Diagnostic Endpoint (2026-02-09)

### 54.1 v4.5 Scope

v4.5 adds startup reliability and DB state observability:

- startup self-check validates required tables exist on app init
- clear human-readable error logging when schema is incomplete
- `GET /health/db` diagnostic endpoint with redacted DB URL, migration head, and table existence map
- regression tests for healthy, empty, and partial DB scenarios

### 54.2 v4.5 Implementation Added

- New service:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/services/db_check.py`
  - `check_schema(engine)` inspects table existence
  - `startup_schema_check(engine)` raises `SchemaError` on missing tables
  - `REQUIRED_TABLES` frozen set of 9 expected tables
- Startup integration:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/main.py`
  - calls `startup_schema_check` on init (skipped when `auto_create_tables` is True)
  - logs warning and continues if check fails (avoids hard crash for dev flexibility)
- New diagnostic endpoint:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/routes/health.py`
  - `GET /health/db` returns:
    - `database_url` (credentials redacted)
    - `migration.current_head` (alembic version)
    - `schema.ok`, `schema.tables` (per-table existence), `schema.missing`
- New regression tests:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v12_startup_check.py`
  - 9 tests covering healthy DB, empty DB, partial DB, SchemaError raise, and endpoint structure

### 54.3 v4.5 Validation Status

Executed on 2026-02-09:

- `cd Backend && ./.venv/bin/python -m pytest tests/ -v`
- `./scripts/v1_smoke.sh`

Result:

- backend tests passed (`31/31`)
- frontend tests passed (`35/35`)
- frontend production build passed
- unified smoke run passed

### 54.4 Remaining Constraints

- Startup check logs a warning but does not hard-crash the app; this allows dev workflows where tables are created lazily.
- `GET /health/db` does not require authentication; consider adding read auth for production exposure.

---

## 55. v4.6 Frontend Component Decomposition and UX Resilience (2026-02-09)

### 55.1 v4.6 Scope

v4.6 improves frontend maintainability and user experience by decomposing views and adding consistent loading, error, and empty state handling:

- extract shared UI components for loading, error, and empty states
- extract OperationalAlerts from DashboardView into shared component
- add loading spinner on initial view mount for all four views
- add error state with retry for all four views when API fails
- add empty state messaging for key data-dependent sections
- expand frontend test suite with loading/error/empty coverage

### 55.2 v4.6 Implementation Added

- New shared components:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/shared/LoadingSpinner.jsx`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/shared/ErrorMessage.jsx`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/shared/EmptyState.jsx`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/shared/OperationalAlerts.jsx`
- View updates (all four):
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/DashboardView.jsx`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/ContentView.jsx`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/EngagementView.jsx`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/SettingsView.jsx`
  - each view now has `initialLoading` and `fetchError` state
  - `refreshData()` wrapped in try/catch with `setFetchError`
  - initial `useEffect` changed from `withAction()` to direct async IIFE
  - early returns for `LoadingSpinner` and `ErrorMessage` before main JSX
  - empty state messaging for pending drafts, comments, and posts
- Expanded frontend tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - 9 new tests covering:
    - dashboard loading spinner, error state, empty posts state
    - content loading spinner, error state, empty pending drafts
    - engagement loading spinner, empty comments
    - settings loading spinner
- Version marker updated:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx` set to `v4.6`

### 55.3 v4.6 Validation Status

Executed on 2026-02-09:

- `cd Backend && ./.venv/bin/python -m pytest tests/ -v`
- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- backend tests passed (`31/31`)
- frontend tests passed (`44/44`)
- frontend production build passed
- unified smoke run passed

### 55.4 Remaining Constraints

- Shared components use inline styles consistent with the existing codebase pattern.
- Error retry resets `initialLoading` and re-fetches; no exponential backoff on client side.

---

## 56. v4.7 Operational Maturity: Logging, Tracing, and Deploy Profiles (2026-02-09)

### 56.1 v4.7 Scope

v4.7 adds production-grade observability and environment-aware defaults:

- structured JSON log formatter for machine-parseable output
- request ID middleware for end-to-end request tracing
- deploy profile separation via `app_env`, `log_level`, and `log_json` config
- aggregated `GET /health/full` endpoint combining all sub-checks
- regression tests covering formatter, middleware, endpoint, and config defaults

### 56.2 v4.7 Implementation Added

- New logging module:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/logging_config.py`
  - `JSONFormatter` outputs structured JSON with timestamp, level, logger, message, optional exception and request_id
  - `configure_logging()` sets root logger format based on `json_format` flag
- New middleware:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/middleware/request_id.py`
  - `RequestIdMiddleware` generates or propagates `x-request-id` header via `contextvars`
  - `get_request_id()` accessor for use in routes and log records
- Config updates:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/config.py`
  - added `log_level: str = "INFO"` and `log_json: bool = False`
- App wiring:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/main.py`
  - calls `configure_logging()` at import time with JSON auto-enabled for `app_env=prod`
  - adds `RequestIdMiddleware` before CORS middleware
  - logs startup info (env, log level, DB URL with credentials stripped)
- New endpoint:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/routes/health.py`
  - `GET /health/full` aggregates heartbeat, database, redis, schema, and migration checks
  - includes `app_env` and `request_id` in response
- New tests:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v13_ops_maturity.py`
  - 14 tests: JSONFormatter (3), RequestIdMiddleware (3), HealthFullEndpoint (5), DeployProfile (3)

### 56.3 v4.7 Validation Status

Executed on 2026-02-09:

- `cd Backend && ./.venv/bin/python -m pytest tests/ -v`
- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- backend tests passed (`45/45`)
- frontend tests passed (`44/44`)
- frontend production build passed
- unified smoke run passed

### 56.4 Remaining Constraints

- JSON logging auto-enables only when `app_env=prod`; local dev uses human-readable format by default.
- Request ID middleware uses `BaseHTTPMiddleware` which has known limitations with streaming responses in Starlette; acceptable for current endpoint patterns.
- `GET /health/full` reports `degraded` when Redis is unreachable, which is expected in minimal local setups.

---

## 57. v4.8 Accessibility and Keyboard Navigation (2026-02-09)

### 57.1 v4.8 Scope

v4.8 improves frontend accessibility for assistive technology and keyboard-only users:

- skip-to-content link for keyboard navigation
- ARIA landmarks and labels on navigation and main content
- aria-current on active sidebar navigation item
- role="alert" on error messages and operational alerts
- role="status" and aria-busy on loading spinner
- role="progressbar" with aria-value attributes on progress bars
- visible focus indicators on all interactive elements
- 7 new frontend accessibility tests

### 57.2 v4.8 Implementation Added

- App shell updates:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/App.jsx`
  - added visually-hidden skip-to-content link (visible on focus)
  - added `id="main-content"` and `aria-label` on `<main>` reflecting active view
- Sidebar updates:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/layout/Sidebar.jsx`
  - added `aria-label="Main navigation"` on `<nav>`
  - added `aria-current="page"` on active nav button
  - added focus ring styling (box-shadow) on nav buttons
  - added `role="status"` and `aria-label` on system status indicator
  - added `aria-hidden="true"` on decorative status dot
- Shared component updates:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/shared/ErrorMessage.jsx` — added `role="alert"`
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/shared/LoadingSpinner.jsx` — added `role="status"`, `aria-busy="true"`, `aria-hidden="true"` on decorative spinner
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/shared/OperationalAlerts.jsx` — added `role="alert"` on visible alert items
- UI component updates:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/ui/Button.jsx` — added visible focus ring via onFocus/onBlur box-shadow
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/ui/ProgressBar.jsx` — added `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, optional `label` prop
- Expanded frontend tests:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.test.jsx`
  - 7 new tests: skip-to-content link, aria-current on active nav, nav aria-label, main aria-label, spinner role/aria-busy, error role=alert, operational alert role=alert

### 57.3 v4.8 Validation Status

Executed on 2026-02-09:

- `cd Backend && ./.venv/bin/python -m pytest tests/ -v`
- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- `./scripts/v1_smoke.sh`

Result:

- backend tests passed (`45/45`)
- frontend tests passed (`51/51`)
- frontend production build passed
- unified smoke run passed

### 57.4 Remaining Constraints

- Form label-to-input associations (htmlFor/id) remain to be addressed in a future pass across all views.
- Semantic list restructuring for comments/drafts/posts deferred to avoid layout-sensitive changes.
- Heading hierarchy (h1/h2/h3) across views could be rationalized in a future pass.

---

## 58. v5.4 Railway Deployment Infrastructure (2026-02-09)

### 58.1 v5.4 Scope

v5.4 adds full production deployment infrastructure targeting Railway as the primary platform:

- Backend Dockerfile with multi-service support (API, worker, beat via `SERVICE` env var)
- Frontend Dockerfile with Node build stage and nginx SPA serving
- Production docker-compose with health checks and dependency ordering
- Production environment template with all secrets documented
- Railway platform configuration
- Comprehensive deployment documentation in README

### 58.2 v5.4 Implementation Added

- Backend Docker infrastructure:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/Dockerfile` — multi-stage Python 3.12 build
  - `/Users/sphiwemawhayi/Personal Brand/Backend/docker-entrypoint.sh` — runs migrations then starts SERVICE (api/worker/beat)
- Frontend Docker infrastructure:
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/Dockerfile` — Node 20 build + nginx alpine serve
  - `/Users/sphiwemawhayi/Personal Brand/Frontend/nginx.conf` — SPA routing, gzip, security headers, asset caching
- Production orchestration:
  - `/Users/sphiwemawhayi/Personal Brand/docker-compose.prod.yml` — full stack (Postgres 16 + Redis 7 + 3 backend services + frontend)
  - `/Users/sphiwemawhayi/Personal Brand/.env.production.template` — all production env vars with defaults and docs
  - `/Users/sphiwemawhayi/Personal Brand/railway.toml` — Railway platform configuration
- Documentation and hygiene:
  - `/Users/sphiwemawhayi/Personal Brand/README.md` — full Railway and Docker Compose deployment guides
  - `/Users/sphiwemawhayi/Personal Brand/.gitignore` — production secrets, local DB, Docker volumes

### 58.3 v5.4 Validation Status

Executed on 2026-02-09:

- `cd Backend && ./.venv/bin/python -m pytest tests/ -v`
- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`

Result:

- backend tests passed (`160/160`)
- frontend tests passed (`51/51`)
- frontend production build passed
- Docker not available locally for image build validation; Dockerfiles follow standard patterns and will be validated on first Railway deploy

### 58.4 Remaining Constraints

- Docker images have not been built locally (Docker not installed in this environment); first build will occur on Railway.
- Custom domain and HTTPS certificate setup is done in the Railway dashboard, not automated.
- Telegram bot webhook mode is not configured; uses polling.
- Railway free tier may not support 4 services; Pro plan ($20/mo) recommended.

---

## 59. v5.4.1 Railway Production Deployment and PostgreSQL Fixes (2026-02-10)

### 59.1 v5.4.1 Scope

First production deploy to Railway revealed three critical issues requiring immediate fixes:

- PostgreSQL enum type creation conflict in Alembic migration
- SQLAlchemy enum name/value case mismatch
- Frontend nginx hardcoded PORT incompatible with Railway dynamic PORT injection

### 59.2 v5.4.1 Implementation

- Rewrote `Backend/alembic/versions/0001_initial.py`:
  - Use `sa.String(length=20)` for all enum columns in `create_table`
  - After table creation, raw SQL `CREATE TYPE` for PostgreSQL native enum types
  - Raw SQL `ALTER TABLE ALTER COLUMN ... TYPE ... USING` to convert String columns to native enums
  - PostgreSQL enum values use lowercase to match SQLAlchemy enum name persistence
  - SQLite path unchanged (no enum type conversion needed)
- Created `Frontend/nginx.conf.template` with `${PORT}` variable
- Updated `Frontend/Dockerfile` to use `envsubst` for dynamic PORT at runtime

### 59.3 v5.4.1 Validation Status

Executed on 2026-02-10:

- All 4 Railway services deployed and healthy
- `curl /health` returns `{"status":"ok"}`
- `curl /health/db` confirms all 11 tables present, migration at `0007_webhook_config`
- User registration and login verified on production
- Draft generation with live Claude API verified

### 59.4 Key Lessons

- SQLAlchemy `sa.Enum` in `create_table` always fires `_on_table_create` event. `create_type=False` does NOT prevent this.
- SQLAlchemy persists Python enum `.name` (lowercase) not `.value` (uppercase) by default.
- Railway monorepo deploys require `railway up --path-as-root Backend/` — GitHub auto-builds fail.

---

## 60. v5.5 Zapier Webhook Integration (2026-02-10)

### 60.1 v5.5 Scope

v5.5 adds Zapier webhook integration for automated LinkedIn posting:

- Webhook service with retry logic and HMAC signing
- Integration at three workflow events
- Admin endpoints for webhook status and testing
- Config, migration, and test coverage

### 60.2 v5.5 Implementation Added

- New service:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/services/webhook_service.py`
  - `send_webhook()` fires HTTP POST to Zapier with 3 retries and exponential backoff (1s, 2s, 4s)
  - `send_test_webhook()` for connectivity verification
  - HMAC-SHA256 signing via `X-Webhook-Signature` header when secret is configured
  - All deliveries logged to `notification_logs` (channel="webhook")
- Config additions:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/config.py`
  - `zapier_webhook_url: str | None = None`
  - `zapier_webhook_secret: str | None = None`
- Model additions:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/models.py`
  - `AppConfig.zapier_webhook_url` and `AppConfig.zapier_webhook_secret`
- Migration:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/alembic/versions/0007_webhook_config.py`
- Workflow integration:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/services/workflow.py`
  - `publish_due_manual_posts()` fires `post.publish_ready` event (PRIMARY integration point)
- Route integration:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/routes/drafts.py` — fires `draft.approved` on draft approval
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/routes/posts.py` — fires `post.published` on manual publish confirmation
- Admin endpoints:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/app/routes/admin.py`
  - `GET /admin/webhook-status` — config status and 24h delivery stats
  - `POST /admin/webhook-test` — send test payload to verify connectivity
- Tests:
  - `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_webhook.py`
  - 10 tests covering payload format, retries, logging, HMAC, admin endpoints, and integration

### 60.3 Webhook Event Payloads

All events use this envelope:
```json
{
  "event": "post.publish_ready",
  "timestamp": "2026-02-10T10:30:00+00:00",
  "data": {
    "post_id": "uuid",
    "content": "Full post text for LinkedIn",
    "format": "TEXT",
    "pillar_theme": "Adtech fundamentals",
    "sub_theme": "Programmatic buying"
  }
}
```

Events fired:
- `post.publish_ready` — when scheduled post is due (primary: Zapier maps `data.content` to LinkedIn post body)
- `draft.approved` — when a draft is approved and scheduled
- `post.published` — when manual publish is confirmed with LinkedIn URL

### 60.4 v5.5 Validation Status

Executed on 2026-02-10:

- `cd Backend && ./.venv/bin/python -m pytest tests/ -v`
- `cd Frontend && npm test -- --run`
- `cd Frontend && npm run build`
- Railway deploy: all 3 backend services updated
- `curl /admin/webhook-status` returns expected structure
- `curl -X POST /admin/webhook-test` returns `{"success":false,"error":"No webhook URL configured"}`
- `curl /health/db` confirms migration at `0007_webhook_config`

Result:

- backend tests passed (`170/170`)
- frontend tests passed (`51/51`)
- frontend production build passed
- production deployment verified

### 60.5 Remaining Constraints

- `ZAPIER_WEBHOOK_URL` not yet set on Railway (user needs to create Zapier account first)
- No acknowledgment mechanism to confirm LinkedIn post was published by Zapier
- Webhook delivery uses `time.sleep()` for retry backoff, blocking the request thread (acceptable for single-user)
