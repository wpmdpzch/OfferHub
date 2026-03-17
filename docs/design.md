# OfferHub 系统设计文档 v1.1

> 版本：v1.3 | 更新时间：2026-03-17 | 状态：已定稿

---

## 一、整体架构

### 1.1 系统分层

```
┌─────────────────────────────────────────────────────────────┐
│  客户端层                                                    │
│  Browser (Next.js SSR/CSR)                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│  接入层                                                      │
│  Nginx  →  FastAPI (路由 / 限流 / 鉴权)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌────────────┐ ┌──────────────────┐
│  内容服务        │ │  用户服务   │ │  采集服务         │
│  (FastAPI)      │ │  (FastAPI) │ │  (Scrapy Worker) │
└────────┬────────┘ └─────┬──────┘ └────────┬─────────┘
         │                │                 │
┌────────▼────────────────▼─────────────────▼─────────┐
│  数据层                                               │
│  PostgreSQL（主库 + 全文搜索）  │  Redis（缓存+队列）  │
└──────────────────────────────────────────────────────┘
```

### 1.2 技术选型决策

| 层级 | 技术 | 决策理由 |
|------|------|----------|
| 前端 | Next.js 14 + TypeScript + TailwindCSS | SSR 利于 SEO，推广必备 |
| 后端 | Python FastAPI | 与爬虫/AI 生态契合，开发快 |
| 爬虫 | Scrapy + aiohttp | 异步高性能采集 |
| 数据库 | PostgreSQL | 全文搜索（pg_trgm）内置，无需额外组件 |
| 缓存/队列 | Redis | 热点缓存 + 爬虫任务队列 + URL 去重 |
| 搜索 | PostgreSQL pg_trgm | MVP 阶段够用，避免引入 ES 的运维复杂度；规模上来后可迁移 |
| 部署 | Docker Compose 单机 | 32G 内存服务器，单机足够支撑 MVP |

### 1.3 Docker Compose 服务清单

```yaml
services:
  web:        # Next.js 前端（port 3000）
  api:        # FastAPI 后端（port 8000）
  worker:     # Scrapy 采集 Worker
  postgres:   # PostgreSQL 主库（port 5432），镜像见 2.5 节
  redis:      # Redis 缓存+队列（port 6379）
  nginx:      # 反向代理（port 80/443）
```

---

## 二、数据库设计

### 2.1 ER 图（核心实体）

```
users ──────< articles >────── tags
  │                │
  │           article_tags
  │
  └──< user_behaviors (浏览/点赞/收藏) >── articles

crawl_sources ──────< crawl_tasks >────── articles
```

### 2.2 核心表结构

**users（用户表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 用户ID |
| username | VARCHAR(50) UNIQUE | 用户名 |
| email | VARCHAR(255) UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | 密码哈希（bcrypt） |
| avatar_url | TEXT | 头像 |
| role | ENUM(user, editor, admin) | 角色 |
| points | INT DEFAULT 0 | 积分 |
| created_at | TIMESTAMPTZ | 注册时间 |

**articles（内容表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 内容ID |
| title | VARCHAR(500) | 标题 |
| summary | TEXT | 摘要（正文前 200 字） |
| content | TEXT | 正文（Markdown） |
| search_vector | TSVECTOR | 全文搜索向量（自动维护） |
| author_id | UUID FK → users | 作者（采集内容为系统账号） |
| category | VARCHAR(50) | 一级分类 |
| sub_category | VARCHAR(50) | 二级分类 |
| source_type | ENUM(ugc, github, gitee, rss, crawler) | 来源类型 |
| source_url | TEXT | 原始链接 |
| source_license | VARCHAR(100) | 开源协议 |
| status | ENUM(pending, published, rejected, deleted) | 状态 |
| view_count | INT DEFAULT 0 | 浏览数 |
| like_count | INT DEFAULT 0 | 点赞数 |
| collect_count | INT DEFAULT 0 | 收藏数 |
| comment_count | INT DEFAULT 0 | 评论数 |
| published_at | TIMESTAMPTZ | 发布时间 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**tags（标签表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | 标签ID |
| name | VARCHAR(50) UNIQUE | 标签名 |
| category | VARCHAR(50) | 所属分类 |
| article_count | INT DEFAULT 0 | 关联文章数 |

