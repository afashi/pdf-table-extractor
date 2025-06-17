import uuid
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from base import Base


class Task(Base):
    """
    数据库任务模型 (Task Model)

    该模型定义了 'tasks' 表的结构，用于存储 PDF 文件处理任务的状态和结果。
    """
    __tablename__ = "tasks"

    # 任务的唯一标识符，使用 UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 上传的原始文件名
    filename = Column(String(255), nullable=False, comment="上传的文件名")

    # 任务的当前状态，例如: pending, processing, completed, failed
    # 添加索引以优化按状态查询的性能
    status = Column(String(10), nullable=False, default='pending', index=True, comment="任务状态")

    # 存储任务成功后的结果，使用 JSONB 类型以高效存储结构化数据（例如标题列表）
    result = Column(JSONB, nullable=True, comment="任务处理结果")

    # 如果任务失败，存储错误信息
    error_message = Column(String(1000), nullable=True, comment="任务失败的错误信息")

    # 记录创建时间，数据库自动设置
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")

    # 记录更新时间，数据库在记录更新时自动设置
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Task(id={self.id}, filename='{self.filename}', status='{self.status}')>"
