import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus
from app.models.social import Comment
from app.services.schemas_comment import CommentCreate, CommentListOut, CommentOut


async def list_comments(
    db: AsyncSession, article_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> CommentListOut:
    q = select(Comment).where(Comment.article_id == article_id, Comment.parent_id.is_(None))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.order_by(Comment.created_at).offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return CommentListOut(total=total, page=page, page_size=page_size, items=[CommentOut.model_validate(r) for r in rows])


async def create_comment(
    db: AsyncSession, article_id: uuid.UUID, user_id: uuid.UUID, data: CommentCreate
) -> CommentOut:
    article = await db.get(Article, article_id)
    if not article or article.status != ArticleStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    comment = Comment(
        article_id=article_id,
        user_id=user_id,
        parent_id=data.parent_id,
        content=data.content,
    )
    db.add(comment)
    article.comment_count += 1
    await db.commit()
    await db.refresh(comment)
    return CommentOut.model_validate(comment)


async def delete_comment(db: AsyncSession, comment_id: uuid.UUID, user_id: uuid.UUID, role: str) -> None:
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    if comment.user_id != user_id and role not in ("editor", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    article = await db.get(Article, comment.article_id)
    if article:
        article.comment_count = max(0, article.comment_count - 1)

    await db.delete(comment)
    await db.commit()
