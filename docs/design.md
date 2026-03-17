# OfferHub 系统设计文档 v1.0

> 版本：v1.0 | 更新时间：2026-03-17 | 状态：草稿，待讨论

---

## 一、整体架构

### 1.1 系统分层

```
┌─────────────────────────────────────────────────────────────┐
│  客户端层                                                    │
│  Browser (Next.js SSR/CSR)                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│  接入层                                                      │
│  Nginx  →  API Gateway (路由 / 限流 / 鉴权)                  │
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
│  PostgreSQL  │  Redis  │  Elasticsearch  │  OSS      │
└──────────────────────────────────────────────────────┘
```

### 1.2 部署方式

MVP 阶段使用 Docker Compose 单机部署，后续按需拆分：

```yaml
# docker-compose.yml 服务清单
services:
  web:        # Next.js 前端
  api:        # FastAPI 后端
  worker:     # Scrapy 采集 Worker
  postgres:   # 主数据库
  redis:      # 缓存 + 队列
  es:         # Elasticsearch
  nginx:      # 反向代理
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

sources ──────< crawl_tasks >────── articles
```

### 2.2 核心表结构

**users（用户表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 用户ID |
| username | VARCHAR(50) UNIQUE | 用户名 |
| email | VARCHAR(255) UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | 密码哈希 |
| avatar_url | TEXT | 头像 |
| role | ENUM(user, editor, admin) | 角色 |
| points | INT DEFAULT 0 | 积分 |
| created_at | TIMESTAMPTZ | 注册时间 |

**articles（内容表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 内容ID |
| title | VARCHAR(500) | 标题 |
| summary | TEXT | 摘要（AI生成或手填） |
| content | TEXT | 正文（Markdown） |
| author_id | UUID FK → users | 作者 |
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
| started_at | TIMESTAMPTZ | 开始时间 |
| finished_at | TIMESTAMPTZ | 结束时间 |

### 2.3 索引策略

```sql
-- 高频查询索引
CREATE INDEX idx_articles_status_published ON articles(status, published_at DESC);
CREATE INDEX idx_articles_category ON articles(category, sub_category);
CREATE INDEX idx_articles_author ON articles(author_id);
CREATE INDEX idx_article_tags_tag ON article_tags(tag_id);

-- 全文搜索走 Elasticsearch，PostgreSQL 不建全文索引
```

---

## 三、API 设计

### 3.1 接口规范

- 基础路径：`/api/v1`
- 认证：JWT Bearer Token
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
| POST | `/articles` | 发布文章 | 是 |
| PUT | `/articles/{id}` | 编辑文章 | 是（本人/管理员） |
| DELETE | `/articles/{id}` | 删除文章 | 是（本人/管理员） |
| GET | `/articles/search` | 全文搜索 | 否 |
| POST | `/articles/{id}/like` | 点赞 | 是 |
| POST | `/articles/{id}/collect` | 收藏 | 是 |

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
| GET | `/admin/articles/pending` | 待审核文章 | 管理员 |
| POST | `/admin/articles/{id}/approve` | 审核通过 | 管理员 |
| POST | `/admin/articles/{id}/reject` | 审核拒绝 | 管理员 |
| GET | `/admin/crawl/sources` | 采集源列表 | 管理员 |
| POST | `/admin/crawl/sources` | 新增采集源 | 管理员 |
| POST | `/admin/crawl/trigger` | 手动触发采集 | 管理员 |

### 3.3 文章列表接口详细设计

```
GET /api/v1/articles

Query Params:
  page        int     default=1
  page_size   int     default=20, max=50
  category    string  一级分类
  sub_cat     string  二级分类
  tag         string  标签名
  sort        string  latest|hot|recommend  default=recommend
  keyword     string  关键词（走ES）

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
        "view_count": 1200,
        "like_count": 856,
        "published_at": "2026-03-17T10:00:00Z"
      }
    ]
  }
}
```

