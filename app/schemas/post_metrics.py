import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PostMetricsOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    snapshot_at: datetime
    views_count: int
    likes_count: int
    comments_count: int
    shares_count: int | None
    saves_count: int | None
    engagement_rate: Decimal | None
    rank_score: Decimal | None
