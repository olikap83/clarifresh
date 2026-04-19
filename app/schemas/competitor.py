import uuid
from datetime import datetime

from pydantic import BaseModel


class CompetitorCreate(BaseModel):
    name: str
    platform: str
    handle: str
    account_id: str | None = None
    hashtags: list[str] = []


class CompetitorUpdate(BaseModel):
    name: str | None = None
    hashtags: list[str] | None = None
    is_active: bool | None = None


class CompetitorOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    platform: str
    handle: str
    account_id: str | None
    hashtags: list[str] | None
    is_active: bool
    created_at: datetime


class CompetitorListOut(BaseModel):
    items: list[CompetitorOut]
    total: int
