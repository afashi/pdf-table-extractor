# src/pdf_extractor/worker/task.py

import time
from ..celery_app import celery_app
from ..core.logger import logger
from ..db.session import SessionLocal
from ..db.models import Task
from ..services.parser_service import PDFParserService # 1. 导入新的服务


def update_task_status(task_id: str, status: str, result: dict = None):
    """Helper function to update task status in the database."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            if result is not None:
                task.result = result
            db.commit()
            logger.info(f"Database updated for task {task_id} with status '{status}'.")
        else:
            logger.warning(f"Task with id {task_id} not found in database for update.")
    except Exception as e:
        db.rollback()
        logger.error(f"Database update failed for task {task_id}: {e}", exc_info=True)
    finally:
        db.close()


@celery_app.task(bind=True, name="process_pdf_file_task")
def process_pdf_file(self, db: SessionLocal, task_id: str, file_path: str, original_filename: str):
    """
    后台任务：使用 PDFParserService 处理PDF，并更新数据库状态。
    """
    logger.info(f"Worker 收到任务 {task_id}，处理文件: {original_filename}")
    update_task_status(task_id, "STARTED")

    try:
        # 2. 实例化并使用服务
        parser = PDFParserService()

        # 提取目录
        toc = parser.get_toc(file_path)

        # 您还可以调用其他服务方法，例如：
        # tables = parser.extract_tables(file_path)
        # text_content = parser.extract_text(file_path)

        # 准备成功的结果
        success_result = {
            "status": "成功",
            "filename": original_filename,
            "result": toc,
            # "table_count": len(tables)
        }

        db.query(Task).filter(Task.id == task_id).update({
            "status": "SUCCESS",
            "result": success_result
        })
        logger.info(f"任务 {task_id} 处理文件 {original_filename} 成功。")
        return success_result

    except ValueError as ve:  # 捕获我们自己定义的异常
        logger.error(f"任务 {task_id} 失败，文件 '{original_filename}' 解析错误: {ve}", exc_info=True)
        failure_result = {"error": str(ve)}
        update_task_status(task_id, "FAILURE", result=failure_result)
        raise ve

    except Exception as e:
        logger.error(f"任务 {task_id} 发生未知错误，处理文件 {original_filename}: {e}", exc_info=True)
        failure_result = {"error": "发生未知服务器错误，请查看日志。"}
        update_task_status(task_id, "FAILURE", result=failure_result)
        raise e