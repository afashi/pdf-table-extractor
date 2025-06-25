# src/pdf_extractor/api/task.py
import uuid

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends

from ..core.logger import logger
from ..db.session import get_db
from ..schemas.task import TaskCreateResponse, Task
from ..worker.tasks import process_pdf_file  # 导入 Celery 任务

router = APIRouter()


@router.post(
    "/",
    response_model=TaskCreateResponse,
    status_code=202,  # 202 Accepted
    summary="创建任务：先保存数据库记录，再分派给Worker"
)
async def create_task(
        file: UploadFile = File(..., description="要处理的PDF文件。"),
        db=Depends(get_db)):
    """
    此端点的执行流程:
    1. 验证上传的文件。
    2. 将文件临时保存到磁盘。
    3. 在数据库中创建一条状态为 "PENDING" 的任务记录。
    4. 使用数据库生成的任务ID，将任务分派给Celery。
    5. 立即将任务ID返回给客户端。
    """
    if file.content_type != "application/pdf":
        logger.warning(f"拒绝了一个非PDF文件上传: {file.filename}")
        raise HTTPException(status_code=400, detail="只能上传PDF文件。")

    # 临时保存文件
    # 注意：在生产环境中，需要一个更健壮的临时文件管理策略
    temp_file_path = f"/tmp/{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)
    except Exception as e:
        logger.error(f"保存临时文件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="无法保存上传的文件。")

    # --- 核心逻辑开始 ---

    # 1. 在数据库中创建任务记录
    # 我们只提供文件名，ID和状态将使用模型中定义的默认值
    db_task = Task(filename=file.filename)
    db.add(db_task)
    db.refresh(db_task)  # 刷新实例以获取数据库生成的值（如ID, created_at）

    task_id = db_task.id
    logger.info(f"数据库记录已创建，任务ID: {task_id}，状态: {db_task.status}")

    # 2. 使用数据库生成的 task_id 来分派 Celery 任务
    process_pdf_file.delay(
        task_id=str(task_id),  # 必须将UUID转为字符串
        file_path=temp_file_path,
        original_filename=file.filename
    )
    logger.info(f"任务 {task_id} 已成功分派给Celery Worker。")

    # 3. 立即返回响应
    return {
        "task_id": task_id,
        "message": "任务已创建并正在后台处理中。"
    }


@router.get("/{task_id}/status", response_model=Task)
def get_task_status(task_id: str, db=Depends(get_db)):
    """
    状态查询接口保持不变，它直接从数据库获取信息，快速且可靠。
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    return task
