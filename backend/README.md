# Backend

FastAPI 后端服务，提供 OfferHub REST API。

## 本地运行

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env  # 填写 JWT_SECRET_KEY 和数据库配置

uvicorn app.main:app --reload --port 8000
```

API 文档：http://localhost:8000/api/docs

## 测试

```bash
# 启动服务后，在项目根目录运行：
python ../scripts/smoke_test.py
```

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `JWT_SECRET_KEY` | JWT 签名密钥 | ✅ |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | ✅ |
| `POSTGRES_HOST` | 数据库主机 | 默认 localhost |
| `POSTGRES_PORT` | 数据库端口 | 默认 5432 |
| `POSTGRES_DB` | 数据库名 | 默认 offerhub |
| `POSTGRES_USER` | 数据库用户 | 默认 offerhub |
| `REDIS_HOST` | Redis 主机 | 默认 localhost |
| `REDIS_PORT` | Redis 端口 | 默认 6379 |
| `CORS_ORIGINS` | 允许的跨域来源 | 默认 http://localhost:3000 |
