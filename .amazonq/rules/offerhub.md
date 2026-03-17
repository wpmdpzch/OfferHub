# OfferHub 项目规则

## 项目概述
OfferHub 是一个开源面试信息聚合平台，定位为"面试领域的信息聚合器"。
- 仓库：GitHub + Gitee 双平台同步
- 部署：单机 Docker Compose（32G 内存服务器）
- 文档：docs/requirements.md（需求）、docs/design.md（设计）

## 语言规范
- 所有对话、注释、文档：中文
- 代码、变量名、函数名、文件名、Git commit：英文

## 技术栈
- 前端：Next.js 14 + React + TypeScript + TailwindCSS
- 后端：Python FastAPI
- 采集：Scrapy + aiohttp
- 数据库：PostgreSQL + Redis + Elasticsearch
- 部署：Docker Compose
- AI：LLM API（多模型切换）

## 项目结构
```
OfferHub/
├── frontend/          # Next.js 前端
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/       # 路由层
│   │   ├── services/  # 业务逻辑层
│   │   ├── models/    # 数据模型
│   │   └── core/      # 配置/工具
│   └── tests/
├── crawler/           # Scrapy 采集服务
├── docs/              # 文档
├── scripts/           # 运维脚本
└── docker-compose.yml
```

## Git 规范
- commit 格式：`type(scope): description`
- type：feat / fix / docs / refactor / test / chore
- 示例：`feat(crawler): add github repo crawler`
- 每次 push 自动同步 GitHub + Gitee

## 合规红线（爬虫相关）
- 必须遵守 robots.txt
- 单域名请求频率 ≤ 1 req/s
- User-Agent 必须标明 OfferHub-Bot
- 仅采集公开内容，不突破登录/付费墙
- 所有采集内容必须标注原始来源链接
