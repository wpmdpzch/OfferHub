import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    verify_password,
)
from app.models.user import User
from app.services.schemas_user import TokenOut, UserLogin, UserOut, UserRegister, UserUpdate


async def register(db: AsyncSession, data: UserRegister) -> UserOut:
    existing = await db.execute(
        select(User).where((User.email == data.email) | (User.username == data.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱或用户名已存在")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        points=10,  # 注册积分
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


async def login(db: AsyncSession, data: UserLogin) -> TokenOut:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = await create_refresh_token(str(user.id))
    return TokenOut(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenOut:
    from jwt import InvalidTokenError
    try:
        payload = decode_token(refresh_token)
        user_id: str = payload["sub"]
        jti: str = payload["jti"]
    except (InvalidTokenError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    from app.core.redis import redis_client
    stored = await redis_client.get(f"refresh_token:{user_id}:{jti}")
    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已失效")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    await revoke_refresh_token(user_id, jti)
    new_access = create_access_token(str(user.id), user.role.value)
    new_refresh = await create_refresh_token(str(user.id))
    return TokenOut(access_token=new_access, refresh_token=new_refresh)


async def logout(user_id: str, refresh_token: str) -> None:
    from jwt import InvalidTokenError
    try:
        payload = decode_token(refresh_token)
        jti: str = payload["jti"]
        await revoke_refresh_token(user_id, jti)
    except (InvalidTokenError, KeyError):
        pass  # token 已过期或无效，忽略


async def update_me(db: AsyncSession, user: User, data: UserUpdate) -> UserOut:
    if data.username is not None:
        existing = await db.execute(select(User).where(User.username == data.username, User.id != user.id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已被占用")
        user.username = data.username
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)
