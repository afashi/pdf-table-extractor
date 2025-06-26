# src/pdf_extractor/worker/task.py

import time
from ..celery_app import celery_app
from ..core.logger import logger
from ..db.session import Session
from ..db.models import Task
from ..schemas.task import TaskStatus
from ..services.parser_service import PDFParserService  # 1. 导入新的服务


@celery_app.task(name="process_pdf_file_task")
def process_pdf_file(task_id: str, file_path: str, original_filename: str, db: Session = None):
    """
    后台任务：使用 PDFParserService 处理PDF，并更新数据库状态。
    """
    logger.info(f"Worker 收到任务 {task_id}，处理文件: {original_filename}")
    update_task_status(db, task_id, "STARTED")

    try:
        # 2. 实例化并使用服务
        parser = PDFParserService()

        # 提取目录
        # toc = parser.get_toc(file_path)
        toc = {"dd":11}
        # 您还可以调用其他服务方法，例如：
        # tables = parser.extract_tables(file_path)
        # text_content = parser.extract_text(file_path)

        # 准备成功的结果
        success_result = {"result": toc}
        update_task_status(db, task_id, TaskStatus.COMPLETED.strip(), success_result)
        logger.info(f"任务 {task_id} 处理文件 {original_filename} 成功。")
        return success_result

    except ValueError as ve:  # 捕获我们自己定义的异常
        logger.error(f"任务 {task_id} 失败，文件 '{original_filename}' 解析错误: {ve}", exc_info=True)
        failure_result = {"error": str(ve)}
        update_task_status(db, task_id, "FAILURE", result=failure_result)
        raise ve

    except Exception as e:
        logger.error(f"任务 {task_id} 发生未知错误，处理文件 {original_filename}: {e}", exc_info=True)
        failure_result = {"error": "发生未知服务器错误，请查看日志。"}
        update_task_status(db, task_id, "FAILURE", result=failure_result)
        raise e


def update_task_status(db, task_id: str, status: str, result: dict = None):
    db.query(Task).filter(Task.id == task_id).update({
        "status": status,
        "result": result
    })
