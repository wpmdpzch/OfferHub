from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt as _bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import settings
from app.core.redis import redis_client


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": expire, "jti": str(uuid4())},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


async def create_refresh_token(user_id: str) -> str:
    jti = str(uuid4())
    expire = timedelta(days=settings.refresh_token_expire_days)
    token = jwt.encode(
        {
            "sub": user_id,
            "jti": jti,
            "exp": datetime.now(timezone.utc) + expire,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    await redis_client.setex(
        f"refresh_token:{user_id}:{jti}",
        int(expire.total_seconds()),
        token,
    )
    return token


def decode_token(token: str) -> dict:
    return jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )


async def revoke_refresh_token(user_id: str, jti: str) -> None:
    await redis_client.delete(f"refresh_token:{user_id}:{jti}")


async def revoke_all_refresh_tokens(user_id: str) -> None:
    keys = await redis_client.keys(f"refresh_token:{user_id}:*")
    if keys:
        await redis_client.delete(*keys)
