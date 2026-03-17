# OfferHub

> 🚀 开源面试备战平台 | 聚合全网面试题 · AI 智能陪练 · 社区互动

聚合 GitHub/Gitee/RSS 等多源面试信息，AI 智能陪练分析，帮你消除面试焦虑。求职者刷题备战，开源免费，持续更新，让每个开发者都能拿到心仪 Offer！

[![License](https://img.shields.io/github/license/wpmdpzch/OfferHub)](LICENSE)

---

## 🔥 核心功能

- **智能题库** — 聚合 GitHub/Gitee 高 Star 面试题仓库 + RSS 技术博客，自动入库
- **全文搜索** — PostgreSQL + zhparser 中文分词，毫秒级检索
- **面经分享** — UGC 投稿，积分激励，先审后发
- **内容审核** — editor/admin 双角色审核体系
- **AI 面试陪练** — （规划中，P2）

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14 + TypeScript + TailwindCSS |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | PostgreSQL 14 (abcfy2/zhparser) + Redis 7 |
| 采集 | aiohttp + feedparser (RSS) + GitHub API |
| 部署 | Docker Compose 单机 |

---

## 🚀 快速启动

```bash
# 1. 克隆仓库
git clone https://github.com/wpmdpzch/OfferHub.git
cd OfferHub

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，修改数据库密码和 JWT_SECRET_KEY

# 3. 启动服务
docker-compose up -d postgres redis
docker-compose up -d api worker

# 4. 预采集种子内容（首次运行）
docker-compose exec worker python scripts/seed_crawl.py

# 5. 访问
# API 文档：http://localhost:8000/api/docs
# 前端：http://localhost:3000（需先 build frontend）
```

---

## 📁 项目结构

```
OfferHub/
├── backend/               # FastAPI 后端
│   └── app/
│       ├── api/v1/        # 路由层
│       ├── services/      # 业务逻辑 + Pydantic schemas
│       ├── models/        # SQLAlchemy ORM 模型
│       └── core/          # 配置 / JWT / Redis / 依赖注入
├── crawler/               # 采集服务
│   ├── spiders/           # RSS / GitHub 采集器
│   └── worker/            # 任务队列消费 + view 计数同步
├── frontend/              # Next.js 14 前端
│   └── src/
│       ├── app/           # App Router 页面
│       ├── components/    # 组件库
│       └── lib/           # API 客户端
├── scripts/
│   ├── init.sql           # 数据库初始化（建表/索引/触发器）
│   ├── seed_crawl.py      # 种子内容预采集（一次性）
│   └── smoke_test.py      # API 冒烟测试
├── nginx/                 # Nginx 反向代理配置
├── docs/
│   ├── requirements.md    # 需求文档 v5.0
│   └── design.md          # 系统设计文档 v1.3
└── docker-compose.yml
```

---

## 📊 开发进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| Week 1-2 | 基础设施：目录结构 / Docker Compose / PostgreSQL init.sql / Nginx | ✅ 完成 |
| Week 3-4 | 后端 API：用户注册登录 / 文章 CRUD / 搜索 / 评论 / 管理接口 / 采集 Worker | ✅ 完成，12/12 smoke tests 通过 |
| Week 5-6 | 前端展示：信息流 / 文章详情 / 搜索页 / 分类标签页 | 🔄 进行中 |
| Week 7-8 | 管理后台 / UGC 投稿 / SEO 优化 | ⏳ 待开始 |
| Week 9-10 | 内测 / Bug 修复 / 种子内容采集 | ⏳ 待开始 |

---

## 📋 API 文档

服务启动后访问：`http://localhost:8000/api/docs`

核心接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录 |
| GET | `/api/v1/articles` | 文章列表（分页/筛选） |
| GET | `/api/v1/articles/{id}` | 文章详情 |
| GET | `/api/v1/search?q=关键词` | 全文搜索 |
| POST | `/api/v1/articles` | 发布文章（需登录） |

---

## ⚠️ 合规说明

- 仅采集公开免费内容，严格遵守 robots.txt
- 请求频率 ≤ 1 req/s，User-Agent 标明 `OfferHub-Bot/1.0`
- 所有采集内容标注原始来源链接
- 内容删除投诉：请提 [GitHub Issue](https://github.com/wpmdpzch/OfferHub/issues)

---

## 🤝 贡献

欢迎 PR 和 Issue！详见 [CONTRIBUTING.md](CONTRIBUTING.md)（规划中）

---

*#interview #AI #opensource #career #developer*
