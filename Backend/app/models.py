import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class DraftStatus(str, enum.Enum):
    pending = "PENDING"
    approved = "APPROVED"
    rejected = "REJECTED"
    expired = "EXPIRED"


class PostFormat(str, enum.Enum):
    text = "TEXT"
    image = "IMAGE"
    carousel = "CAROUSEL"


class PostTone(str, enum.Enum):
    educational = "EDUCATIONAL"
    opinionated = "OPINIONATED"
    direct = "DIRECT"
    exploratory = "EXPLORATORY"


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    pillar_theme: Mapped[str] = mapped_column(String(120))
    sub_theme: Mapped[str] = mapped_column(String(120))
    format: Mapped[PostFormat] = mapped_column(Enum(PostFormat))
    tone: Mapped[PostTone] = mapped_column(Enum(PostTone))
    content_body: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    carousel_document_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[DraftStatus] = mapped_column(Enum(DraftStatus), default=DraftStatus.pending)
    approval_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    guardrail_check_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    guardrail_violations: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_citations: Mapped[str | None] = mapped_column(Text, nullable=True)

    published_post: Mapped["PublishedPost"] = relationship(back_populates="draft", uselist=False)


class PublishedPost(Base):
    __tablename__ = "published_posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("drafts.id"))
    linkedin_post_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    linkedin_post_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_publish_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manual_publish_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment_monitoring_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment_monitoring_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_comment_poll_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_body: Mapped[str] = mapped_column(Text)
    format: Mapped[PostFormat] = mapped_column(Enum(PostFormat))
    tone: Mapped[PostTone] = mapped_column(Enum(PostTone))
    impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reactions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_metrics_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    draft: Mapped[Draft] = relationship(back_populates="published_post")
    comments: Mapped[list["Comment"]] = relationship(back_populates="published_post")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    published_post_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("published_posts.id"))
    linkedin_comment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    commenter_name: Mapped[str] = mapped_column(String(120))
    commenter_profile_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    commenter_follower_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment_text: Mapped[str] = mapped_column(Text)
    commented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_high_value: Mapped[bool] = mapped_column(Boolean, default=False)
    high_value_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    auto_reply_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_reply_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_reply_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manual_reply_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_reply_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    published_post: Mapped[PublishedPost] = relationship(back_populates="comments")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    channel: Mapped[str] = mapped_column(String(32))
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class AppConfig(Base):
    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    posting_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    comment_replies_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    kill_switch: Mapped[bool] = mapped_column(Boolean, default=False)


class SourceMaterial(Base):
    __tablename__ = "source_materials"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    source_name: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(1024), unique=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    pillar_theme: Mapped[str | None] = mapped_column(String(120), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128))
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class EngagementMetric(Base):
    __tablename__ = "engagement_metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    published_post_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("published_posts.id"))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reactions: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)


class LearningWeight(Base):
    __tablename__ = "learning_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    format_weights_json: Mapped[str] = mapped_column(Text)
    tone_weights_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
