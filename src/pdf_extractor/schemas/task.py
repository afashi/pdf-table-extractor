import uuid
from enum import Enum

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from uuid import UUID


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# --- Pydantic Schemas for Task ---

class TaskBase(BaseModel):
    """
    基础 Schema，包含所有 Task 共有的字段。
    """
    filename: Optional[str]


class TaskCreate(TaskBase):
    """
    用于创建新任务的 Schema。
    API 在接收创建请求时，会用此模型验证请求体。
    """


class TaskCreateResponse(TaskBase):
    task_id: Optional[str] = None
    filename: Optional[str] = None
    message: Optional[str] = None


class TaskUpdate(BaseModel):
    """
    用于更新任务的 Schema。
    所有字段都是可选的，因为客户端可能只更新部分字段。
    """
    status: Optional[str] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None


class TaskInDBBase(TaskBase):
    """
    存储在数据库中的 Task 模型的基础 Schema。
    包含了从数据库读取时必然存在的字段。
    """
    # 2. 使用 Field 和 default_factory 来生成默认的 UUID
    id: UUID = Field(default_factory=uuid.uuid4)

    # 3. 将所有可能为 None 的字段用 Optional[] 包装
    status: Optional[str] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Task(TaskInDBBase):
    """
    最终返回给客户端的 Task Schema。
    目前与 TaskInDBBase 相同，但可以根据需要进行扩展，
    例如隐藏某些字段或添加计算字段。
    """
    pass


class TaskInDB(TaskInDBBase):
    """
    代表数据库中完整记录的 Schema。
    """
    pass