**article_tags（文章-标签关联）**

| 字段 | 类型 | 说明 |
|------|------|------|
| article_id | UUID FK | 文章ID |
| tag_id | INT FK | 标签ID |

**comments（评论表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 评论ID |
| article_id | UUID FK | 文章ID |
| user_id | UUID FK | 评论者 |
| parent_id | UUID FK nullable | 父评论（回复） |
| content | TEXT | 评论内容 |
| like_count | INT DEFAULT 0 | 点赞数 |
| created_at | TIMESTAMPTZ | 创建时间 |

**crawl_sources（采集源配置表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | 源ID |
| name | VARCHAR(100) | 源名称 |
| type | ENUM(github, gitee, rss, web) | 源类型 |
| url | TEXT | 目标URL |
| enabled | BOOLEAN DEFAULT true | 是否启用 |
| crawl_interval | INT | 采集间隔（分钟） |
| last_crawled_at | TIMESTAMPTZ | 上次采集时间 |
| config | JSONB | 额外配置（headers/selectors等） |

**crawl_tasks（采集任务记录）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 任务ID |
| source_id | INT FK | 采集源 |
| status | ENUM(pending, running, done, failed) | 状态 |
| items_found | INT | 发现条目数 |
| items_saved | INT | 入库条目数 |
| error_msg | TEXT | 错误信息 |
| retry_count | INT DEFAULT 0 | 已重试次数 |
| started_at | TIMESTAMPTZ | 开始时间 |
| finished_at | TIMESTAMPTZ | 结束时间 |

**user_behaviors（用户行为记录表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL PK | 行为ID（高频写入用 BIGSERIAL） |
| user_id | UUID FK → users | 用户 |
| article_id | UUID FK → articles | 目标文章 |
| behavior | ENUM(view, like, collect, report) | 行为类型 |
| created_at | TIMESTAMPTZ DEFAULT now() | 发生时间 |

> 唯一约束：`UNIQUE(user_id, article_id, behavior)`，防止重复点赞/收藏。
> 浏览行为（view）不受唯一约束限制；点赞/收藏/举报受约束，保证幂等。
> articles 表的 `like_count`/`collect_count`/`view_count` 为冗余计数字段，通过触发器或异步任务从 user_behaviors 聚合更新，避免每次查询实时 COUNT。
> **浏览行为写入方案（已决策）**：用户浏览时写 Redis `INCR article:view:{article_id}`，异步 Worker 每 5 分钟同步到 `articles.view_count`；同时异步写入 user_behaviors（behavior='view'），用于后续 P2 个性化推荐。

**举报处理流程（已决策）**：`POST /articles/{id}/report` 写入 user_behaviors 后，将文章状态置为 `pending` 进入待审核队列，由 editor/admin 人工处理。MVP 阶段不做自动化阈值触发，不通知被举报者，举报人不可见举报内容。

**point_logs（积分流水表，P1）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 流水ID |
| user_id | UUID FK → users | 用户 |
| delta | INT | 积分变化（正数加分，负数扣分） |
| reason | VARCHAR(100) | 原因：register/publish/liked/collected/daily_login/violation |
| ref_id | UUID nullable | 关联文章/评论 ID |
| created_at | TIMESTAMPTZ DEFAULT now() | 发生时间 |

### 2.3 索引策略

```sql
-- 常规查询索引
CREATE INDEX idx_articles_status_published ON articles(status, published_at DESC);
CREATE INDEX idx_articles_category ON articles(category, sub_category);
CREATE INDEX idx_articles_author ON articles(author_id);
CREATE INDEX idx_article_tags_tag ON article_tags(tag_id);

-- 全文搜索索引（GIN，支持中文分词）
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);

-- URL 去重索引
CREATE UNIQUE INDEX idx_articles_source_url ON articles(source_url)
    WHERE source_url IS NOT NULL;

-- user_behaviors 索引
CREATE UNIQUE INDEX idx_behaviors_unique ON user_behaviors(user_id, article_id, behavior)
    WHERE behavior IN ('like', 'collect', 'report');
CREATE INDEX idx_behaviors_article ON user_behaviors(article_id, behavior);
CREATE INDEX idx_behaviors_user ON user_behaviors(user_id, behavior, created_at DESC);
```

