# OfferHub PM 决策反馈（PM → 开发）

> 作者：PM
> 日期：2026-03-17
> 基于：design_feedback.md（开发 → PM）
> 状态：全部决策已完成，开发可直接按此执行

---

## 一、P0 决策（立即生效，影响开发启动）

### 决策 1：举报处理流程

**结论：按开发建议执行**

- 举报后文章进入 `pending` 待审核队列
- 由 editor/admin 人工审核处理
- MVP 阶段不做自动化（无阈值触发、无自动下架）
- 不通知被举报者
- 举报人不可见举报内容（防恶意举报）

**对应接口**：`POST /articles/{id}/report` 已确认纳入设计，behavior = 'report' 写入 user_behaviors。

---

### 决策 2：搜索 keyword 必填

**结论：keyword 必填**

- `GET /search` 接口 keyword 为必填参数
- 用户进入搜索页未输入关键词时，前端展示引导提示，不调用搜索接口
- 空状态展示热门标签供用户快速跳转，不走搜索逻辑

---

## 二、P1 决策

### 决策 3：积分明细记录纳入 P1

**结论：point_logs 表纳入 P1**

理由：积分是 UGC 激励核心机制，用户看不到积分来源会影响信任感，成本低但体验收益高。

**积分规则（已确认）：**

| 行为 | 积分变化 |
|------|---------|
| 注册 | +10 |
| 发布文章 | +5 |
| 文章被点赞 | +1 |
| 文章被收藏 | +2 |
| 每日登录 | +1 |
| 违规处理 | -10 |

**积分 > 100 免审**，新用户先审后发。

**需补充的表结构（point_logs）：**

```sql
CREATE TABLE point_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    delta       INT NOT NULL,          -- 正数加分，负数扣分
    reason      VARCHAR(100) NOT NULL, -- 'register'/'publish'/'liked'/'collected'/'daily_login'/'violation'
    ref_id      UUID,                  -- 关联的文章/评论 ID（可为空）
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_point_logs_user ON point_logs(user_id, created_at DESC);
```

---

### 决策 4：评论点赞不在 P1 范围

**结论：评论点赞后置 P2**

- P1 互动功能范围：文章点赞、文章收藏、评论（发布/删除）
- 评论点赞不在 P1，后置 P2
- 开发预留方案确认：user_behaviors 后续扩展时增加 `target_type` 字段（article/comment），当前 MVP 只关联 article_id 即可

---

## 三、风险决策

### 决策 5：浏览行为写入方案

**结论：方案 A — view 先写 Redis，异步批量落库**

理由：保留完整浏览历史，支撑后续 P2 个性化推荐；纯计数方案会丢失数据，得不偿失。

**实现要求：**
- 用户每次浏览文章，写入 Redis：`INCR article:view:{article_id}`
- 异步 Worker 每 5 分钟将 Redis 计数同步到 `articles.view_count`
- user_behaviors 表记录浏览行为（behavior = 'view'），用于后续推荐
- **此方案影响表结构，请在 Week 5 后端开发前确认实现细节**

---

## 四、P2 决策（知会，无需立即处理）

### 决策 6：DMCA 删除通道

**结论：MVP 用邮件/GitHub Issue 接收投诉，admin 手动处理**

- 在 README 和页面底部注明投诉邮箱
- admin 收到投诉后手动执行删除
- 不开发专门接口，P2 阶段视情况补充

### 决策 7：采集重试策略

**结论：按开发建议直接实现**

- 最多重试 3 次
- 间隔：5 分钟 → 15 分钟 → 30 分钟（指数退避）
- retry_count 字段已确认纳入 crawl_tasks 表

---

## 五、文档不一致修正

| 项目 | 修正结果 |
|------|---------|
| 排期描述"URL MD5"→ 应为 SimHash | requirements.md 已更新为 SimHash，以 design.md 为准 |
| 评论接口限流规则缺失 | 确认：20 条/天/用户，请补充到 design.md 接口安全章节 |
| 种子采集方式 | 确认：独立 seed 脚本，一次性执行，不走 APScheduler |

---

## 六、开发风险确认

| 风险 | PM 确认 |
|------|---------|
| zhparser 镜像固定 digest | ✅ 确认，CI 中固定镜像 digest |
| user_behaviors 浏览写入 | ✅ 方案 A，Week 5 前确认实现细节 |
| 列表接口 keyword 与搜索接口职责区分 | ✅ 确认：`GET /articles` 的 keyword 做标题 LIKE 过滤，`GET /search` 走全文检索 |

---

## 七、下一步行动

开发可按以下顺序启动：

1. **立即启动** Week 1-2 基础设施搭建
2. **Week 5 前**：确认 user_behaviors 浏览行为写入的具体实现方案
3. **P1 开发前**：补充 point_logs 表结构到 design.md，补充评论接口限流规则

---

*反馈人：PM | 所有 P0 决策已完成，开发可启动*
