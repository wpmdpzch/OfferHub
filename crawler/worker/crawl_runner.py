"""执行单个采集任务"""
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def run_crawl_task(task_id: str) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.config import settings
    from app.models.crawler import CrawlTask, CrawlTaskStatus, CrawlSource

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        task = await db.get(CrawlTask, uuid.UUID(task_id))
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        source = await db.get(CrawlSource, task.source_id)
        if not source or not source.enabled:
            task.status = CrawlTaskStatus.failed
            task.error_msg = "Source not found or disabled"
            await db.commit()
            return

        task.status = CrawlTaskStatus.running
        task.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            if source.type.value == "rss":
                from crawler.spiders.rss_spider import crawl_rss
                saved = await crawl_rss(db, source)
            elif source.type.value == "github":
                from crawler.spiders.github_spider import crawl_github
                saved = await crawl_github(db, source)
            else:
                saved = 0

            task.status = CrawlTaskStatus.done
            task.items_saved = saved
            source.last_crawled_at = datetime.now(timezone.utc)
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task.status = CrawlTaskStatus.failed
            task.error_msg = str(e)
            task.retry_count += 1

        task.finished_at = datetime.now(timezone.utc)
        await db.commit()

    await engine.dispose()
