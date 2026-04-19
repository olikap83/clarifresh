import uuid
from datetime import datetime

from pydantic import BaseModel


class CommentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    platform_comment_id: str
    author_handle: str | None
    text: str
    likes_count: int
    posted_at: datetime | None


class CommentListOut(BaseModel):
    items: list[CommentOut]
    total: int
    page: int
    page_size: int
