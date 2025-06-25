# src/pdf_extractor/api/__init__.py

from fastapi import APIRouter

from . import task

# 创建一个聚合所有 API 路由的主路由器
api_router = APIRouter()

# 使用 include_router 将各个模块的路由包含进来
# 注意，这里的 prefix 是相对于 /api 的
api_router.include_router(task.router, prefix="/tasks", tags=["Task Management"])
