import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PostMetricsSummary(BaseModel):
    views_count: int
    likes_count: int
    comments_count: int
    shares_count: int | None
    saves_count: int | None
    engagement_rate: Decimal | None
    rank_score: Decimal | None


class SocialPostOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    competitor_id: uuid.UUID
    competitor_name: str | None = None
    platform: str
    platform_post_id: str
    post_type: str
    caption: str | None
    hashtags: list[str] | None
    url: str
    thumbnail_url: str | None
    posted_at: datetime
    ingested_at: datetime
    metrics: PostMetricsSummary | None = None
    has_sentiment: bool = False
    has_summary: bool = False
    ai_summary: str | None = None
    summary_generated_at: datetime | None = None


class SocialPostListOut(BaseModel):
    items: list[SocialPostOut]
    total: int
    page: int
    page_size: int
    total_pages: int
