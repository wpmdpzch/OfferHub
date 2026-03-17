"""端到端冒烟测试"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://localhost:8000/api/v1"
passed = 0
failed = 0


def req(method, path, body=None, token=None):
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


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  OK  {name}")
        passed += 1
    else:
        print(f"  FAIL {name} | {detail}")
        failed += 1


print("\n=== OfferHub API Smoke Test ===\n")

# 1. Health
try:
    resp = urllib.request.urlopen("http://localhost:8000/health")
    r = json.loads(resp.read())
    status = resp.status
except Exception as e:
    r, status = {}, 0
check("GET /health", status == 200 and r.get("status") == "ok")

# 2. 注册
r, status = req("POST", "/auth/register", {
    "username": "smokeuser", "email": "smoke@example.com", "password": "password123"
})
check("POST /auth/register", r.get("code") == 0, r)

# 3. 重复注册 -> 409
r, status = req("POST", "/auth/register", {
    "username": "smokeuser", "email": "smoke@example.com", "password": "password123"
})
check("POST /auth/register duplicate -> 409", status == 409, f"status={status}")

# 4. 登录
r, status = req("POST", "/auth/login", {
    "email": "smoke@example.com", "password": "password123"
})
check("POST /auth/login", r.get("code") == 0, r)
token = r.get("data", {}).get("access_token", "")
refresh_token = r.get("data", {}).get("refresh_token", "")
check("access_token present", bool(token))

# 5. 获取当前用户
r, status = req("GET", "/users/me", token=token)
check("GET /users/me", r.get("code") == 0 and r.get("data", {}).get("username") == "smokeuser", r)

# 6. 发布文章（新用户积分=10，应进 pending）
r, status = req("POST", "/articles", {
    "title": "字节跳动前端面经 2026",
    "content": "## 一面\n- 手写 Promise\n- 事件循环\n\n## 二面\n- 系统设计",
    "category": "面经分享",
    "tag_names": ["前端", "字节跳动"]
}, token=token)
check("POST /articles", r.get("code") == 0, r)
article_id = r.get("data", {}).get("id", "")
article_status = r.get("data", {}).get("status", "")
check("new user article -> pending", article_status == "pending", f"status={article_status}")

# 7. 文章列表
r, status = req("GET", "/articles")
check("GET /articles", r.get("code") == 0, r)

# 8. 搜索（URL encode 中文）
q = urllib.parse.quote("字节")
r, status = req("GET", f"/search?q={q}")
check("GET /search", r.get("code") == 0, r)

# 9. Refresh token
r, status = req("POST", "/auth/refresh", {"refresh_token": refresh_token})
check("POST /auth/refresh", r.get("code") == 0, r)

# 10. 未认证访问需要认证的接口 -> 403
r, status = req("POST", "/articles", {"title": "test", "content": "test"})
check("POST /articles without token -> 403", status == 403, f"status={status}")

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