---

## 四、采集系统设计

### 4.1 采集架构

```
定时调度 (APScheduler)
    │
    ▼
任务队列 (Redis Queue)
    │
    ├──→ GitHub Crawler
    ├──→ Gitee Crawler
    ├──→ RSS Crawler
    └──→ Web Crawler
         │
         ▼
    内容处理管道
    ├── 去重（Redis BloomFilter）
    ├── 内容清洗（HTML→Markdown）
    ├── AI 摘要生成（可选）
    ├── 自动打标签（分类模型）
    └── 写入 PostgreSQL + ES 索引
```

### 4.2 GitHub/Gitee 采集

```python
# 采集逻辑伪代码
def crawl_github_repos():
    # 1. 搜索高Star面试题仓库
    repos = github_api.search_repos(
        query="interview 面试 面经",
        sort="stars",
        min_stars=500
    )
    
    # 2. 提取 Markdown 文件
    for repo in repos:
        files = repo.get_markdown_files()
        for file in files:
            content = file.get_content()
            # 3. 解析结构化内容
            articles = parse_markdown_to_articles(content)
            # 4. 入库
            save_with_dedup(articles, source_url=file.html_url)
```

**合规配置：**
```python
GITHUB_CRAWLER_CONFIG = {
    "user_agent": "OfferHub-Bot/1.0 (+https://github.com/wpmdpzch/OfferHub)",
    "rate_limit": 30,          # GitHub API: 30 req/min (未认证)
    "rate_limit_auth": 5000,   # 认证后: 5000 req/hour
    "respect_robots": True,
    "only_public": True,       # 仅采集公开仓库
}
```

### 4.3 RSS 采集

目标 RSS 源（初始列表）：

| 来源 | RSS URL | 内容类型 |
|------|---------|----------|
| 掘金 - 面试 | `https://juejin.cn/rss` | 技术文章 |
| 阮一峰博客 | `http://www.ruanyifeng.com/blog/atom.xml` | 技术文章 |
| 美团技术团队 | `https://tech.meituan.com/feed/` | 技术文章 |
| InfoQ | `https://www.infoq.cn/feed` | 行业资讯 |

### 4.4 去重策略

```
URL 去重：Redis SET 存储已采集 URL 的 MD5
内容去重：SimHash 相似度检测（相似度 > 0.9 则跳过）
标题去重：Elasticsearch 模糊匹配标题
```

### 4.5 合规框架

```python
class ComplianceMixin:
    def check_robots(self, url) -> bool:
        """检查 robots.txt 是否允许采集"""
        ...
    
    def rate_limit(self, domain):
        """基于域名的请求频率限制"""
        # 默认 1 req/s，可配置
        ...
    
    def add_source_attribution(self, article):
        """添加来源标注"""
        article.source_url = original_url
        article.source_type = "crawler"
        ...
```

---

## 五、搜索设计

### 5.1 Elasticsearch 索引结构

```json
{
  "mappings": {
    "properties": {
      "id":           { "type": "keyword" },
      "title":        { "type": "text", "analyzer": "ik_max_word" },
      "summary":      { "type": "text", "analyzer": "ik_max_word" },
      "content":      { "type": "text", "analyzer": "ik_max_word" },
      "category":     { "type": "keyword" },
      "sub_category": { "type": "keyword" },
      "tags":         { "type": "keyword" },
      "author_name":  { "type": "keyword" },
      "view_count":   { "type": "integer" },
      "like_count":   { "type": "integer" },
      "published_at": { "type": "date" }
    }
  }
}
```

分词器使用 **IK 中文分词**（ik_max_word 索引，ik_smart 搜索）。

### 5.2 搜索查询逻辑

