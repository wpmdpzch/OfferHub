import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.models.article import Article, ArticleStatus, SourceType
from app.models.social import BehaviorType, Tag, UserBehavior
from app.models.user import User
from app.services.schemas_article import (
    ArticleCreate,
    ArticleDetail,
    ArticleListItem,
    ArticleListOut,
    ArticleUpdate,
    SearchItem,
)

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _get_or_create_tags(db: AsyncSession, names: list[str]) -> list[Tag]:
    tags = []
    for name in names:
        result = await db.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            await db.flush()
        tags.append(tag)
    return tags


async def list_articles(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    sub_cat: str | None = None,
    tag: str | None = None,
    sort: Literal["latest", "hot", "recommend"] = "latest",
    keyword: str | None = None,
) -> ArticleListOut:
    q = select(Article).where(Article.status == ArticleStatus.published)

    if category:
        q = q.where(Article.category == category)
    if sub_cat:
        q = q.where(Article.sub_category == sub_cat)
    if keyword:
        q = q.where(Article.title.ilike(f"%{keyword}%"))
    if tag:
        from app.models.social import Tag as TagModel
        from sqlalchemy import Table, Column, Integer as Int
        from sqlalchemy import MetaData
        tag_result = await db.execute(select(TagModel).where(TagModel.name == tag))
        tag_obj = tag_result.scalar_one_or_none()
        if tag_obj:
            from sqlalchemy import exists
            article_tags = text(
                "EXISTS (SELECT 1 FROM article_tags WHERE article_id = articles.id AND tag_id = :tid)"
            )
            q = q.where(text("EXISTS (SELECT 1 FROM article_tags WHERE article_id = articles.id AND tag_id = :tid)").bindparams(tid=tag_obj.id))

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    if sort == "hot":
        q = q.order_by(Article.like_count.desc(), Article.published_at.desc())
    else:
        q = q.order_by(Article.published_at.desc())

    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()

    return ArticleListOut(
        total=total,
        page=page,
        page_size=page_size,
        items=[ArticleListItem.model_validate(r) for r in rows],
    )


async def get_article(
    db: AsyncSession, article_id: uuid.UUID, viewer_id: uuid.UUID | None = None
) -> ArticleDetail:
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article or article.status == ArticleStatus.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if article.status != ArticleStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    # 浏览计数写 Redis，异步落库
    await redis_client.incr(f"article:view:{article_id}")

    detail = ArticleDetail.model_validate(article)
    if viewer_id:
        liked = await db.execute(
            select(UserBehavior).where(
                UserBehavior.user_id == viewer_id,
                UserBehavior.article_id == article_id,
                UserBehavior.behavior == BehaviorType.like,
            )
        )
        collected = await db.execute(
            select(UserBehavior).where(
                UserBehavior.user_id == viewer_id,
                UserBehavior.article_id == article_id,
                UserBehavior.behavior == BehaviorType.collect,
            )
        )
        detail.viewer_liked = liked.scalar_one_or_none() is not None
        detail.viewer_collected = collected.scalar_one_or_none() is not None
    return detail


async def create_article(db: AsyncSession, author: User, data: ArticleCreate) -> ArticleDetail:
    from app.core.config import settings
    # REVIEW_ENABLED=false 时直接发布；true 时进入 pending 等待审核
    if settings.review_enabled:
        initial_status = ArticleStatus.pending
        published_at = None
    else:
        initial_status = ArticleStatus.published
        published_at = datetime.now(timezone.utc)
    summary = data.summary or (data.content[:200] if data.content else None)

    article = Article(
        title=data.title,
        content=data.content,
        summary=summary,
        author_id=author.id,
        category=data.category,
        sub_category=data.sub_category,
        source_type=SourceType.ugc,
        source_url=data.source_url,
        status=initial_status,
        published_at=published_at,
    )
    db.add(article)
    await db.flush()

    if data.tag_names:
        tags = await _get_or_create_tags(db, data.tag_names)
        for tag in tags:
            await db.execute(
                text("INSERT INTO article_tags (article_id, tag_id) VALUES (:aid, :tid) ON CONFLICT DO NOTHING")
                .bindparams(aid=article.id, tid=tag.id)
            )

    await db.commit()
    await db.refresh(article)
    return ArticleDetail.model_validate(article)


