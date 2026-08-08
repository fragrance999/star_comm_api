from fastapi import APIRouter

from app.api.v1 import auth, memories, spirit, users

# 路由总入口
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(spirit.router, prefix="/spirit", tags=["spirit"])
api_router.include_router(memories.router, prefix="/memories", tags=["memories"])
