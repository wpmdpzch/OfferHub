from fastapi import APIRouter

from app.api.v1.endpoints import articles, users, admin

router = APIRouter(prefix="/api/v1")
router.include_router(users.router, tags=["auth & users"])
router.include_router(articles.router, tags=["articles"])
router.include_router(admin.router, tags=["admin"])
