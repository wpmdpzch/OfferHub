# OfferHub Code Review Feedback

> 审查时间：2026-03-17
> 审查范围：backend / crawler / frontend / scripts（全量扫描）
> 结论：**需修改**

---

## 🔴 阻塞问题（必须修复，阻塞合并）

### 1. 硬编码凭证 — `backend/app/core/config.py:10-17`

**问题**：密码/JWT 密钥直接写在源码中。即使后续删除，Git 历史仍会永久保留，存在凭证泄露风险（CWE-798）。

**修复方案**：
```python
# ❌ 错误
SECRET_KEY = "hardcoded-secret-key"
DB_PASSWORD = "hardcoded-password"

# ✅ 正确：只从环境变量读取，不设置任何默认密钥值
import os

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set")
```

同时检查 `.env.example` 是否已加入 `.gitignore`，确保真实 `.env` 不被提交。

---

### 2. python-jose JWT 算法混淆漏洞 — `backend/requirements.txt:8-9`

**问题**：python-jose ≤ 3.3.0 存在 ECDSA 算法混淆攻击（GHSA-6c5p-j8vq-pqhj），攻击者可伪造 JWT 绕过身份验证。

**修复方案**：
```txt
# ❌ 当前
python-jose==3.3.0

# ✅ 方案一：升级并启用 cryptography 后端
python-jose[cryptography]>=3.3.0

# ✅ 方案二（推荐）：迁移到 PyJWT，维护更活跃
PyJWT>=2.8.0
```

---

### 3. python-jose 同上漏洞 — `crawler/requirements.txt:7-8`

同上，crawler 服务也引用了 python-jose，修复方式相同。

---

## 🟡 需改进（建议在本迭代修复）

### 4. python-multipart DoS 漏洞 — `backend/requirements.txt:11-12`

**问题**：python-multipart < 0.0.18 解析 multipart 表单时，攻击者可发送恶意请求导致 CPU 耗尽，阻塞 ASGI 事件循环（GHSA-59g5-xgcq-4qw3，CWE-770）。

**修复**：
```txt
python-multipart>=0.0.18
```

---

### 5. aiohttp HTTP 请求走私漏洞 — `crawler/requirements.txt:5-6`

**问题**：aiohttp < 3.12.14 纯 Python 模式下存在 trailer section 解析缺陷，可绕过防火墙/代理保护（GHSA-9548-qrrj-x5pj，CWE-444）。

**修复**：
```txt
aiohttp>=3.12.14
```

---

### 6. Next.js 图片优化 DoS 漏洞 — `frontend/package.json:5-6`

**问题**：Next.js < 14.2.7 图片优化功能存在 DoS 漏洞，可导致 CPU 过载（GHSA-g77x-44xx-532m，CWE-674）。

**修复**：
```json
"next": ">=14.2.7"
```

---

### 7. 潜在 SSRF 风险 — `frontend/src/lib/api.ts:6-7` 和 `frontend/src/app/admin/page.tsx:10-11`

**问题**：API base URL 若可被外部影响，存在服务端请求伪造风险（CWE-918），攻击者可能探测内网服务或 AWS 元数据接口（169.254.169.254）。

**修复方案**：
- 确保 `NEXT_PUBLIC_API_URL` 仅在构建时通过 CI/CD 注入，不接受运行时用户输入
- 在 Next.js 配置中添加域名白名单：

```js
// next.config.js
const allowedHosts = ['api.offerhub.com', 'localhost'];

module.exports = {
  async rewrites() { /* ... */ },
  // 图片域名白名单
  images: {
    domains: allowedHosts,
  },
};
```

---

### 8. smoke_test 使用明文 HTTP — `scripts/smoke_test.py:17-18`

**问题**：测试脚本通过 `http://` 发送含认证信息的请求，凭证在网络中明文传输（CWE-319）。

**修复**：
```python
# ❌ 当前
BASE_URL = "http://localhost:8000"

# ✅ 本地测试可保留 http，但需加注释说明仅限回环地址
BASE_URL = os.getenv("SMOKE_TEST_URL", "http://localhost:8000")
# NOTE: http is acceptable only for loopback (127.0.0.1/localhost) in local dev.
# Production smoke tests must use https://.
```

---

## 🟢 建议优化（可选，下个迭代处理）

### 9. 函数扇出过高 — `backend/app/services/article_service.py:37-38`

该函数调用了 19 个其他函数（超过 98% 基准），耦合度过高，建议将 lines 54-85 的逻辑提取为独立私有方法，例如 `_build_article_response()`。

### 10. 函数扇出过高 — `crawler/spiders/rss_spider.py:22-23`

函数扇出 17，建议将 lines 32-69 的 entry 解析逻辑提取为 `_parse_entry(entry) -> dict` 独立方法，提升可测试性。

### 11. 圈复杂度过高 — `crawler/spiders/github_spider.py:22-23`

圈复杂度 16（超过 98% 基准），多层嵌套 if 难以维护。建议：
- 使用提前 return（guard clause）减少嵌套层级
- 将不同仓库类型的处理逻辑拆分为独立方法

### 12. 函数扇出过高 — `crawler/worker/view_sync.py:11-12`

函数扇出 16，建议将 Redis 读取逻辑与数据库同步逻辑拆分为两个独立函数。

### 13. 全局变量并发风险 — `scripts/smoke_test.py:30-31`

测试脚本中的全局状态在并发场景下不安全，建议改用函数参数传递或封装为测试类。

### 14. `==` 与 `is` 混用 — `scripts/seed_crawl.py:25-26`

对 `None` 的判断应使用 `is` / `is not`，而非 `==` / `!=`：
```python
# ❌
if result == None:

# ✅
if result is None:
```

---

## ✅ 做得好的地方

- 整体架构分层清晰（api → services → models → core），依赖方向正确，无跨层直接调用
- 全程使用 SQLAlchemy ORM，未发现 SQL 拼接，SQL 注入风险低
- Docker Compose 服务间通过内网通信，未暴露不必要端口
- 爬虫合规意识好：robots.txt 遵守、频率限制（≤1 req/s）、User-Agent 规范均有体现
- smoke_test 覆盖 12 个核心接口，基础回归有保障

---

## 修复优先级汇总

| 优先级 | 问题 | 文件 | 类型 |
|--------|------|------|------|
| P0 | 硬编码凭证 | `backend/app/core/config.py` | 安全 |
| P0 | python-jose JWT 漏洞 | `backend/requirements.txt` | 依赖漏洞 |
| P0 | python-jose JWT 漏洞 | `crawler/requirements.txt` | 依赖漏洞 |
| P1 | python-multipart DoS | `backend/requirements.txt` | 依赖漏洞 |
| P1 | aiohttp 请求走私 | `crawler/requirements.txt` | 依赖漏洞 |
| P1 | Next.js DoS | `frontend/package.json` | 依赖漏洞 |
| P1 | SSRF 风险确认 | `frontend/src/lib/api.ts` | 安全 |
| P1 | SSRF 风险确认 | `frontend/src/app/admin/page.tsx` | 安全 |
| P2 | smoke_test 明文 HTTP | `scripts/smoke_test.py` | 安全 |
| P3 | 函数扇出/圈复杂度 | 多处 | 代码质量 |
| P3 | 全局变量/`is` vs `==` | `scripts/` | 代码质量 |
