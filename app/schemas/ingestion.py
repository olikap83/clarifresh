import uuid
from datetime import datetime

from pydantic import BaseModel


class IngestionTriggerRequest(BaseModel):
    competitor_id: uuid.UUID | None = None
    platform: str | None = None
    max_posts_per_competitor: int = 50


class IngestionJobOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    trigger_type: str
    triggered_by: str | None
    platform: str | None
    competitor_id: uuid.UUID | None
    apify_run_id: str | None
    status: str
    posts_ingested: int | None
    comments_ingested: int | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None


class IngestionJobListOut(BaseModel):
    items: list[IngestionJobOut]
    total: int


class IngestionTriggerOut(BaseModel):
    job_id: uuid.UUID
    status: str
    message: str
    competitors_targeted: int
