import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SentimentResultOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    social_post_id: uuid.UUID
    analyzed_at: datetime
    overall_sentiment: str
    positive_score: Decimal
    negative_score: Decimal
    neutral_score: Decimal
    comment_count_analyzed: int
    key_themes: list[str] | None
    sentiment_summary: str | None
    model_used: str


class SentimentTriggerOut(BaseModel):
    status: str
    message: str
    sentiment_result_id: uuid.UUID | None = None
