"""端到端冒烟测试"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# NOTE: http is acceptable only for loopback (127.0.0.1/localhost) in local dev.
# Production smoke tests must use https://.
BASE = os.getenv("SMOKE_TEST_URL", "http://localhost:8000/api/v1")


def req(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[dict, int]:
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return json.loads(raw), e.code
        except Exception:
            return {"raw": raw.decode(errors="replace")}, e.code


class TestRunner:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            print(f"  OK  {name}")
            self.passed += 1
        else:
            print(f"  FAIL {name} | {detail}")
            self.failed += 1

    def run(self) -> int:
        print("\n=== OfferHub API Smoke Test ===\n")

        # 1. Health
        try:
            base_url = BASE.rsplit("/api/v1", 1)[0]
            resp = urllib.request.urlopen(f"{base_url}/health")
            r = json.loads(resp.read())
            status = resp.status
        except Exception:
            r, status = {}, 0
        self.check("GET /health", status == 200 and r.get("status") == "ok")

        # 2. 注册
        r, status = req("POST", "/auth/register", {
            "username": "smokeuser", "email": "smoke@example.com", "password": "password123"
        })
        self.check("POST /auth/register", r.get("code") == 0, str(r))

        # 3. 重复注册 -> 409
        r, status = req("POST", "/auth/register", {
            "username": "smokeuser", "email": "smoke@example.com", "password": "password123"
        })
        self.check("POST /auth/register duplicate -> 409", status == 409, f"status={status}")

        # 4. 登录
        r, status = req("POST", "/auth/login", {
            "email": "smoke@example.com", "password": "password123"
        })
        self.check("POST /auth/login", r.get("code") == 0, str(r))
        token = r.get("data", {}).get("access_token", "")
        refresh_token = r.get("data", {}).get("refresh_token", "")
        self.check("access_token present", bool(token))

        # 5. 获取当前用户
        r, status = req("GET", "/users/me", token=token)
        self.check("GET /users/me",
                   r.get("code") == 0 and r.get("data", {}).get("username") == "smokeuser", str(r))

        # 6. 发布文章
        r, status = req("POST", "/articles", {
            "title": "字节跳动前端面经 2026",
            "content": "## 一面\n- 手写 Promise\n- 事件循环\n\n## 二面\n- 系统设计",
            "category": "面经分享",
            "tag_names": ["前端", "字节跳动"]
        }, token=token)
        self.check("POST /articles", r.get("code") == 0, str(r))
        article_status = r.get("data", {}).get("status", "")
        # review_enabled=False 时直接 published，True 时 pending
        self.check("article status valid",
                   article_status in ("published", "pending"), f"status={article_status}")

        # 7. 文章列表
        r, status = req("GET", "/articles")
        self.check("GET /articles", r.get("code") == 0, str(r))

        # 8. 搜索
        q = urllib.parse.quote("字节")
        r, status = req("GET", f"/search?q={q}")
        self.check("GET /search", r.get("code") == 0, str(r))

        # 9. Refresh token
        r, status = req("POST", "/auth/refresh", {"refresh_token": refresh_token})
        self.check("POST /auth/refresh", r.get("code") == 0, str(r))

        # 10. 未认证访问需要认证的接口 -> 403
        r, status = req("POST", "/articles", {"title": "test", "content": "test"})
        self.check("POST /articles without token -> 403", status == 403, f"status={status}")

        print(f"\n{'=' * 40}")
        print(f"Results: {self.passed} passed, {self.failed} failed")
        return 0 if self.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(TestRunner().run())
