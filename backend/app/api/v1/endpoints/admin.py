import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AdminOnly, EditorOrAdmin
from app.core.response import Response, ok
from app.models.article import Article, ArticleStatus
from app.models.crawler import CrawlSource, CrawlTask, CrawlTaskStatus
from app.models.social import Tag
from app.services.schemas_article import ArticleListItem, ArticleListOut

router = APIRouter(prefix="/admin")


@router.get("/articles/pending", response_model=Response)
async def pending_articles(
    _: EditorOrAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    from sqlalchemy import func
    q = select(Article).where(Article.status == ArticleStatus.pending)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.order_by(Article.created_at).offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return ok(ArticleListOut(
        total=total, page=page, page_size=page_size,
        items=[ArticleListItem.model_validate(r) for r in rows],
    ).model_dump())


@router.post("/articles/{article_id}/approve", response_model=Response)
async def approve_article(
    article_id: uuid.UUID,
    _: EditorOrAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from datetime import datetime, timezone
    await db.execute(
        update(Article).where(Article.id == article_id).values(
            status=ArticleStatus.published,
            published_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()
    return ok()


@router.post("/articles/{article_id}/reject", response_model=Response)
async def reject_article(
    article_id: uuid.UUID,
    _: EditorOrAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(update(Article).where(Article.id == article_id).values(status=ArticleStatus.rejected))
    await db.commit()
    return ok()


@router.get("/tags", response_model=Response)
async def list_tags(_: EditorOrAdmin, db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.execute(select(Tag).order_by(Tag.article_count.desc()))).scalars().all()
    return ok([{"id": t.id, "name": t.name, "category": t.category, "article_count": t.article_count} for t in rows])


@router.post("/tags", response_model=Response)
async def create_tag(
    name: str,
    category: Optional[str] = None,
    _: EditorOrAdmin = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    tag = Tag(name=name, category=category)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return ok({"id": tag.id, "name": tag.name})


@router.delete("/tags/{tag_id}", response_model=Response)
async def delete_tag(
    tag_id: int,
    _: EditorOrAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tag = await db.get(Tag, tag_id)
    if tag:
        await db.delete(tag)
        await db.commit()
    return ok()


@router.get("/crawl/sources", response_model=Response)
async def list_sources(_: AdminOnly, db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.execute(select(CrawlSource))).scalars().all()
    return ok([{
        "id": s.id, "name": s.name, "type": s.type, "url": s.url,
        "enabled": s.enabled, "crawl_interval": s.crawl_interval,
        "last_crawled_at": s.last_crawled_at,
    } for s in rows])


@router.post("/crawl/sources", response_model=Response)
async def create_source(
    name: str, type: str, url: str, crawl_interval: int = 60,
    _: AdminOnly = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    source = CrawlSource(name=name, type=type, url=url, crawl_interval=crawl_interval)
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return ok({"id": source.id, "name": source.name})


@router.post("/crawl/trigger", response_model=Response)
async def trigger_crawl(
    source_id: int,
    _: AdminOnly,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.core.redis import redis_client
    task = CrawlTask(source_id=source_id, status=CrawlTaskStatus.pending)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    await redis_client.lpush("crawl_queue", str(task.id))
    return ok({"task_id": str(task.id)})