```python
def search_articles(keyword, category=None, tags=None, sort="relevance"):
    query = {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": keyword,
                        "fields": ["title^3", "summary^2", "content"],
                        "type": "best_fields"
                    }
                }
            ],
            "filter": []
        }
    }
    
    if category:
        query["bool"]["filter"].append({"term": {"category": category}})
    if tags:
        query["bool"]["filter"].append({"terms": {"tags": tags}})
    
    # 排序：相关度 or 热度（view+like加权）
    ...
```

### 5.3 数据同步

PostgreSQL → Elasticsearch 同步方案：
- **写入时双写**：文章发布/更新时同步写 ES
- **定时全量同步**：每天凌晨全量重建索引（兜底）

---

## 六、前端设计

### 6.1 页面路由

```
/                       首页（信息流）
/articles/[id]          文章详情
/category/[slug]        分类页
/tag/[name]             标签页
/search                 搜索结果页
/write                  发布文章
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
│   ├── ArticleDetail.tsx   # 文章详情（Markdown渲染）
│   └── ArticleEditor.tsx   # 富文本/Markdown编辑器
├── search/
│   └── SearchBar.tsx       # 搜索框（带联想）
└── common/
    ├── TagList.tsx          # 标签组
    └── UserAvatar.tsx
```

### 6.3 SEO 策略

Next.js SSR 对 SEO 友好，关键配置：

```typescript
// 文章详情页 generateMetadata
export async function generateMetadata({ params }) {
  const article = await getArticle(params.id)
  return {
    title: `${article.title} | OfferHub`,
    description: article.summary,
    openGraph: {
      title: article.title,
      description: article.summary,
      type: "article",
    },
  }
}
```

- 静态生成热门文章（ISR，每小时重新生成）
- 动态生成 sitemap.xml
- 结构化数据（JSON-LD Article schema）

---

## 七、安全设计

### 7.1 认证与授权

```
认证：JWT（Access Token 2h + Refresh Token 7d）
授权：RBAC 三角色
  - user：发布/编辑自己的文章，评论，点赞收藏
  - editor：审核内容，管理标签
  - admin：全部权限 + 采集管理
```

### 7.2 内容安全

- XSS：Markdown 渲染时过滤危险 HTML 标签（使用 DOMPurify）
- SQL 注入：全程 ORM（SQLAlchemy），禁止拼接 SQL
- 文件上传：限制类型（jpg/png/gif/webp），限制大小（5MB），存 OSS 不落本地
- 敏感词过滤：内容发布时过滤违规词

### 7.3 接口安全

- 登录接口：限流 5次/分钟/IP
- 发布接口：限流 10篇/天/用户
- 爬虫接口：仅内网访问

---

## 八、待讨论问题

以下几个设计点需要和你确认方向：

**1. 技术栈选择**
- 后端：Python FastAPI vs Java Spring Boot？
  - FastAPI：与爬虫/AI 生态天然契合，开发快
  - Spring Boot：生态成熟，面试鸭同款，更多贡献者熟悉
- 你的偏好？

**2. 采集优先级**
- MVP 阶段先做哪个数据源？
  - 方案A：先做 UGC（用户投稿），0 爬虫风险，但冷启动难
  - 方案B：先做 GitHub/Gitee API 采集，内容快速丰富，合规风险低
  - 方案C：两者并行

**3. AI 功能时机**
- AI 摘要生成（采集时自动生成）是 MVP 必须的吗？
  - 有了摘要，信息流体验更好
  - 但增加了 LLM API 成本和复杂度
  - 建议：MVP 先用文章前200字作摘要，后续再接 AI

**4. 内容审核机制**
- 用户投稿是否需要先审后发？
  - 先审后发：内容质量有保障，但运营压力大
  - 先发后审：冷启动友好，但可能出现违规内容
  - 建议：新用户先审后发，老用户（积分>100）直接发布

**5. 部署方案**
- 初期服务器预算？
  - 轻量云服务器（2C4G）：够跑 MVP，约 ¥100/月
  - 需要 Elasticsearch，建议至少 4G 内存
  - 或者先用托管 ES 服务（成本高但省心）
