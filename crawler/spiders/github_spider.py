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


async def crawl_github(db: AsyncSession, source: CrawlSource) -> int:
    from app.core.config import settings
    if settings.github_token:
        HEADERS["Authorization"] = f"Bearer {settings.github_token}"

    saved = 0
    config = source.config or {}
    query = config.get("query", "interview 面试 面经")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # 搜索高 Star 仓库
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
            repo_url = repo["html_url"]
            license_name = (repo.get("license") or {}).get("spdx_id")

            # 列出根目录 Markdown 文件
            contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"
            await asyncio.sleep(1.0)  # 合规：1 req/s
            async with session.get(contents_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    continue
                contents = await resp.json()

            for item in contents:
                if not isinstance(item, dict):
                    continue
                if not item.get("name", "").endswith(".md"):
                    continue
                if item.get("size", 0) > 500_000:  # 跳过超大文件
                    continue

                file_url = item.get("html_url", "")
                existing = await db.execute(select(Article).where(Article.source_url == file_url))
                if existing.scalar_one_or_none():
                    continue

                # 获取文件内容
                await asyncio.sleep(1.0)
                async with session.get(item["download_url"], timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        continue
                    content = await resp.text()

                title = item["name"].replace(".md", "").replace("-", " ").replace("_", " ")
                summary = content[:200]

                article = Article(
                    title=title[:500],
                    summary=summary,
                    content=content,
                    author_id=SYSTEM_AUTHOR_ID,
                    source_type=SourceType.github,
                    source_url=file_url,
                    source_license=license_name,
                    status=ArticleStatus.published,
                    published_at=datetime.now(timezone.utc),
                )
                db.add(article)
                saved += 1

        await db.commit()

    logger.info(f"GitHub crawler: saved {saved} articles")
    return saved
