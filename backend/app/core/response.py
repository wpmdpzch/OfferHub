from typing import Any

from pydantic import BaseModel


class Response(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: Any = None


def ok(data: Any = None, msg: str = "ok") -> Response:
    return Response(code=0, msg=msg, data=data)


def err(code: int, msg: str) -> Response:
    return Response(code=code, msg=msg)
