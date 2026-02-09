import uuid
from datetime import datetime
from pydantic import BaseModel

from .models import DraftStatus, PostFormat, PostTone


class DraftCreate(BaseModel):
    pillar_theme: str
    sub_theme: str
    format: PostFormat
    tone: PostTone
    content_body: str
    image_url: str | None = None
    carousel_document_url: str | None = None


class DraftRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    pillar_theme: str
    sub_theme: str
    format: PostFormat
    tone: PostTone
    content_body: str
    image_url: str | None
    carousel_document_url: str | None
    status: DraftStatus
    rejection_reason: str | None
    guardrail_check_passed: bool
    guardrail_violations: str | None
    source_citations: str | None

    class Config:
        from_attributes = True


class DraftApprove(BaseModel):
    scheduled_time: datetime | None = None


class DraftReject(BaseModel):
    reason: str


class PublishedPostRead(BaseModel):
    id: uuid.UUID
    draft_id: uuid.UUID
    linkedin_post_url: str | None
    scheduled_time: datetime | None
    published_at: datetime | None
    actual_publish_time: datetime | None
    manual_publish_notified_at: datetime | None
    comment_monitoring_started_at: datetime | None
    comment_monitoring_until: datetime | None
    last_comment_poll_at: datetime | None

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    published_post_id: uuid.UUID
    commenter_name: str
    comment_text: str
    commenter_follower_count: int | None = None
    commenter_profile_url: str | None = None


class CommentRead(BaseModel):
    id: uuid.UUID
    published_post_id: uuid.UUID
    commenter_name: str
    comment_text: str
    commented_at: datetime
    is_high_value: bool
    high_value_reason: str | None
    escalated: bool
    auto_reply_sent: bool
    auto_reply_text: str | None

    class Config:
        from_attributes = True


class ManualPublishConfirm(BaseModel):
    linkedin_post_url: str


class SourceMaterialRead(BaseModel):
    id: uuid.UUID
    source_name: str
    title: str
    url: str
    published_at: datetime | None
    summary_text: str | None
    relevance_score: float
    pillar_theme: str | None

    class Config:
        from_attributes = True


class SourceIngestRequest(BaseModel):
    feed_urls: list[str] = []
    max_items_per_feed: int = 10


class AuditLogRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    actor: str
    action: str
    resource_type: str
    resource_id: str | None
    detail_json: str | None

    class Config:
        from_attributes = True


class PostMetricsUpdate(BaseModel):
    impressions: int
    reactions: int
    comments_count: int
    shares: int


class LearningWeightsRead(BaseModel):
    format_weights_json: str
    tone_weights_json: str
    updated_at: datetime


# Authentication schemas

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: str | None = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email_or_username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


# Content Engine schemas

class ContentGenerateRequest(BaseModel):
    """Request to generate a new draft via content engine."""

    research_context: str | None = None
    pillar_override: str | None = None
    sub_theme_override: str | None = None
    format_override: PostFormat | None = None
    tone_override: PostTone | None = None


class ContentGenerateResponse(BaseModel):
    """Response from content generation."""

    success: bool
    draft: DraftRead | None
    attempts: int
    requires_manual: bool
    error_message: str | None
    guardrail_violations: list[str] | None


class PostAngleRead(BaseModel):
    """Post angle representation."""

    id: str
    name: str
    description: str


class SubThemeCoverage(BaseModel):
    """Coverage stats for a sub-theme."""

    pillar_theme: str
    sub_theme: str
    post_count_30_days: int
    last_posted_at: datetime | None


class ContentPyramidRead(BaseModel):
    """Full content pyramid structure with coverage stats."""

    pillars: list[str]
    sub_themes: dict[str, list[str]]
    post_angles: list[PostAngleRead]
    coverage: list[SubThemeCoverage]


class ContentWeightsRead(BaseModel):
    """Current format and tone weights."""

    format_weights: dict[str, float]
    tone_weights: dict[str, float]
