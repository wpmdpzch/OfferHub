# OfferHub

> 🚀 开源面试备战平台 | 聚合全网面试题 · AI 智能陪练 · 社区互动

[![GitHub stars](https://img.shields.io/github/stars/wpmdpzch/OfferHub?style=social)](https://github.com/wpmdpzch/OfferHub)
[![License: MIT](https://img.shields.io/github/license/wpmdpzch/OfferHub)](LICENSE)
[![Backend Test](https://img.shields.io/github/actions/workflow/status/wpmdpzch/OfferHub/backend-test.yml?label=Backend%20Test)](.github/workflows/backend-test.yml)
[![Frontend Build](https://img.shields.io/github/actions/workflow/status/wpmdpzch/OfferHub/frontend-build.yml?label=Frontend%20Build)](.github/workflows/frontend-build.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)](https://fastapi.tiangolo.com/)

[Demo](https://offerhub.vercel.app) · [在线文档](#) · [贡献指南](CONTRIBUTING.md) · [Discussions](https://github.com/wpmdpzch/OfferHub/discussions)

---

## ✨ 为什么选择 OfferHub？

| 痛点 | OfferHub 解决方式 |
|------|-------------------|
| 面经散落在牛客/知乎/掘金/公众号，找起来费劲 | 🔍 **多源聚合**：GitHub/Gitee 高 Star 仓库 + RSS 技术博客，自动采集入库 |
| 搜索结果质量参差不齐，重复内容多 | 🏆 **精选内容**：只聚合高质量开源面试题，拒绝低质爬虫内容 |
| 面试趋势变化快，旧面经参考价值低 | ⚡ **持续更新**：RSS + GitHub API 自动追踪，热门内容第一时间入库 |
| 想刷题但不知道从哪开始 | 🎯 **智能分类**：按公司/技术栈/难度分层，随时找到适合你的题目 |

---

## 🎯 核心功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 智能题库聚合 | ✅ 可用 | GitHub/Gitee API + RSS 自动采集 |
| 全文搜索 | ✅ 可用 | PostgreSQL zhparser 中文分词，毫秒级检索 |
| 面经分享 (UGC) | ✅ 可用 | 投稿入口、积分激励、先审后发 |
| 用户系统 | ✅ 可用 | 注册/登录/JWT 认证 |
| 评论互动 | ✅ 可用 | 点赞/收藏/评论/举报 |
| AI 面试陪练 | 🔨 规划中 | P2 阶段实现 |
| 题库组卷 | 🔨 规划中 | P2 阶段实现 |

---

## 📸 产品截图

> 快速预览 OfferHub 的核心界面

| 首页信息流 | 搜索结果 |
|:---:|:---:|
| ![Home](docs/screenshots/home.png) | ![Search](docs/screenshots/search.png) |

| 文章详情 | 写文章 |
|:---:|:---:|
| ![Article](docs/screenshots/article.png) | ![Write](docs/screenshots/write.png) |

---

## 🛠 技术栈

| 层级 | 技术 | 选择理由 |
|------|------|----------|
| 前端 | Next.js 14 + TypeScript + TailwindCSS | SSR 利于 SEO，App Router 现代架构 |
| 后端 | Python FastAPI + SQLAlchemy | 与爬虫/AI 生态契合，异步高性能 |
| 数据库 | PostgreSQL 14 + zhparser | 全文搜索内置，中文分词开箱即用 |
| 缓存/队列 | Redis 7 | 热点缓存 + 爬虫任务队列 + URL 去重 |
| 采集 | aiohttp + feedparser + GitHub API | 异步高效，支持多源采集 |
| 部署 | Docker Compose | 一键启动，单机即可支撑 MVP |

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐，3 分钟跑起来）

```bash
# 1. 克隆
git clone https://github.com/wpmdpzch/OfferHub.git
cd OfferHub

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，修改以下必填项：
#   POSTGRES_PASSWORD=your_secure_password
#   JWT_SECRET_KEY=your_secure_jwt_secret

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化数据库并采集种子内容
docker-compose exec worker python scripts/seed_crawl.py

# 5. 访问
# 前端：http://localhost:3000
# API 文档：http://localhost:8000/api/docs
```

### 方式二：本地开发

```bash
# 前置条件：Python 3.11+ / Node.js 20+ / PostgreSQL 14 / Redis 7

# 克隆
git clone https://github.com/wpmdpzch/OfferHub.git
cd OfferHub

# 后端
cd backend
pip install -r requirements.txt
cp ../.env.example .env  # 填写 JWT_SECRET_KEY 和数据库密码
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

---

## 📁 项目结构

```
OfferHub/
├── backend/               # FastAPI 后端
│   └── app/
│       ├── api/v1/        # API 路由层
│       ├── services/      # 业务逻辑 + Pydantic schemas
│       ├── models/        # SQLAlchemy ORM 模型
│       └── core/          # 配置 / JWT / Redis / 依赖注入
├── frontend/              # Next.js 14 前端
│   └── src/
│       ├── app/           # App Router 页面
│       ├── components/    # UI 组件
│       └── lib/           # API 客户端
├── crawler/               # 采集服务
│   ├── spiders/           # RSS / GitHub 采集器
│   └── worker/            # 任务队列消费 + 浏览计数同步
├── scripts/
│   ├── init.sql           # 数据库初始化（建表/索引/触发器）
│   ├── seed_crawl.py      # 种子内容预采集
│   └── smoke_test.py      # API 冒烟测试
└── docs/
    ├── requirements.md    # 需求文档
    └── design.md          # 系统设计文档
```

---

## 🤝 贡献

欢迎 PR 和 Issue！

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何本地开发、提交 PR 和报告 Bug。

快速链接：
- 🐛 [报告 Bug](.github/ISSUE_TEMPLATE/bug_report.yml)
- 💡 [功能建议](.github/ISSUE_TEMPLATE/feature_request.yml)
- 💬 [讨论区](https://github.com/wpmdpzch/OfferHub/discussions)

---

## 📈 发展路线图

```
当前阶段：MVP 完成 (v1.0)
│
├── v1.1 (进行中)
│   └── 开源基础设施完善：CI/CD、测试覆盖、贡献指南
│
├── v1.2
│   └── 采集系统增强：更多 RSS 源、GitHub 仓库自动发现
│
├── v2.0
│   └── AI 面试陪练：模拟面试、答案评估
│
└── v3.0
    └── 题库组卷：分类题库、在线答题、评分
```

---

## ⚠️ 合规说明

- 仅采集公开免费内容，严格遵守 robots.txt
- 请求频率 ≤ 1 req/s，User-Agent 标明 `OfferHub-Bot/1.0`
- 所有采集内容标注原始来源链接
- 内容删除投诉：请提 [GitHub Issue](https://github.com/wpmdpzch/OfferHub/issues)

---

## 📄 License

MIT © wpmdpzch

---

⭐ 如果这个项目对你有帮助，请点一个 Star！你的支持是我持续维护的动力。
