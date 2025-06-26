from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from .core.config import settings
from .core.logger import logger
from .api import api_router  # 1. 只需导入 api_router


# --- 1. 应用生命周期事件 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动和关闭时执行的事件管理器。
    """
    logger.info(f"PDF Extractor API - 启动中...")
    logger.info(f"日志级别: {settings.log_level.upper()}")
    logger.info(f"Celery Broker: {settings.rabbitmq.url}")
    yield
    # --- 应用关闭时执行 ---
    logger.info("PDF Extractor API - 已关闭")


# --- 2. 创建 FastAPI 应用实例 ---
app = FastAPI(
    title=settings.project_name,
    description="一个用于从PDF文件中提取表格的API服务",
    version="1.0.0",
    lifespan=lifespan  # 使用新的生命周期管理器
)

# --- 3. 包含 API 路由 ---
# 包含来自 `api` 模块的路由，并为其添加统一的前缀 `/api`
app.include_router(api_router, prefix="/api")


# --- 4. 定义根端点 ---
@app.get("/", tags=["Health Check"])
async def read_root():
    """
    根端点，用于简单的服务健康检查。
    """
    logger.info("接收到健康检查请求")
    return {"status": "ok", "message": f"Welcome to {settings.project_name}!"}
