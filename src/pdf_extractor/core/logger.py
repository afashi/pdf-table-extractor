import logging
import sys
import json
from pathlib import Path
from typing import Union

from ..core.config import settings


# --- 1. 自定义 JSON 日志格式化器 ---
class JsonFormatter(logging.Formatter):
    """
    自定义日志格式化器，将日志记录输出为JSON格式。
    """

    def format(self, record: logging.LogRecord) -> str:
        # 创建基础日志信息字典
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        # 如果有异常信息，则添加它
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)

        # 将字典序列化为JSON字符串
        return json.dumps(log_record, ensure_ascii=False)


# --- 2. 日志配置函数 ---
def setup_logging():
    """
    配置并返回一个日志记录器实例。
    - 在开发环境中，使用易于阅读的控制台输出。
    - 在生产环境中，使用JSON格式输出，便于日志聚合系统处理。
    """
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())

    # --- 移除所有已存在的处理器，避免重复记录 ---
    if logger.hasHandlers():
        logger.handlers.clear()

    # --- 创建并配置控制台处理器 ---
    # 在非生产环境，使用更易读的格式
    if settings.log_level.upper() == "DEBUG":
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:  # 在生产环境，使用JSON格式
        console_formatter = JsonFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


# --- 3. 初始化并导出日志记录器 ---
# 在模块加载时，立即配置好日志系统
logger = setup_logging()

# --- 如何使用 ---
# 在其他任何模块中，你只需要:
# from .core.logger import logger
#
# logger.info("这是一条信息日志")
# logger.debug("这是一条调试日志")
# try:
#     1 / 0
# except ZeroDivisionError:
#     logger.error("计算出错", exc_info=True)