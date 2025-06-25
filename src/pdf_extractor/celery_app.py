import logging
from celery import Celery
from celery.signals import after_setup_logger

from .core.config import settings
from .core.logger import JsonFormatter
from .db.session import DBTask

# --- 1. 创建 Celery 实例 ---
celery_app = Celery(
    "pdf_extractor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    # 更新这里：指向新的任务模块路径
    include=["src.pdf_extractor.worker.tasks"],
    task_cls=DBTask,
)

# --- 2. Celery 配置 ---
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


# --- 3. 集成结构化日志 ---
@after_setup_logger.connect
def setup_celery_logging(logger, **kwargs):
    """
    在Celery设置好logger后，为其添加使用我们自定义JsonFormatter的处理器。
    """
    for handler in logger.handlers:
        logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    logger.setLevel(settings.log_level.upper())