from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


# 这里创建FastAPI、配置CORS、注册/health，再把所有业务接口挂到 /api/v1
def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    # 给 FastAPI 应用添加 跨域 CORS 中间件
    # 允许指定前端地址，带着登录信息，用任意请求方法和请求头，访问这个后端 API。
    app.add_middleware(
        # 启动CORS处理，
        CORSMiddleware,
        # 允许哪些前端地址访问后端？
        allow_origins=settings.cors_origins,
        # 允许携带认证信息，比如：Cookie、Authorization Header等
        allow_credentials=True,
        # 允许所有HTTP方法，比如：GET、POST、PUT、DELETE等
        allow_methods=["*"],
        #  允许前端请求携带所有请求头，比如：Content-Type、Authorization
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
