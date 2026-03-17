"""RSS 采集器，遵守合规红线"""
import asyncio
import logging
from datetime import datetime, timezone

import aiohttp
import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus, SourceType
from app.models.crawler import CrawlSource

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "OfferHub-Bot/1.0 (+https://github.com/wpmdpzch/OfferHub)"
}
SYSTEM_AUTHOR_ID = "00000000-0000-0000-0000-000000000001"
RATE_LIMIT_DELAY = 1.0  # 1 req/s


async def crawl_rss(db: AsyncSession, source: CrawlSource) -> int:
    saved = 0
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(source.url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                content = await resp.text()
    except Exception as e:
        raise RuntimeError(f"RSS fetch failed: {e}")

    feed = feedparser.parse(content)
    for entry in feed.entries:
        url = entry.get("link", "")
        if not url:
            continue

        # URL 去重
        existing = await db.execute(select(Article).where(Article.source_url == url))
        if existing.scalar_one_or_none():
            continue

        title = entry.get("title", "")[:500]
        summary_raw = entry.get("summary", "") or entry.get("description", "")
        summary = summary_raw[:200] if summary_raw else None
        content_raw = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else summary_raw

        published_at = None
        if entry.get("published_parsed"):
            import time
            published_at = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)

        article = Article(
            title=title,
            summary=summary,
            content=content_raw or summary,
            author_id=SYSTEM_AUTHOR_ID,
            source_type=SourceType.rss,
            source_url=url,
            status=ArticleStatus.published,
            published_at=published_at or datetime.now(timezone.utc),
        )
        db.add(article)
        saved += 1
        await asyncio.sleep(RATE_LIMIT_DELAY)

    await db.commit()
    logger.info(f"RSS {source.name}: saved {saved} articles")
    return saved
