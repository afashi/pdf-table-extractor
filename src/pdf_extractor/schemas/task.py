from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID


# --- Pydantic Schemas for Task ---

class TaskBase(BaseModel):
    """
    基础 Schema，包含所有 Task 共有的字段。
    """
    filename: Optional[str] = None


class TaskCreate(TaskBase):
    """
    用于创建新任务的 Schema。
    API 在接收创建请求时，会用此模型验证请求体。
    """
    filename: str


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
    id: UUID
    status: str
    result: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Pydantic V2 or higher
    # 允许 Pydantic 模型从 ORM 对象（如 SQLAlchemy 模型实例）创建，
    # 实现 ORM 对象到 Schema 的自动映射。
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