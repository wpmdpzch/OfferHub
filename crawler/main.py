"""
采集 Worker 主入口
- 监听 Redis crawl_queue，执行采集任务
- 每 5 分钟同步 view 计数从 Redis → PostgreSQL
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from worker.view_sync import sync_view_counts
from worker.crawl_runner import run_crawl_task

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def crawl_loop():
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
                await run_crawl_task(task_id)
        except Exception as e:
            logger.error(f"Crawl loop error: {e}")
            await asyncio.sleep(5)


async def view_sync_loop():
    logger.info("View sync loop started (interval: 300s)")
    while True:
        await asyncio.sleep(300)
        try:
            await sync_view_counts()
        except Exception as e:
            logger.error(f"View sync error: {e}")


async def main():
    await asyncio.gather(crawl_loop(), view_sync_loop())


if __name__ == "__main__":
    asyncio.run(main())
