# 使用服务器 IP 部署星邻社 H5

本文用于第一阶段临时部署，让任意手机访问：

```text
http://82.156.43.206
```

正式上线前建议改为域名和 HTTPS。

## 部署结构

```text
Nginx web container :80
├── /        前端 H5 静态页面
└── /api/v1 反代到 FastAPI

FastAPI api container :8000
PostgreSQL + pgvector container
Redis container
```

PostgreSQL 和 Redis 不暴露公网端口，只在 Docker 内部网络访问。数据保存在 Docker volumes：

```text
starcomm_prod_postgres_data
starcomm_prod_redis_data
```

## 服务器准备

服务器已确认：

```text
Ubuntu 24.04 LTS
Docker 29.5.2
```

继续检查 Docker Compose：

```bash
docker compose version
```

检查端口占用：

```bash
ss -tulpn | grep -E ':80|:443|:8000|:5432|:6379'
```

如果 80 端口已被占用，需要先停掉占用 80 的服务，或者临时把 `deploy/production/docker-compose.yml` 的 `80:80` 改成 `8080:80`。

## 克隆代码

在服务器执行：

```bash
mkdir -p ~/star_comm
cd ~/star_comm

git clone git@github.com:fragrance999/star_comm_api.git
git clone git@github.com:fragrance999/star_comm_frontend.git
```

如果服务器还没有 GitHub SSH key，可以先用 HTTPS clone：

```bash
git clone https://github.com/fragrance999/star_comm_api.git
git clone https://github.com/fragrance999/star_comm_frontend.git
```

私有仓库用 HTTPS 时需要 GitHub token。

## 配置生产环境变量

```bash
cd ~/star_comm/star_comm_api/deploy/production
cp .env.example .env
nano .env
```

必须修改：

```bash
POSTGRES_PASSWORD=换成强密码
DATABASE_URL=postgresql+asyncpg://starcomm:同一个强密码@postgres:5432/starcomm
JWT_SECRET_KEY=换成很长的随机字符串
CORS_ORIGINS=http://82.156.43.206
```

生成随机 JWT 密钥：

```bash
openssl rand -hex 32
```

## 启动生产环境

```bash
cd ~/star_comm/star_comm_api/deploy/production
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f api
docker compose logs -f web
```

## 验证

在服务器验证：

```bash
curl http://127.0.0.1/health
curl http://127.0.0.1/api/v1/users/me
```

第二个接口未登录应返回 401。

在手机或电脑浏览器访问：

```text
http://82.156.43.206
```

## 日常更新

服务器拉最新代码并重建：

```bash
cd ~/star_comm/star_comm_api
git pull

cd ~/star_comm/star_comm_frontend
git pull

cd ~/star_comm/star_comm_api/deploy/production
docker compose up -d --build
```

## 停止服务

停止容器但保留数据库数据：

```bash
cd ~/star_comm/star_comm_api/deploy/production
docker compose down
```

删除数据库和 Redis 数据需要额外删除 volumes，不要在生产环境随便执行。

