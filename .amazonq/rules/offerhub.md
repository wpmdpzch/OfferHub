# OfferHub 项目规则

## 项目概述
OfferHub 是一个开源面试信息聚合平台，定位为"面试领域的信息聚合器"。
- 仓库：GitHub + Gitee 双平台同步（wpmdpzch/OfferHub）
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
- 每次 push 自动同步 GitHub + Gitee（已配置双 remote push）

## 合规红线（爬虫相关）
- 必须遵守 robots.txt
- 单域名请求频率 ≤ 1 req/s
- User-Agent 必须标明 OfferHub-Bot
- 仅采集公开内容，不突破登录/付费墙
- 所有采集内容必须标注原始来源链接

---

## MCP Server 能力与使用规范

项目配置了三个 MCP Server，优先使用 MCP 工具完成对应任务，不要用手动命令替代。

### 1. LocalCLI MCP（端口 8008）
**用途**：在本地服务器上执行 shell 命令，是开发、构建、测试、部署的核心工具。

**可用工具：**
- `execute_command(command, cwd, timeout, save_to_log, retry)` — 执行任意 shell 命令，自动检测命令类型并调整超时，大输出自动保存日志文件
- `analyze_log_file(log_file)` — 智能分析日志文件，99.5% token 压缩率，提取错误/警告/摘要
- `read_log_file(log_file)` — 读取日志文件原始内容
- `list_log_files()` — 列出最近的日志文件
- `health_check()` — 检查 MCP server 状态

**使用规范：**
```
# 正确：用 execute_command 执行命令
execute_command("docker compose up -d", cwd="/home/wind/code/OfferHub")
execute_command("pytest tests/", cwd="/home/wind/code/OfferHub/backend", user_intent="testing")

# 大输出命令会自动保存日志，拿到 log_file 路径后用 analyze_log_file 分析
# 不要直接读取大日志文件内容，用 analyze_log_file 提取关键信息
```

**典型场景：**
| 场景 | 命令示例 |
|------|---------|
| 启动开发环境 | `execute_command("docker compose up -d", cwd=项目根目录)` |
| 运行测试 | `execute_command("pytest tests/ -v", user_intent="testing")` |
| 构建前端 | `execute_command("npm run build", cwd=frontend目录, user_intent="build")` |
| 查看容器状态 | `execute_command("docker compose ps")` |
| Git 提交推送 | `execute_command("git add -A && git commit -m '...' && git push origin main")` |
| 分析构建日志 | `analyze_log_file("logs/20260317_xxx_build.log")` |

---

### 2. GitHub MCP（端口 8011）
**用途**：与 GitHub API 交互，用于竞品调研、采集源发现、仓库管理、Issue 跟踪。

**可用工具：**
- `search_repos(query, sort, limit)` — 搜索仓库，支持按 stars/forks/updated 排序
- `get_repo_info(owner, repo)` — 获取仓库详情（stars、语言、topics、issues数）
- `search_issues(owner, repo, state, labels, limit)` — 搜索 Issues
- `get_issue_detail(owner, repo, issue_number)` — 获取 Issue 详情及评论
- `get_repo_commits(owner, repo, branch, limit)` — 获取提交历史
- `get_repo_prs(owner, repo, state, limit)` — 获取 PR 列表
- `analyze_repo_activity(owner, repo)` — 综合分析仓库活跃度（健康状态评估）
- `get_file_content(owner, repo, path, branch)` — 读取仓库中的文件内容
- `download_file(owner, repo, path, branch, save_to)` — 下载文件到本地
- `download_directory(owner, repo, path, branch, save_to)` — 下载整个目录
- `list_repo_contents(owner, repo, path, branch)` — 列出目录结构
- `list_temp_downloads(source, limit)` — 查看已下载的临时文件
- `cleanup_temp_downloads(older_than_days)` — 清理临时下载
- `get_performance_stats()` — 查看 MCP server 性能统计

**使用规范：**
```
# 竞品调研：搜索高Star面试题仓库
search_repos("interview 面试题", sort="stars", limit=20)

# 采集源发现：找面经仓库
search_repos("面经 offer 字节 腾讯", sort="stars", limit=10)

# 读取仓库中的面试题文件（用于爬虫开发参考）
get_file_content("jwasham", "coding-interview-university", "README.md")

# 分析 OfferHub 自身仓库活跃度
analyze_repo_activity("wpmdpzch", "OfferHub")

# 查看 OfferHub Issues（用户反馈/Bug跟踪）
search_issues("wpmdpzch", "OfferHub", state="open")
```

