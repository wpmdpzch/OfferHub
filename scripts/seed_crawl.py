"""种子内容预采集脚本，一次性执行，不走 APScheduler"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.config import settings
    from app.models.crawler import CrawlSource, CrawlSourceType
    from sqlalchemy import select

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        # 采集所有启用的 GitHub 源
        result = await db.execute(
            select(CrawlSource).where(
                CrawlSource.enabled == True,
                CrawlSource.type == CrawlSourceType.github,
            )
        )
        github_sources = result.scalars().all()

        for source in github_sources:
            logger.info(f"Seeding from GitHub source: {source.name}")
            from crawler.spiders.github_spider import crawl_github
            try:
                saved = await crawl_github(db, source)
                logger.info(f"  → {saved} articles saved")
            except Exception as e:
                logger.error(f"  → Failed: {e}")

        # 采集所有 RSS 源
        result = await db.execute(
            select(CrawlSource).where(
                CrawlSource.enabled == True,
                CrawlSource.type == CrawlSourceType.rss,
            )
        )
        rss_sources = result.scalars().all()

        for source in rss_sources:
            logger.info(f"Seeding from RSS source: {source.name}")
            from crawler.spiders.rss_spider import crawl_rss
            try:
                saved = await crawl_rss(db, source)
                logger.info(f"  → {saved} articles saved")
            except Exception as e:
                logger.error(f"  → Failed: {e}")

    await engine.dispose()
    logger.info("Seed crawl completed")


if __name__ == "__main__":
    asyncio.run(main())