### 2.4 全文搜索向量维护

```sql
-- 启用 zhparser 扩展（容器启动时执行一次）
CREATE EXTENSION IF NOT EXISTS zhparser;
CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);
ALTER TEXT SEARCH CONFIGURATION chinese
    ADD MAPPING FOR n, v, a, i, e, l WITH simple;

-- 自动更新 search_vector（触发器）
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('chinese', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('chinese', coalesce(NEW.summary, '')), 'B') ||
    setweight(to_tsvector('chinese', coalesce(NEW.content, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER articles_search_vector_update
  BEFORE INSERT OR UPDATE ON articles
  FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

### 2.5 PostgreSQL 镜像选型

**决策：使用 `abcfy2/zhparser` 作为基础镜像。**

| 方案 | 镜像 | 说明 |
|------|------|------|
| ✅ 选用 | `abcfy2/zhparser:14` | 基于 PostgreSQL 14，预装 zhparser + SCWS 分词词典，开箱即用 |
| 备选 | 官方镜像 + 手动编译 | 需要在 Dockerfile 中编译 zhparser，构建时间长，维护成本高 |
| 放弃 | pg_jieba | 依赖 jieba C++ 库，Docker 镜像更难维护，社区活跃度低于 zhparser |

```yaml
# docker-compose.yml 中 postgres 服务
postgres:
  image: abcfy2/zhparser:14
  environment:
    POSTGRES_DB: offerhub
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
```

> `init.sql` 在容器首次启动时自动执行，负责创建扩展、配置分词器、建表、建索引。

---

## 三、API 设计

### 3.1 接口规范

- 基础路径：`/api/v1`
- 认证：JWT Bearer Token（Access Token 2h + Refresh Token 7d）
- 响应格式：
```json
{
  "code": 0,
  "msg": "ok",
  "data": {}
}
```
- 错误码：`0` 成功，`4xx` 客户端错误，`5xx` 服务端错误

### 3.2 核心接口列表

**内容接口**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/articles` | 文章列表（分页+筛选） | 否 |
| GET | `/articles/{id}` | 文章详情 | 否 |
| POST | `/articles` | 发布文章（UGC） | 是 |
| PUT | `/articles/{id}` | 编辑文章 | 是（本人/管理员） |
| DELETE | `/articles/{id}` | 删除文章 | 是（本人/管理员） |
| GET | `/search` | 全文搜索（zhparser + pg_trgm） | 否 |
| POST | `/articles/{id}/like` | 点赞（幂等） | 是 |
| DELETE | `/articles/{id}/like` | 取消点赞 | 是 |
| POST | `/articles/{id}/collect` | 收藏（幂等） | 是 |
| DELETE | `/articles/{id}/collect` | 取消收藏 | 是 |
| POST | `/articles/{id}/report` | 举报 | 是 |

**用户接口**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/auth/register` | 注册 | 否 |
| POST | `/auth/login` | 登录 | 否 |
| POST | `/auth/refresh` | 刷新Token | 是 |
| GET | `/users/me` | 当前用户信息 | 是 |
| PUT | `/users/me` | 更新个人信息 | 是 |
| GET | `/users/{id}/articles` | 用户发布的文章 | 否 |

**评论接口**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/articles/{id}/comments` | 评论列表 | 否 |
| POST | `/articles/{id}/comments` | 发表评论 | 是 |
| DELETE | `/comments/{id}` | 删除评论 | 是 |

**管理接口**

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/admin/articles/pending` | 待审核文章 | editor/admin |
| POST | `/admin/articles/{id}/approve` | 审核通过 | editor/admin |
| POST | `/admin/articles/{id}/reject` | 审核拒绝 | editor/admin |
| GET | `/admin/tags` | 标签列表管理 | editor/admin |
| POST | `/admin/tags` | 新增标签 | editor/admin |
| DELETE | `/admin/tags/{id}` | 删除标签 | editor/admin |
| GET | `/admin/crawl/sources` | 采集源列表 | admin |
| POST | `/admin/crawl/sources` | 新增采集源 | admin |
| POST | `/admin/crawl/trigger` | 手动触发采集 | admin |

### 3.3 文章列表接口详细设计

```
GET /api/v1/articles

