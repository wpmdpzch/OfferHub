import uuid
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.response import Response, ok
from app.core.security import decode_token
from app.models.social import BehaviorType
from app.models.user import User
from app.services import article_service, comment_service
from app.services.schemas_article import ArticleCreate, ArticleUpdate
from app.services.schemas_comment import CommentCreate

router = APIRouter()

_optional_bearer = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_optional_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    if not credentials:
        return None
    try:
        from jose import JWTError
        from sqlalchemy import select
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.get("/articles", response_model=Response)
async def list_articles(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category: Optional[str] = None,
    sub_cat: Optional[str] = None,
    tag: Optional[str] = None,
    sort: Literal["latest", "hot", "recommend"] = "latest",
    keyword: Optional[str] = None,
):
    result = await article_service.list_articles(db, page, page_size, category, sub_cat, tag, sort, keyword)
    return ok(result.model_dump())


@router.post("/articles", response_model=Response)
async def create_article(
    data: ArticleCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    article = await article_service.create_article(db, current_user, data)
    return ok(article.model_dump())


@router.get("/search", response_model=Response)
async def search(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category: Optional[str] = None,
    tag: Optional[str] = None,
):
    result = await article_service.search_articles(db, q, page, page_size, category, tag)
    return ok(result)


@router.get("/articles/{article_id}", response_model=Response)
async def get_article(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Optional[User], Depends(get_optional_user)] = None,
):
    viewer_id = current_user.id if current_user else None
    article = await article_service.get_article(db, article_id, viewer_id)
    return ok(article.model_dump())


@router.put("/articles/{article_id}", response_model=Response)
async def update_article(
    article_id: uuid.UUID,
    data: ArticleUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    article = await article_service.update_article(db, article_id, current_user, data)
    return ok(article.model_dump())


@router.delete("/articles/{article_id}", response_model=Response)
async def delete_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await article_service.delete_article(db, article_id, current_user)
    return ok()


@router.post("/articles/{article_id}/like", response_model=Response)
async def like_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return ok(await article_service.toggle_behavior(db, article_id, current_user.id, BehaviorType.like, True))


@router.delete("/articles/{article_id}/like", response_model=Response)
async def unlike_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return ok(await article_service.toggle_behavior(db, article_id, current_user.id, BehaviorType.like, False))


@router.post("/articles/{article_id}/collect", response_model=Response)
async def collect_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return ok(await article_service.toggle_behavior(db, article_id, current_user.id, BehaviorType.collect, True))


@router.delete("/articles/{article_id}/collect", response_model=Response)
async def uncollect_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return ok(await article_service.toggle_behavior(db, article_id, current_user.id, BehaviorType.collect, False))


@router.post("/articles/{article_id}/report", response_model=Response)
async def report_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return ok(await article_service.report_article(db, article_id, current_user.id))


@router.get("/articles/{article_id}/comments", response_model=Response)
async def list_comments(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    result = await comment_service.list_comments(db, article_id, page, page_size)
    return ok(result.model_dump())


@router.post("/articles/{article_id}/comments", response_model=Response)
async def create_comment(
    article_id: uuid.UUID,
    data: CommentCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    comment = await comment_service.create_comment(db, article_id, current_user.id, data)
    return ok(comment.model_dump())


@router.delete("/comments/{comment_id}", response_model=Response)
async def delete_comment(
    comment_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await comment_service.delete_comment(db, comment_id, current_user.id, current_user.role.value)
    return ok()
