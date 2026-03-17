import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    type: Mapped[CrawlSourceType] = mapped_column(Enum(CrawlSourceType, name="crawl_source_type"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    crawl_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config: Mapped[dict | None] = mapped_column(JSONB)


class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("crawl_sources.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[CrawlTaskStatus] = mapped_column(Enum(CrawlTaskStatus, name="crawl_task_status"), nullable=False, default=CrawlTaskStatus.pending)
    items_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_saved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_msg: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
