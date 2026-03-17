import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CrawlSourceType(str, enum.Enum):
    github = "github"
    gitee = "gitee"
    rss = "rss"
    web = "web"


class CrawlTaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class CrawlSource(Base):
    __tablename__ = "crawl_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[CrawlSourceType] = mapped_column(Enum(CrawlSourceType), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    crawl_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config: Mapped[dict | None] = mapped_column(JSONB)


class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    import uuid as _uuid
    from sqlalchemy.dialects.postgresql import UUID as _UUID
    from sqlalchemy import ForeignKey as _FK

    id: Mapped[_uuid.UUID] = mapped_column(_UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    source_id: Mapped[int] = mapped_column(Integer, _FK("crawl_sources.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[CrawlTaskStatus] = mapped_column(Enum(CrawlTaskStatus), nullable=False, default=CrawlTaskStatus.pending)
    items_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_saved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_msg: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
