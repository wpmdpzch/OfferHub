import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        if not 2 <= len(v) <= 50:
            raise ValueError("用户名长度 2-50")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码至少 8 位")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    avatar_url: str | None
    role: str
    points: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    username: str | None = None
    avatar_url: str | None = None
