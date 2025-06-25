import time
from ..celery_app import celery_app
from ..core.logger import logger


# 为了让 Celery Worker 能够找到这个任务，
# 我们需要从 celery_app 模块导入 celery_app 实例。

@celery_app.task(bind=True, name="process_pdf_file_task")
def process_pdf_file(self, file_path: str, original_filename: str):
    """
    后台任务：处理上传的PDF文件。

    Args:
        self: 任务实例 (由 bind=True 注入)。
        file_path (str): 保存在服务器上的临时文件的绝对路径。
        original_filename (str): 用户上传时的原始文件名。
    """
    task_id = self.request.id
    logger.info(
        f"开始处理文件: {original_filename} (路径: {file_path})",
        extra={"task_id": task_id}
    )

    try:
        # 模拟一个耗时的PDF解析过程
        logger.debug(f"模拟PDF解析...", extra={"task_id": task_id, "file_path": file_path})
        time.sleep(15)  # 模拟15秒的处理时间

        # 在这里替换为真实的PDF处理逻辑，例如:
        # from ..services.pdf_parser import extract_tables
        # tables = extract_tables(file_path)
        # result = {"table_count": len(tables)}
        # logger.info(f"文件 {original_filename} 处理完成，提取到 {len(tables)} 个表格。", extra={"task_id": task_id})

        # 模拟成功结果
        result = {"status": "成功", "message": f"{original_filename} 已处理完毕。"}
        logger.info(f"文件 {original_filename} 处理成功。", extra={"task_id": task_id})

        return result

    except Exception as e:
        logger.error(
            f"处理文件 {original_filename} 时发生严重错误: {e}",
            exc_info=True,
            extra={"task_id": task_id}
        )
        # 任务失败，可以进行重试。 countdown是重试前的等待秒数。
        # self.retry() 会抛出一个异常，所以这之后的代码不会执行。
        raise self.retry(exc=e, countdown=60, max_retries=3)