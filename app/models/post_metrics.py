import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PostMetrics(Base):
    __tablename__ = "post_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    social_post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    views_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    likes_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    comments_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    shares_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    saves_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    engagement_rate: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    rank_score: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)

    post: Mapped["SocialPost"] = relationship("SocialPost", back_populates="metrics")  # noqa: F821
