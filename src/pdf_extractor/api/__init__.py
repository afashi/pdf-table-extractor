# src/pdf_extractor/api/__init__.py

from fastapi import APIRouter

from . import upload
from . import tasks
# 假如未来有更多路由，在这里继续导入
# from . import reports
# from . import users

# 创建一个聚合所有 API 路由的主路由器
api_router = APIRouter()

# 使用 include_router 将各个模块的路由包含进来
# 注意，这里的 prefix 是相对于 /api 的
api_router.include_router(upload.router, prefix="/upload", tags=["PDF Operations"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Task Management"])

# 在这里继续添加其他路由
# api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
# api_router.include_router(users.router, prefix="/users", tags=["User Management"])