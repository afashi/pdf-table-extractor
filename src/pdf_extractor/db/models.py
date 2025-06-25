import uuid
from typing import Any, Dict

from sqlalchemy import String, Text, DateTime, func, Enum as sa_Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

# 假设 'base.py' 在同一目录下或可访问的路径中
from .base import Base
from ..schemas.task import TaskStatus


class Task(Base):
    """
    数据库任务模型 (Task Model)
    (优化版)
    """
    __tablename__ = "tasks"

    # 2. 使用 SQLAlchemy 2.0 的 Mapped 和 mapped_column 语法
    # 这提供了完整的类型提示支持，更具现代感。
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    filename: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="上传的文件名"
    )

    # 3. 将 status 字段的类型改为枚举 (Enum)
    status: Mapped[TaskStatus] = mapped_column(
        sa_Enum(TaskStatus, name="task_status_enum", native_enum=False),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
        comment="任务状态"
    )

    # 对于 PostgreSQL, JSONB 是一个很好的选择。这里使用通用的 JSON 以保持兼容性。
    # Mapped[Dict[str, Any]] 提供了更精确的类型提示。
    result: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=True, comment="任务处理结果"
    )

    # 4. 将 error_message 的类型改为 Text，以容纳更长的错误信息
    error_message: Mapped[str] = mapped_column(
        Text, nullable=True, comment="任务失败的错误信息"
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def __repr__(self):
        return f"<Task(id={self.id}, filename='{self.filename}', status='{self.status.value}')>"
