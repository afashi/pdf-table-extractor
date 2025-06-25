from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from ..worker.celery_app import celery_app
from ..schemas.task import TaskStatusResponse
from ..core.logger import logger

router = APIRouter()


@router.get(
    "/{task_id}/status",
    response_model=TaskStatusResponse,
    summary="查询后台任务的状态和结果",
    description="根据任务ID获取其当前状态（如：等待、进行中、成功、失败）以及处理结果。"
)
def get_task_status(task_id: str):
    """
    根据给定的 task_id 查询 Celery 任务的状态。

    Args:
        task_id (str): Celery 任务的唯一标识符。

    Returns:
        一个包含任务状态和结果的字典。
    """
    logger.info(f"查询任务状态，任务ID: {task_id}")

    # 使用从 Celery 应用实例获取的 AsyncResult 来查询任务
    task_result = AsyncResult(task_id, app=celery_app)

    # 准备响应数据
    response_data = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }

    if task_result.successful():
        # 如果任务成功完成，获取结果
        response_data["result"] = task_result.get()
        logger.info(f"任务 {task_id} 已成功完成。")

    elif task_result.failed():
        # 如果任务失败，记录错误并返回异常信息
        # traceback 包含详细的错误堆栈，更便于调试
        error_info = {
            "error": str(task_result.info),  # 异常类型和消息
            "traceback": task_result.traceback  # 完整的错误堆栈
        }
        response_data["result"] = error_info
        logger.warning(f"任务 {task_id} 执行失败。错误: {task_result.info}")

    # 对于 PENDING, RETRY, STARTED 等其他状态，result 字段将保持为 None
    else:
        logger.info(f"任务 {task_id} 当前状态: {task_result.status}")

    return response_data