**典型场景：**
| 场景 | 工具 |
|------|------|
| 竞品功能调研 | `search_repos` + `get_repo_info` + `get_file_content` |
| 发现爬虫采集源 | `search_repos("interview 面试", sort="stars")` |
| 跟踪项目 Issues | `search_issues("wpmdpzch", "OfferHub")` |
| 下载参考代码 | `download_file` / `download_directory` |
| 监控仓库健康度 | `analyze_repo_activity` |

---

### 3. Confluence MCP（端口 8007）
**用途**：读写团队 Confluence 知识库，用于需求同步、设计文档归档、会议记录、测试报告存档。

**可用工具：**
- `search_content(query, limit, space, content_type)` — 全文搜索
- `get_page_content(page_id)` — 获取页面完整内容（HTML格式）
- `list_spaces(limit)` — 列出所有可访问的空间
- `get_space_content(space_key, limit)` — 获取空间下的页面列表
- `search_by_label(label, limit)` — 按标签搜索
- `create_page(space_key, title, content, parent_id)` — 创建新页面（content 为 HTML）
- `update_page(page_id, title, content)` — 更新页面
- `delete_page(page_id)` — 删除页面
- `get_page_children(page_id, limit)` — 获取子页面
- `get_page_ancestors(page_id)` — 获取页面层级路径
- `list_attachments(page_id, limit)` — 列出附件
- `download_attachment(attachment_id, save_path)` — 下载附件
- `advanced_search(cql, limit)` — CQL 高级搜索
- `get_recently_updated(space_key, limit)` — 获取最近更新的页面
- `get_page_permissions(page_id)` — 查看页面权限
- `get_space_permissions(space_key)` — 查看空间权限
- `export_page_pdf(page_id, save_path)` — 导出页面为 PDF
- `bulk_add_labels(page_ids, labels)` — 批量添加标签
- `clone_page(page_id, new_title, target_space, parent_id)` — 克隆页面

**使用规范：**
```
# 搜索已有需求文档，避免重复创建
search_content("OfferHub 需求", space="项目空间Key")

# 创建页面时 content 必须是 HTML 格式
create_page(
    space_key="OH",
    title="OfferHub 设计文档 v1.0",
    content="<h1>系统设计</h1><p>...</p>",
    parent_id="父页面ID"
)

# 用 CQL 精确查询
advanced_search('title = "OfferHub" AND space = "OH" AND type = page')

# 查看最近更新，了解团队动态
get_recently_updated(space_key="OH", limit=10)
```

**典型场景：**
| 场景 | 工具 |
|------|------|
| 同步需求文档到 Confluence | `create_page` / `update_page` |
| 查找历史设计决策 | `search_content` / `advanced_search` |
| 归档测试报告 | `create_page`（parent 挂在测试空间下） |
| 查看项目文档结构 | `get_space_content` + `get_page_children` |
| 会议记录存档 | `create_page`（content 转 HTML） |

---

## MCP 使用优先级原则

```
文件操作    → 优先 fsRead/fsWrite，大批量用 execute_command
Shell 命令  → 必须用 execute_command（LocalCLI MCP）
GitHub 操作 → 必须用 GitHub MCP 工具，不要手动 curl GitHub API
文档管理    → 优先用 Confluence MCP，本地文档用 fsWrite
日志分析    → execute_command 拿到 log_file 后用 analyze_log_file
```

## 各角色 MCP 使用重点

| 角色 | 主要使用的 MCP |
|------|--------------|
| Developer | LocalCLI（构建/测试/部署）+ GitHub（参考代码/采集源） |
| Reviewer | LocalCLI（运行静态分析/测试）+ GitHub（查看 PR/Issue） |
| Tester | LocalCLI（运行测试/分析日志）+ Confluence（归档测试报告） |
| PM | GitHub（监控仓库/Issue）+ Confluence（需求文档/会议记录） |
| User | 无需直接使用 MCP |