async def update_article(
    db: AsyncSession, article_id: uuid.UUID, user: User, data: ArticleUpdate
) -> ArticleDetail:
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if article.author_id != user.id and user.role.value not in ("editor", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    if data.title is not None:
        article.title = data.title
    if data.content is not None:
        article.content = data.content
        article.summary = data.content[:200]
    if data.category is not None:
        article.category = data.category
    if data.sub_category is not None:
        article.sub_category = data.sub_category

    if data.tag_names is not None:
        await db.execute(text("DELETE FROM article_tags WHERE article_id = :aid").bindparams(aid=article.id))
        tags = await _get_or_create_tags(db, data.tag_names)
        for tag in tags:
            await db.execute(
                text("INSERT INTO article_tags (article_id, tag_id) VALUES (:aid, :tid) ON CONFLICT DO NOTHING")
                .bindparams(aid=article.id, tid=tag.id)
            )

    await db.commit()
    await db.refresh(article)
    return ArticleDetail.model_validate(article)


async def delete_article(db: AsyncSession, article_id: uuid.UUID, user: User) -> None:
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if article.author_id != user.id and user.role.value not in ("editor", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    article.status = ArticleStatus.deleted
    await db.commit()


async def toggle_behavior(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    behavior: BehaviorType,
    add: bool,
) -> dict:
    result = await db.execute(select(Article).where(Article.id == article_id, Article.status == ArticleStatus.published))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    existing = await db.execute(
        select(UserBehavior).where(
            UserBehavior.user_id == user_id,
            UserBehavior.article_id == article_id,
            UserBehavior.behavior == behavior,
        )
    )
    record = existing.scalar_one_or_none()

    count_col = Article.like_count if behavior == BehaviorType.like else Article.collect_count

    if add and not record:
        db.add(UserBehavior(user_id=user_id, article_id=article_id, behavior=behavior))
        await db.execute(update(Article).where(Article.id == article_id).values({count_col: count_col + 1}))
    elif not add and record:
        await db.delete(record)
        await db.execute(update(Article).where(Article.id == article_id).values({count_col: count_col - 1}))

    await db.commit()
    return {"ok": True}


async def report_article(db: AsyncSession, article_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    existing = await db.execute(
        select(UserBehavior).where(
            UserBehavior.user_id == user_id,
            UserBehavior.article_id == article_id,
            UserBehavior.behavior == BehaviorType.report,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(UserBehavior(user_id=user_id, article_id=article_id, behavior=BehaviorType.report))
        article.status = ArticleStatus.pending
        await db.commit()
    return {"ok": True}


async def search_articles(
    db: AsyncSession,
    q: str,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    tag: str | None = None,
) -> dict:
    # 主路径：zhparser 全文检索
    base_conditions = "status = 'published'"
    if category:
        base_conditions += f" AND category = :category"

    fts_sql = text(f"""
        SELECT *, ts_headline('chinese', coalesce(summary, ''), query, 'MaxWords=20, MinWords=5') AS highlight,
               ts_rank(search_vector, query) AS rank
        FROM articles, plainto_tsquery('chinese', :q) query
        WHERE search_vector @@ query AND {base_conditions}
        ORDER BY rank DESC
        LIMIT :limit OFFSET :offset
    """)

    count_sql = text(f"""
        SELECT count(*) FROM articles, plainto_tsquery('chinese', :q) query
        WHERE search_vector @@ query AND {base_conditions}
    """)

    params: dict = {"q": q, "limit": page_size, "offset": (page - 1) * page_size}
    if category:
        params["category"] = category

    rows = (await db.execute(fts_sql, params)).mappings().all()
    total = (await db.execute(count_sql, params)).scalar_one()

    # 降级：pg_trgm 模糊匹配
    if total == 0:
        fallback_sql = text(f"""
            SELECT *, NULL AS highlight FROM articles
            WHERE title % :q AND {base_conditions}
            ORDER BY similarity(title, :q) DESC
            LIMIT :limit OFFSET :offset
        """)
        count_fallback = text(f"SELECT count(*) FROM articles WHERE title % :q AND {base_conditions}")
        rows = (await db.execute(fallback_sql, params)).mappings().all()
        total = (await db.execute(count_fallback, params)).scalar_one()

    items = []
    for row in rows:
        article = await db.get(Article, row["id"])
        if article:
            item = SearchItem.model_validate(article)
            item.highlight = row.get("highlight")
            items.append(item)

    return {"total": total, "page": page, "page_size": page_size, "items": items}
