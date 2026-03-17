-- OfferHub 数据库初始化脚本
-- 容器首次启动时自动执行

-- 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS zhparser;

-- 中文分词配置
CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);
ALTER TEXT SEARCH CONFIGURATION chinese
    ADD MAPPING FOR n, v, a, i, e, l WITH simple;

-- ============================================================
-- 枚举类型
-- ============================================================
CREATE TYPE user_role AS ENUM ('user', 'editor', 'admin');
CREATE TYPE article_status AS ENUM ('pending', 'published', 'rejected', 'deleted');
CREATE TYPE source_type AS ENUM ('ugc', 'github', 'gitee', 'rss', 'crawler');
CREATE TYPE crawl_source_type AS ENUM ('github', 'gitee', 'rss', 'web');
CREATE TYPE crawl_task_status AS ENUM ('pending', 'running', 'done', 'failed');
CREATE TYPE behavior_type AS ENUM ('view', 'like', 'collect', 'report');

-- ============================================================
-- 用户表
-- ============================================================
CREATE TABLE users (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username     VARCHAR(50)  NOT NULL UNIQUE,
    email        VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url   TEXT,
    role         user_role    NOT NULL DEFAULT 'user',
    points       INT          NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ============================================================
-- 标签表
-- ============================================================
CREATE TABLE tags (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(50) NOT NULL UNIQUE,
    category      VARCHAR(50),
    article_count INT NOT NULL DEFAULT 0
);

-- ============================================================
-- 文章表
-- ============================================================
CREATE TABLE articles (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title          VARCHAR(500) NOT NULL,
    summary        TEXT,
    content        TEXT,
    search_vector  TSVECTOR,
    author_id      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    category       VARCHAR(50),
    sub_category   VARCHAR(50),
    source_type    source_type  NOT NULL DEFAULT 'ugc',
    source_url     TEXT,
    source_license VARCHAR(100),
    status         article_status NOT NULL DEFAULT 'pending',
    view_count     INT NOT NULL DEFAULT 0,
    like_count     INT NOT NULL DEFAULT 0,
    collect_count  INT NOT NULL DEFAULT 0,
    comment_count  INT NOT NULL DEFAULT 0,
    published_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 文章-标签关联
-- ============================================================
CREATE TABLE article_tags (
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id     INT  NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

-- ============================================================
-- 评论表
-- ============================================================
CREATE TABLE comments (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id  UUID REFERENCES comments(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    like_count INT  NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 用户行为表
-- ============================================================
CREATE TABLE user_behaviors (
    id         BIGSERIAL PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    behavior   behavior_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 积分流水表（P1）
-- ============================================================
CREATE TABLE point_logs (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delta      INT          NOT NULL,
    reason     VARCHAR(100) NOT NULL,
    ref_id     UUID,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ============================================================
-- 采集源配置表
-- ============================================================
CREATE TABLE crawl_sources (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    type            crawl_source_type NOT NULL,
    url             TEXT NOT NULL,
    enabled         BOOLEAN NOT NULL DEFAULT true,
    crawl_interval  INT NOT NULL DEFAULT 60,
    last_crawled_at TIMESTAMPTZ,
    config          JSONB
);

-- ============================================================
-- 采集任务记录表
-- ============================================================
CREATE TABLE crawl_tasks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id   INT NOT NULL REFERENCES crawl_sources(id) ON DELETE CASCADE,
    status      crawl_task_status NOT NULL DEFAULT 'pending',
    items_found INT NOT NULL DEFAULT 0,
    items_saved INT NOT NULL DEFAULT 0,
    error_msg   TEXT,
    retry_count INT NOT NULL DEFAULT 0,
    started_at  TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX idx_articles_status_published ON articles(status, published_at DESC);
CREATE INDEX idx_articles_category ON articles(category, sub_category);
CREATE INDEX idx_articles_author ON articles(author_id);
CREATE INDEX idx_article_tags_tag ON article_tags(tag_id);
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);
CREATE UNIQUE INDEX idx_articles_source_url ON articles(source_url) WHERE source_url IS NOT NULL;

-- pg_trgm 索引（标题模糊搜索兜底）
CREATE INDEX idx_articles_title_trgm ON articles USING GIN(title gin_trgm_ops);

-- user_behaviors 索引
CREATE UNIQUE INDEX idx_behaviors_unique
    ON user_behaviors(user_id, article_id, behavior)
    WHERE behavior IN ('like', 'collect', 'report');
CREATE INDEX idx_behaviors_article ON user_behaviors(article_id, behavior);
CREATE INDEX idx_behaviors_user ON user_behaviors(user_id, behavior, created_at DESC);

-- point_logs 索引
CREATE INDEX idx_point_logs_user ON point_logs(user_id, created_at DESC);

-- comments 索引
CREATE INDEX idx_comments_article ON comments(article_id, created_at);

-- ============================================================
-- 触发器：自动更新 search_vector（zhparser 中文分词）
-- ============================================================
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

-- 触发器：文章更新时自动维护 updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER articles_updated_at
    BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 初始数据：系统账号（采集内容的 author）
-- ============================================================
INSERT INTO users (id, username, email, password_hash, role, points)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'offerhub_bot',
    'bot@offerhub.internal',
    'not-a-real-hash',
    'admin',
    9999
);

-- 初始 RSS 采集源
INSERT INTO crawl_sources (name, type, url, crawl_interval) VALUES
    ('掘金', 'rss', 'https://juejin.cn/rss', 60),
    ('阮一峰博客', 'rss', 'http://www.ruanyifeng.com/blog/atom.xml', 1440),
    ('美团技术团队', 'rss', 'https://tech.meituan.com/feed/', 720),
    ('InfoQ', 'rss', 'https://www.infoq.cn/feed', 120);
