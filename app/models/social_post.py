import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SocialPost(Base):
    __tablename__ = "social_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    platform_post_id: Mapped[str] = mapped_column(String(255), nullable=False)
    post_type: Mapped[str] = mapped_column(String(20), nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="posts")  # noqa: F821
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="post", cascade="all, delete-orphan")  # noqa: F821
    metrics: Mapped[list["PostMetrics"]] = relationship("PostMetrics", back_populates="post", cascade="all, delete-orphan")  # noqa: F821
    sentiment_results: Mapped[list["SentimentResult"]] = relationship("SentimentResult", back_populates="post", cascade="all, delete-orphan")  # noqa: F821
