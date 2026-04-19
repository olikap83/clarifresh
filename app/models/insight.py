import uuid
from datetime import date, datetime

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    platform: Mapped[str | None] = mapped_column(String(20), nullable=True)
    competitor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    top_post_ids: Mapped[list[str] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    flop_post_ids: Mapped[list[str] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    recommendations: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    model_used: Mapped[str] = mapped_column(String(100), nullable=False, default="claude-sonnet-4-6")
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
