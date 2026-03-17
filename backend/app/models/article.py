import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ArticleStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    rejected = "rejected"
    deleted = "deleted"


class SourceType(str, enum.Enum):
    ugc = "ugc"
    github = "github"
    gitee = "gitee"
    rss = "rss"
    crawler = "crawler"


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))
    sub_category: Mapped[str | None] = mapped_column(String(50))
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False, default=SourceType.ugc)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_license: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[ArticleStatus] = mapped_column(Enum(ArticleStatus), nullable=False, default=ArticleStatus.pending)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    collect_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped["User"] = relationship("User", lazy="selectin")  # type: ignore[name-defined]
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="article_tags", lazy="selectin")  # type: ignore[name-defined]
