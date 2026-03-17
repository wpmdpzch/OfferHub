import uuid
from datetime import datetime

from pydantic import BaseModel, HttpUrl


class AuthorOut(BaseModel):
    id: uuid.UUID
    username: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ArticleCreate(BaseModel):
    title: str
    content: str
    category: str | None = None
    sub_category: str | None = None
    tag_names: list[str] = []
    source_url: str | None = None


class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    sub_category: str | None = None
    tag_names: list[str] | None = None


class ArticleListItem(BaseModel):
    id: uuid.UUID
    title: str
    summary: str | None
    category: str | None
    sub_category: str | None
    tags: list[TagOut]
    author: AuthorOut
    source_url: str | None
    source_type: str
    view_count: int
    like_count: int
    collect_count: int
    comment_count: int
    published_at: datetime | None

    model_config = {"from_attributes": True}


class ArticleDetail(ArticleListItem):
    content: str | None
    source_license: str | None
    updated_at: datetime
    viewer_liked: bool | None = None
    viewer_collected: bool | None = None


class ArticleListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ArticleListItem]


class SearchItem(ArticleListItem):
    highlight: str | None = None