Query Params:
  page        int     default=1
  page_size   int     default=20, max=50
  category    string  一级分类
  sub_cat     string  二级分类
  tag         string  标签名
  sort        string  latest|hot|recommend  default=latest
  keyword     string  关键词（标题 LIKE 过滤，非全文检索；全文检索请用 GET /search）

Response:
{
  "code": 0,
  "data": {
    "total": 1000,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "...",
        "title": "...",
        "summary": "...",
        "category": "面经分享",
        "tags": ["前端", "字节"],
        "author": { "id": "...", "username": "张三", "avatar": "..." },
        "source_url": "https://...",
        "view_count": 1200,
        "like_count": 856,
        "published_at": "2026-03-17T10:00:00Z"
      }
    ]
  }
}
```

### 3.4 文章详情接口响应体

```
GET /api/v1/articles/{id}

Response:
{
  "code": 0,
  "data": {
    "id": "...",
    "title": "...",
    "content": "...",        // Markdown 全文
    "summary": "...",
    "category": "面经分享",
    "sub_category": "大厂",
    "tags": ["前端", "字节"],
    "author": { "id": "...", "username": "张三", "avatar": "..." },
    "source_url": "https://...",
    "source_type": "ugc",
    "source_license": "MIT",
    "view_count": 1200,
    "like_count": 856,
    "collect_count": 120,
    "comment_count": 34,
    "viewer_liked": false,      // 当前登录用户是否已点赞（未登录为 null）
    "viewer_collected": false,  // 当前登录用户是否已收藏（未登录为 null）
    "published_at": "2026-03-17T10:00:00Z",
    "updated_at": "2026-03-17T12:00:00Z"
  }
}
```

### 3.5 搜索接口详细设计

```
GET /api/v1/search

Query Params:
  q           string  必填，搜索关键词
  page        int     default=1
  page_size   int     default=20, max=50
  category    string  可选，一级分类过滤
  tag         string  可选，标签过滤

Response: 同文章列表接口，items 额外包含 highlight 字段
{
  "code": 0,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        ...文章列表字段...,
        "highlight": "...命中关键词的<em>摘要片段</em>..."
      }
    ]
  }
}
```

搜索策略：优先 tsvector 全文检索（zhparser 中文分词），无结果时降级到 pg_trgm 模糊匹配兜底。

---

## 四、采集系统设计

### 4.1 采集架构

```
定时调度 (APScheduler)
    │
    ▼
任务队列 (Redis List)
    │
    ├──→ GitHub Crawler（GitHub MCP API）
    ├──→ Gitee Crawler（Gitee API）
    ├──→ RSS Crawler（feedparser）
    └──→ Web Crawler（Scrapy，谨慎使用）
         │
         ▼
    内容处理管道
    ├── URL 去重（Redis SET + DB UNIQUE 索引）
    ├── 内容清洗（HTML → Markdown）
    ├── 摘要提取（正文前 200 字）
    ├── 自动分类打标（关键词匹配规则）
    └── 写入 PostgreSQL（触发器自动更新 search_vector）
```

### 4.2 GitHub/Gitee 采集

```python
# 采集逻辑（利用 GitHub MCP 工具）
async def crawl_github_interview_repos():
    # 1. 搜索高 Star 面试题仓库
    repos = await github_mcp.search_repos(
        query="interview 面试 面经",
        sort="stars",
        limit=50
    )

    for repo in repos:
        if repo["stars"] < 500:
            continue
        # 2. 列出仓库 Markdown 文件
        contents = await github_mcp.list_repo_contents(
            repo["owner"], repo["name"]
        )
        # 3. 提取并解析内容
        for file in contents["files"]:
            if file["name"].endswith(".md"):
                content = await github_mcp.get_file_content(
                    repo["owner"], repo["name"], file["path"]
                )
                await save_article(content, source=repo["url"])
