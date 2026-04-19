import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    social_post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    overall_sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    positive_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    negative_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    neutral_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    comment_count_analyzed: Mapped[int] = mapped_column(Integer, nullable=False)
    key_themes: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    sentiment_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_claude_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False, default="claude-sonnet-4-6")
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    post: Mapped["SocialPost"] = relationship("SocialPost", back_populates="sentiment_results")  # noqa: F821
