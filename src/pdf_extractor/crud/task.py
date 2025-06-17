from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import models
from ..schemas import task as task_schema
from .base import CRUDBase  # 假设 CRUDBase 在 base.py 中


class CRUDTask(CRUDBase[models.Task, task_schema.TaskCreate, task_schema.TaskUpdate]):
    """
    针对 Task 模型的特定 CRUD 操作。
    所有方法都不再包含 db.commit()。
    """

    def create(self, db: Session, *, obj_in: task_schema.TaskCreate) -> models.Task:
        """
        创建一个新任务，但不提交事务。

        Args:
            db: SQLAlchemy Session.
            obj_in: 用于创建任务的数据模型.

        Returns:
            新创建的 Task 对象 (尚未持久化提交).
        """
        db_obj = models.Task(
            filename=obj_in.filename,
            status="pending"
        )
        db.add(db_obj)
        db.flush()  # 将更改发送到数据库事务中，以便获取 ID 等默认值
        db.refresh(db_obj)
        return db_obj

    def update(
            self,
            db: Session,
            *,
            db_obj: models.Task,
            obj_in: Union[task_schema.TaskUpdate, Dict[str, Any]]
    ) -> models.Task:
        """
        更新一个任务，但不提交事务。
        """
        # 使用基类的 update 方法，确保它内部也没有 commit
        # (通常 CRUDBase 的 update 方法只包含 add 和 flush)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj


# 创建一个 CRUDTask 的单例
task = CRUDTask(models.Task)