```

**合规配置：**
```python
CRAWLER_CONFIG = {
    "user_agent": "OfferHub-Bot/1.0 (+https://github.com/wpmdpzch/OfferHub)",
    "github_rate_limit": 5000,   # 认证后 5000 req/hour
    "web_rate_limit": 1,         # 普通网站 1 req/s
    "random_delay": (1, 3),      # 随机延迟秒数
    "respect_robots": True,
    "only_public": True,
}
```

### 4.3 RSS 采集源（初始列表）

| 来源 | RSS URL | 内容类型 |
|------|---------|----------|
| 掘金 | `https://juejin.cn/rss` | 技术文章 |
| 阮一峰博客 | `http://www.ruanyifeng.com/blog/atom.xml` | 技术文章 |
| 美团技术团队 | `https://tech.meituan.com/feed/` | 技术文章 |
| InfoQ | `https://www.infoq.cn/feed` | 行业资讯 |

### 4.4 去重策略

```
1. URL 去重：articles 表 source_url 唯一索引，插入时自动拦截
2. 内容去重：SimHash 相似度检测（相似度 > 0.9 跳过）
3. Redis 布隆过滤器：采集前快速预判，减少 DB 查询
```

### 4.5 合规框架

```python
class ComplianceMixin:
    async def check_robots(self, url: str) -> bool:
        """检查 robots.txt 是否允许采集"""
        ...

    async def rate_limit(self, domain: str):
        """基于域名的请求频率限制（Redis 令牌桶）"""
        ...

    def add_attribution(self, article: dict) -> dict:
        """添加来源标注，确保原始链接可追溯"""
        article["source_url"] = self.original_url
        return article
```

---

## 五、搜索设计

### 5.1 方案选择

MVP 阶段使用 **PostgreSQL 内置全文搜索**（pg_trgm + tsvector），不引入 Elasticsearch。

理由：
- 32G 单机部署，减少服务数量降低运维复杂度
- pg_trgm 支持模糊匹配，tsvector 支持权重排序，满足 MVP 需求
- 数据量达到百万级或搜索体验明显不足时，再迁移到 ES

### 5.2 搜索查询实现

```python
async def search_articles(
    keyword: str,
    category: str = None,
    tags: list = None,
    page: int = 1,
    page_size: int = 20
):
    # 主路径：zhparser 中文全文搜索（tsvector）
    query = """
        SELECT *, ts_rank(search_vector, query) AS rank
        FROM articles, plainto_tsquery('chinese', :keyword) query
        WHERE search_vector @@ query
          AND status = 'published'
        ORDER BY rank DESC
        LIMIT :limit OFFSET :offset
    """
    # 降级兜底：pg_trgm 模糊匹配（处理英文/拼写错误/部分匹配）
    fallback_query = """
        SELECT * FROM articles
        WHERE title % :keyword AND status = 'published'
        ORDER BY similarity(title, :keyword) DESC
        LIMIT :limit OFFSET :offset
    """
```

### 5.3 搜索性能预期

| 数据量 | 查询响应时间（预估） |
|--------|---------------------|
| 1 万篇 | < 50ms |
| 10 万篇 | < 200ms |
| 100 万篇 | 考虑迁移 ES |

---

## 六、前端设计

### 6.1 页面路由

```
/                       首页（信息流）
/articles/[id]          文章详情
/category/[slug]        分类页
/tag/[name]             标签页
/search                 搜索结果页
/write                  发布文章（UGC）
/user/[id]              用户主页
/me                     个人中心
/me/articles            我的文章
/me/collections         我的收藏
/admin                  管理后台（管理员）
/admin/review           内容审核
/admin/crawl            采集管理
```

### 6.2 核心组件

```
components/
├── layout/
│   ├── Header.tsx          # 顶部导航（搜索框、登录入口）
│   ├── Sidebar.tsx         # 左侧分类筛选
│   └── Footer.tsx
├── article/
│   ├── ArticleCard.tsx     # 信息流卡片
│   ├── ArticleList.tsx     # 无限滚动列表
│   ├── ArticleDetail.tsx   # 文章详情（Markdown 渲染）
│   └── ArticleEditor.tsx   # Markdown 编辑器
├── search/
│   └── SearchBar.tsx       # 搜索框（带联想）
└── common/
    ├── TagList.tsx
    └── UserAvatar.tsx
```

