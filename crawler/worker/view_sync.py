"""每 5 分钟将 Redis 中的 view 计数同步到 PostgreSQL"""
import logging
import uuid

import redis.asyncio as aioredis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


async def sync_view_counts() -> None:
    from app.core.config import settings
    from app.models.article import Article

    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    keys = await r.keys("article:view:*")
    if not keys:
        await engine.dispose()
        return

    async with session_factory() as db:
        for key in keys:
            count_str = await r.getdel(key)
            if not count_str:
                continue
            article_id = key.split(":")[-1]
            try:
                await db.execute(
                    update(Article)
                    .where(Article.id == uuid.UUID(article_id))
                    .values(view_count=Article.view_count + int(count_str))
                )
            except Exception as e:
                logger.error(f"Failed to sync view count for {article_id}: {e}")
                await r.incrby(key, int(count_str))  # 回写，避免丢失
        await db.commit()

    logger.info(f"Synced view counts for {len(keys)} articles")
    await engine.dispose()
