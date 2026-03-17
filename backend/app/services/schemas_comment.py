import uuid
from datetime import datetime

from pydantic import BaseModel


class CommentCreate(BaseModel):
    content: str
    parent_id: uuid.UUID | None = None


class CommentOut(BaseModel):
    id: uuid.UUID
    article_id: uuid.UUID
    user_id: uuid.UUID
    parent_id: uuid.UUID | None
    content: str
    like_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CommentOut]
