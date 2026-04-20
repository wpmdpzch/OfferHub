"""
采集 Worker 主入口
- APScheduler 定时调度采集任务
- 监听 Redis crawl_queue 消费采集任务
- 每 5 分钟同步 view 计数从 Redis → PostgreSQL
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_

from worker.view_sync import sync_view_counts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def enqueue_crawl_tasks():
    """检查需要采集的源，往 Redis 队列推送任务"""
    import redis.asyncio as aioredis
    from app.core.config import settings
    from app.models.crawler import CrawlSource, CrawlTask, CrawlTaskStatus
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    try:
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        r = aioredis.from_url(settings.redis_url, decode_responses=True)

        async with session_factory() as db:
            # 查找需要采集的源（上一次采集时间 + 间隔 < 当前时间）
            result = await db.execute(
                select(CrawlSource).where(
                    CrawlSource.enabled.is_(True)
                )
            )
            sources = result.scalars().all()

            for source in sources:
                if source.last_crawled_at is None:
                    should_crawl = True
                else:
                    elapsed = (datetime.now(timezone.utc) - source.last_crawled_at.replace(tzinfo=timezone.utc)).total_seconds()
                    should_crawl = elapsed >= (source.crawl_interval * 60)

                if should_crawl:
                    # 检查是否已有待处理/运行中的任务
                    existing = await db.execute(
                        select(CrawlTask).where(
                            and_(
                                CrawlTask.source_id == source.id,
                                CrawlTask.status.in_([CrawlTaskStatus.pending.value, CrawlTaskStatus.running.value])
                            )
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # 创建任务并推入队列
                    task = CrawlTask(source_id=source.id)
                    db.add(task)
                    await db.flush()
                    await r.lpush("crawl_queue", str(task.id))
                    logger.info(f"Scheduled crawl task for source: {source.name}")

            await db.commit()
        await engine.dispose()
    except Exception as e:
        logger.error(f"Failed to enqueue crawl tasks: {e}")


async def crawl_loop():
    """从 Redis 队列消费采集任务"""
    import redis.asyncio as aioredis
    from app.core.config import settings

    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    logger.info("Crawl worker started, listening on crawl_queue...")

    while True:
        try:
            item = await r.brpop("crawl_queue", timeout=5)
            if item:
                _, task_id = item
                logger.info(f"Processing crawl task: {task_id}")
                from worker.crawl_runner import run_crawl_task
                await run_crawl_task(task_id)
        except Exception as e:
            logger.error(f"Crawl loop error: {e}")
            await asyncio.sleep(5)


async def view_sync_loop():
    """定时同步 view 计数"""
    logger.info("View sync loop started (interval: 300s)")
    while True:
        await asyncio.sleep(300)
        try:
            await sync_view_counts()
        except Exception as e:
            logger.error(f"View sync error: {e}")


async def main():
    scheduler = AsyncIOScheduler()
    # 每 15 分钟检查需要采集的源
    scheduler.add_job(enqueue_crawl_tasks, IntervalTrigger(minutes=15))
    scheduler.start()
    logger.info("Scheduler started: crawl tasks every 15 minutes")

    await asyncio.gather(
        crawl_loop(),
        view_sync_loop(),
    )


if __name__ == "__main__":
    asyncio.run(main())
