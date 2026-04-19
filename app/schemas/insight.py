import uuid
from datetime import date, datetime

from pydantic import BaseModel


class InsightGenerateRequest(BaseModel):
    period_start: date
    period_end: date
    competitor_id: uuid.UUID | None = None
    platform: str | None = None
    insight_type: str = "weekly_summary"


class InsightOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    period_start: date
    period_end: date
    platform: str | None
    competitor_id: uuid.UUID | None
    competitor_name: str | None = None
    insight_type: str
    title: str
    body: str
    top_post_ids: list[uuid.UUID] | None
    flop_post_ids: list[uuid.UUID] | None
    recommendations: list[str] | None
    generated_at: datetime
    model_used: str


class InsightListOut(BaseModel):
    items: list[InsightOut]
    total: int
    page: int
    page_size: int
