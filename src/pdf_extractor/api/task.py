# src/pdf_extractor/api/task.py (修正后)
import tempfile
import uuid
import os

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session

from ..core.logger import logger
from ..db.session import get_db, get_db_with_commit, SessionLocal
from ..schemas import task as task_schema # 使用别名以区分
from ..crud import task as crud_task     # 导入 CRUD 操作
from ..db import models                   # 导入 SQLAlchemy models
from ..worker.tasks import process_pdf_file

router = APIRouter()


@router.post(
    "/",
    response_model=task_schema.TaskCreateResponse,
    status_code=202,
    summary="上传PDF并创建处理任务"
)
async def create_upload_task(  # <-- 1. 重命名函数
        file: UploadFile = File(..., description="要处理的PDF文件。"),
        db: Session = Depends(get_db)):
    """
    此端点的执行流程:
    1. 验证上传的文件。
    2. 将文件安全地保存到临时位置。
    3. 使用 CRUD 层在数据库中创建任务记录。
    4. 将任务分派给 Celery。
    5. 立即返回任务ID。
    """
    if file.content_type != "application/pdf":
        logger.warning(f"拒绝了一个非PDF文件上传: {file.filename}")
        raise HTTPException(status_code=400, detail="只能上传PDF文件。")

    # --- 2. 使用 tempfile 安全创建临时文件 ---
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name
        logger.info(f"文件 '{file.filename}' 已临时保存到: {temp_file_path}")
    except Exception as e:
        logger.error(f"保存临时文件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="无法保存上传的文件。")

    # --- 3. 使用 CRUD 层创建数据库任务 ---
    task_to_create = task_schema.TaskCreate(filename=file.filename)
    db_task = crud_task.task.create(db=db, obj_in=task_to_create)

    # 手动提交事务 (因为 get_db 不会自动提交)
    db.commit()
    db.refresh(db_task)

    task_id = db_task.id
    logger.info(f"数据库记录已创建，任务ID: {task_id}")

    # --- 4. 分派 Celery 任务 ---
    process_pdf_file.delay(
        task_id=str(task_id),
        file_path=temp_file_path,
        original_filename=file.filename
    )
    logger.info(f"任务 {task_id} 已成功分派给Celery Worker。")

    return {
        "task_id": str(task_id), # 确保返回的是字符串
        "filename": file.filename,
        "message": "任务已创建并正在后台处理中。"
    }


@router.get("/{task_id}/status", response_model=task_schema.Task)
def get_task_status(task_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    状态查询接口，通过ID从数据库获取任务信息。
    """
    # --- 5. 使用 CRUD 层查询 ---
    db_task = crud_task.task.get(db=db, id=task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="任务未找到")
    return db_task

def get_db_session():
    """
    一个 FastAPI 依赖项，它能创建并产出一个数据库会话，
    并在请求处理结束后关闭它。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(
    "/create_test_task",  # <-- 1. 修改路径和函数名
    response_model=task_schema.TaskCreateResponse,
    status_code=202,
    summary="创建一个用于测试的虚拟任务"
)
async def create_test_task(db: Session = Depends(get_db_session)):
    """
    创建一个虚拟任务用于测试，不涉及文件上传。
    """
    # 模拟文件名和路径
    test_filename = f"test_file_{uuid.uuid4()}.pdf"
    test_filepath = f"/path/to/virtual/{test_filename}"

    # --- 3. 使用 CRUD 层创建数据库任务 ---
    task_to_create = task_schema.TaskBase(filename=test_filename)
    db_task = crud_task.task.create(db=db, obj_in=task_to_create)
    db.commit()  # <--- 4. 在这里提交事务
    db.refresh(db_task)
    task_id = db_task.id
    logger.info(f"数据库测试任务已创建，ID: {task_id}")

    # --- 4. 分派 Celery 任务 ---
    process_pdf_file.delay(
        task_id=str(task_id),
        file_path=test_filepath,
        original_filename=test_filename
    )
    logger.info(f"测试任务 {task_id} 已成功分派给Celery Worker。")

    return {
        "task_id": str(task_id),
        "filename": test_filename,
        "message": "测试任务已创建并正在后台处理中。"
    }