# Contributing to OfferHub

🎯 我们的目标：让每个开发者都能拿到心仪 Offer。

感谢你愿意为 OfferHub 贡献力量！本指南会帮助你快速上手。

---

## 快速开始

### 1. 克隆并启动

```bash
git clone https://github.com/wpmdpzch/OfferHub.git
cd OfferHub

# 复制环境变量
cp .env.example .env
# 编辑 .env，填写 JWT_SECRET_KEY 和数据库密码

# 启动基础设施服务
docker-compose up -d postgres redis

# 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 启动前端（新开终端）
cd frontend
npm install
npm run dev
```

### 2. 创建你的分支

```bash
git checkout -b feature/your-feature-name
# 或修复 bug：
git checkout -b fix/description-of-bug
```

---

## 项目结构概览

```
OfferHub/
├── backend/           # FastAPI 后端 (Python)
│   └── app/
│       ├── api/v1/    # API 路由
│       ├── services/  # 业务逻辑 + Pydantic schemas
│       ├── models/    # SQLAlchemy ORM 模型
│       └── core/      # 配置、认证、数据库连接
├── frontend/          # Next.js 14 前端 (TypeScript)
│   └── src/
│       ├── app/       # App Router 页面
│       └── components/# UI 组件
├── crawler/           # 数据采集服务 (Python)
│   ├── spiders/       # RSS / GitHub 采集器
│   └── worker/        # 任务队列消费者
├── scripts/           # 工具脚本
│   ├── init.sql       # 数据库初始化
│   ├── seed_crawl.py  # 种子内容采集
│   └── smoke_test.py  # API 冒烟测试
└── docs/              # 设计文档
```

---

## 代码规范

### Backend (Python)

- 使用 `async/await` 异步风格
- 所有 API 响应通过 `app/core/response.py` 的 `Response` 封装
- Pydantic schema 放在 `services/schemas_*.py`
- 业务逻辑放在 `services/*_service.py`
- 禁止 SQL 拼接，使用 SQLAlchemy ORM
- 数据库敏感配置必须通过环境变量，禁止硬编码

### Frontend (TypeScript/React)

- 使用 TypeScript，类型定义放在 `src/types/index.ts`
- 组件使用函数式组件 + hooks
- API 调用通过 `src/lib/api.ts` 封装
- 样式使用 TailwindCSS
- 页面组件放在 `src/app/[page]/page.tsx`
- 可复用组件放在 `src/components/`

### Commit 规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构（不影响功能）
perf: 性能优化
test: 测试相关
chore: 构建/工具变更
```

### Pull Request 规范

1. PR 标题清晰描述改动（如 `feat: add GitHub Actions CI/CD`）
2. Description 中说明：
   - 这个 PR 做了什么
   - 解决了什么问题（关联 Issue）
   - 如何测试
3. 确保 CI 通过后再合并
4. 一个 PR 只做一件事

---

## 测试

### Backend

```bash
cd backend
# 启动服务后运行冒烟测试
python ../scripts/smoke_test.py
```

### Frontend

```bash
cd frontend
npm run build   # 构建验证
npm run lint    # 代码检查
```

---

## 报告 Bug

请使用 [Bug Report 模板](./.github/ISSUE_TEMPLATE/bug_report.yml) 提交，务必包含：

- 复现步骤
- 预期行为 vs 实际行为
- 环境信息（操作系统、Python/Node 版本等）
- 日志/截图

---

## 功能建议

欢迎提交功能请求！请使用 [Feature Request 模板](./.github/ISSUE_TEMPLATE/feature_request.yml)。

描述清楚：
- 这个功能解决什么问题
- 你的使用场景是什么
- 你认为的合理实现方式（可选）

---

## 行为准则

- 保持友好和尊重
- 对新人耐心
- 技术讨论基于事实和代码
- Issues 和 PRs 会尽快回复（通常 48 小时内）

---

## 许可证

参与本项目意味着你同意你的贡献遵循 [MIT License](../LICENSE)。

有问题？可以在 [GitHub Discussions](https://github.com/wpmdpzch/OfferHub/discussions) 提问。
