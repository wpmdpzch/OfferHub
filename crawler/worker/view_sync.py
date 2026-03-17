"""每 5 分钟将 Redis 中的 view 计数同步到 PostgreSQL"""
import logging
import uuid

import redis.asyncio as aioredis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


async def _read_view_counts(r: aioredis.Redis, keys: list[str]) -> dict[str, int]:
    """从 Redis 批量读取并删除 view 计数，返回 {article_id: count}。"""
    counts: dict[str, int] = {}
    for key in keys:
        count_str = await r.getdel(key)
        if count_str:
            counts[key.split(":")[-1]] = int(count_str)
    return counts


async def _flush_counts_to_db(
    session_factory: async_sessionmaker,
    r: aioredis.Redis,
    counts: dict[str, int],
) -> None:
    """将 view 计数批量写入 PostgreSQL，失败时回写 Redis 避免丢失。"""
    from app.models.article import Article
    async with session_factory() as db:
        for article_id, count in counts.items():
            try:
                await db.execute(
                    update(Article)
                    .where(Article.id == uuid.UUID(article_id))
                    .values(view_count=Article.view_count + count)
                )
            except Exception as e:
                logger.error(f"Failed to sync view count for {article_id}: {e}")
                await r.incrby(f"article:view:{article_id}", count)
        await db.commit()


async def sync_view_counts() -> None:
    from app.core.config import settings

    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    keys = await r.keys("article:view:*")
    if not keys:
        await engine.dispose()
        return

    counts = await _read_view_counts(r, keys)
    await _flush_counts_to_db(session_factory, r, counts)

    logger.info(f"Synced view counts for {len(keys)} articles")
    await engine.dispose()
