from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.response import Response, ok
from app.services import user_service
from app.services.schemas_user import TokenOut, UserLogin, UserOut, UserRegister, UserUpdate

router = APIRouter()


@router.post("/auth/register", response_model=Response)
async def register(data: UserRegister, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await user_service.register(db, data)
    return ok(user.model_dump())


@router.post("/auth/login", response_model=Response)
async def login(data: UserLogin, db: Annotated[AsyncSession, Depends(get_db)]):
    tokens = await user_service.login(db, data)
    return ok(tokens.model_dump())


@router.post("/auth/refresh", response_model=Response)
async def refresh(
    refresh_token: Annotated[str, Body(embed=True)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await user_service.refresh_tokens(db, refresh_token)
    return ok(tokens.model_dump())


@router.post("/auth/logout", response_model=Response)
async def logout(
    refresh_token: Annotated[str, Body(embed=True)],
    current_user: CurrentUser,
):
    await user_service.logout(str(current_user.id), refresh_token)
    return ok()


@router.get("/users/me", response_model=Response)
async def get_me(current_user: CurrentUser):
    return ok(UserOut.model_validate(current_user).model_dump())


@router.put("/users/me", response_model=Response)
async def update_me(
    data: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await user_service.update_me(db, current_user, data)
    return ok(user.model_dump())
