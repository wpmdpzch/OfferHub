"""GitHub 仓库 Markdown 采集器，支持递归子目录"""
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
MAX_DEPTH = 3  # 最大递归深度
MAX_FILES_PER_REPO = 50  # 每个仓库最多采集文件数
RATE_LIMIT_DELAY = 1.0  # 1 req/s


async def _fetch_content(session: aiohttp.ClientSession, url: str) -> dict | None:
    """获取目录或文件内容"""
    await asyncio.sleep(RATE_LIMIT_DELAY)
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
    except Exception:
        return None


def _is_md_file(item: dict) -> bool:
    """判断是否为可采集的 Markdown 文件"""
    if not isinstance(item, dict):
        return False
    name = item.get("name", "")
    if not name.endswith(".md") and not name.endswith(".markdown"):
        return False
    # 跳过过大的文件
    if item.get("size", 0) > 500_000:
        return False
    return True


async def _download_md_content(session: aiohttp.ClientSession, download_url: str) -> str | None:
    """下载单个 Markdown 文件内容"""
    await asyncio.sleep(RATE_LIMIT_DELAY)
    try:
        async with session.get(download_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            return await resp.text()
    except Exception:
        return None


async def _crawl_directory(
    session: aiohttp.ClientSession,
    db: AsyncSession,
    contents_url: str,
    repo: dict,
    license_name: str | None,
    saved_count: dict,
    depth: int = 0,
) -> None:
    """递归采集目录中的 Markdown 文件"""
    if depth >= MAX_DEPTH or saved_count["total"] >= MAX_FILES_PER_REPO:
        return

    contents = await _fetch_content(session, contents_url)
    if not contents or not isinstance(contents, list):
        return

    for item in contents:
        if saved_count["total"] >= MAX_FILES_PER_REPO:
            break

        if item.get("type") == "dir":
            # 递归进入子目录
            await _crawl_directory(
                session, db, item["url"], repo, license_name, saved_count, depth + 1
            )
        elif _is_md_file(item):
            # 检查是否已入库
            file_url = item.get("html_url", "")
            existing = await db.execute(select(Article).where(Article.source_url == file_url))
            if existing.scalar_one_or_none():
                continue

            # 跳过 README 等首页文件（标题意义不大）
            name_lower = item["name"].lower()
            if name_lower.startswith("readme") or name_lower.startswith("changelog"):
                title = item["name"].replace(".md", "").replace(".markdown", "").replace("-", " ").replace("_", " ").title()
            else:
                title = item["name"].replace(".md", "").replace(".markdown", "").replace("-", " ").replace("_", " ")

            content = await _download_md_content(session, item.get("download_url", ""))
            if content is None:
                continue

            article = Article(
                title=title[:500],
                summary=content[:200] if content else None,
                content=content,
                author_id=SYSTEM_AUTHOR_ID,
                source_type=SourceType.github,
                source_url=file_url,
                source_license=license_name,
                status=ArticleStatus.published,
                published_at=datetime.now(timezone.utc),
            )
            db.add(article)
            saved_count["total"] += 1
            logger.info(f"  Saved: {title[:60]}")


async def crawl_github(db: AsyncSession, source: CrawlSource) -> int:
    from app.core.config import settings
    if settings.github_token:
        HEADERS["Authorization"] = f"Bearer {settings.github_token}"

    config = source.config or {}
    query = config.get("query", "interview 面试 面经")
    saved = {"total": 0}

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # Step 1: 搜索高 Star 仓库
        search_url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=30"
        resp = await _fetch_content(session, search_url)
        if not resp:
            raise RuntimeError("GitHub search failed")

        items = resp.get("items", [])
        logger.info(f"GitHub search: found {len(items)} repositories")

        for repo in items:
            if saved["total"] >= MAX_FILES_PER_REPO:
                break

            stars = repo.get("stargazers_count", 0)
            if stars < MIN_STARS:
                continue

            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            license_name = (repo.get("license") or {}).get("spdx_id")

            logger.info(f"Crawling repo: {owner}/{repo_name} (⭐ {stars})")

            # Step 2: 获取仓库根目录
            contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"
            await _crawl_directory(session, db, contents_url, repo, license_name, saved)

        await db.commit()

    logger.info(f"GitHub crawler: saved {saved['total']} articles")
    return saved["total"]
