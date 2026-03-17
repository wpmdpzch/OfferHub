"""GitHub 仓库 Markdown 采集器"""
import asyncio
import logging
from datetime import datetime, timezone

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus, SourceType
from app.models.crawler import CrawlSource

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "OfferHub-Bot/1.0 (+https://github.com/wpmdpzch/OfferHub)",
    "Accept": "application/vnd.github+json",
}
SYSTEM_AUTHOR_ID = "00000000-0000-0000-0000-000000000001"
MIN_STARS = 500


async def _fetch_md_file(session: aiohttp.ClientSession, item: dict) -> str | None:
    """下载单个 Markdown 文件内容，失败返回 None。"""
    if not isinstance(item, dict):
        return None
    if not item.get("name", "").endswith(".md"):
        return None
    if item.get("size", 0) > 500_000:
        return None
    await asyncio.sleep(1.0)  # 合规：1 req/s
    async with session.get(item["download_url"], timeout=aiohttp.ClientTimeout(total=15)) as resp:
        if resp.status != 200:
            return None
        return await resp.text()


async def _save_md_items(
    db: AsyncSession,
    session: aiohttp.ClientSession,
    contents: list,
    repo: dict,
) -> int:
    """遍历目录条目，保存未入库的 Markdown 文件，返回保存数量。"""
    saved = 0
    license_name = (repo.get("license") or {}).get("spdx_id")
    for item in contents:
        if not isinstance(item, dict) or not item.get("name", "").endswith(".md"):
            continue
        if item.get("size", 0) > 500_000:
            continue

        file_url = item.get("html_url", "")
        existing = await db.execute(select(Article).where(Article.source_url == file_url))
        if existing.scalar_one_or_none():
            continue

        content = await _fetch_md_file(session, item)
        if content is None:
            continue

        title = item["name"].replace(".md", "").replace("-", " ").replace("_", " ")
        db.add(Article(
            title=title[:500],
            summary=content[:200],
            content=content,
            author_id=SYSTEM_AUTHOR_ID,
            source_type=SourceType.github,
            source_url=file_url,
            source_license=license_name,
            status=ArticleStatus.published,
            published_at=datetime.now(timezone.utc),
        ))
        saved += 1
    return saved


async def crawl_github(db: AsyncSession, source: CrawlSource) -> int:
    from app.core.config import settings
    if settings.github_token:
        HEADERS["Authorization"] = f"Bearer {settings.github_token}"

    config = source.config or {}
    query = config.get("query", "interview 面试 面经")
    saved = 0

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        search_url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=30"
        async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                raise RuntimeError(f"GitHub search failed: {resp.status}")
            data = await resp.json()

        for repo in data.get("items", []):
            if repo.get("stargazers_count", 0) < MIN_STARS:
                continue

            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"
            await asyncio.sleep(1.0)  # 合规：1 req/s
            async with session.get(contents_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    continue
                contents = await resp.json()

            saved += await _save_md_items(db, session, contents, repo)

        await db.commit()

    logger.info(f"GitHub crawler: saved {saved} articles")
    return saved
