# star_comm_api

星邻社后端代码仓库，第一阶段使用 FastAPI 搭建注册登录基础能力。

## 技术栈

- Python 3.12
- FastAPI
- SQLAlchemy 2.x async
- Alembic
- PostgreSQL + pgvector
- Redis
- JWT
- Argon2 password hashing

## 本地环境

系统环境由开发者自己维护。建议先确认：

```bash
conda activate starcomm-api
python --version
docker info
docker compose version
```

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

创建本地环境变量：

```bash
cp .env.example .env
```

本地 `.env` 不要提交到 Git。

## 启动本地 PostgreSQL 和 Redis

确保 Docker Desktop 已启动，然后执行：

```bash
docker compose -f deploy/local/docker-compose.yml up -d
```

停止：

```bash
docker compose -f deploy/local/docker-compose.yml down
```

## 数据库迁移

```bash
alembic upgrade head
```

## 启动后端

```bash
uvicorn app.main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

## 第一阶段接口

```text
GET  /health
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/users/me
```

## 注册示例

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "account": "test@example.com",
    "password": "password123",
    "nickname": "测试用户",
    "birth_year": 1998,
    "accepted_terms": true
  }'
```

## 登录示例

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "account": "test@example.com",
    "password": "password123"
  }'
```

## 分支规则

基础环境和登录模块可以在 `main` 分支完成。登录模块完成后，后续业务内容开发从 `main` 新建 `feature/*` 分支。