### 6.3 SEO 策略

- Next.js SSR：文章详情页服务端渲染，对搜索引擎友好
- ISR：热门文章每小时重新生成静态页
- 动态生成 sitemap.xml
- 结构化数据（JSON-LD Article schema）

```typescript
export async function generateMetadata({ params }) {
  const article = await getArticle(params.id)
  return {
    title: `${article.title} | OfferHub`,
    description: article.summary,
    openGraph: { title: article.title, description: article.summary, type: "article" },
  }
}
```

---

## 七、安全设计

### 7.1 认证与授权

```
认证：JWT（Access Token 2h + Refresh Token 7d）
授权：RBAC 三角色
  - user：发布/编辑自己的文章，评论，点赞/取消点赞，收藏/取消收藏，举报
  - editor：user 全部权限 + 审核内容 + 管理标签
  - admin：全部权限 + 采集管理 + 用户管理
```

**Refresh Token 存储与吊销：**

- Refresh Token 存储在 Redis，key 为 `refresh_token:{user_id}:{jti}`，TTL 7天
- 用户登出时删除对应 Redis key，实现即时吊销
- 用户修改密码时删除该用户所有 `refresh_token:{user_id}:*`，强制全端重新登录
- Access Token 无状态，依赖短过期时间（2h）自然失效；如需提前吊销，维护 Redis 黑名单 `token_blacklist:{jti}`

### 7.2 内容安全

- XSS：Markdown 渲染时过滤危险 HTML 标签（DOMPurify）
- SQL 注入：全程 ORM（SQLAlchemy），禁止拼接 SQL
- 文件上传：MVP 阶段不支持，后续限制类型（jpg/png/gif/webp）和大小（5MB）
- 敏感词过滤：内容发布时过滤违规词

### 7.3 接口安全

- 登录接口：限流 5 次/分钟/IP
- 发布接口：限流 10 篇/天/用户
- 评论接口：限流 20 条/天/用户
- 采集管理接口：仅内网或管理员访问

---

## 八、待决策事项

| 事项 | 当前状态 | 说明 |
|------|----------|------|
| 图片/附件存储 | **已决策：暂不支持** | MVP 阶段不支持用户上传图片/附件；采集内容中的图片直接引用原始 URL |
| 中文分词扩展 | **已决策：zhparser** | 使用 `abcfy2/zhparser:14` 镜像，见 2.5 节 |
| UGC 审核机制 | 已定 | 新用户先审后发，积分 > 100 免审 |
| AI 摘要 | 后置 | MVP 用正文前 200 字，后续接 LLM API |
| 搜索升级时机 | 后置 | 内容量超 100 万或搜索体验明显不足时迁移 ES |
| 积分规则 | **已定** | 见下方积分体系说明 |
| point_logs 表 | **P1 纳入** | 积分流水表，见 2.2 节 |
| 浏览行为写入 | **已决策** | Redis INCR + 异步 Worker 落库，见 2.2 节 user_behaviors 说明 |
| 种子采集方式 | **已决策** | 独立 `scripts/seed_crawl.py` 脚本，一次性执行，不走 APScheduler |
| 评论点赞 | 后置 P2 | user_behaviors 后续扩展 target_type 字段区分 article/comment |

### 积分体系

| 行为 | 积分变化 | 说明 |
|------|----------|------|
| 注册 | +10 | 一次性 |
| 发布文章（审核通过） | +5 | 每篇 |
| 文章被点赞 | +1 | 每次，上限 50/篇 |
| 文章被收藏 | +2 | 每次，上限 20/篇 |
| 每日登录 | +1 | 每天首次 |
| 文章被举报并核实违规 | -10 | 扣分 |

积分 > 100 的用户发布文章免审核（直接 published 状态）。积分存储在 users.points，变更通过后端服务异步写入，不在请求链路中同步计算。
