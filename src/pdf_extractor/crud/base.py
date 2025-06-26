from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from pdf_extractor.db.models import Base

# 为 CRUDBase 定义泛型类型，使其可以适用于任何 SQLAlchemy 模型和 Pydantic Schema
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用 CRUD 操作基类，所有方法均不主动提交事务。

    事务的提交（commit）或回滚（rollback）由 API 层的依赖项
    （例如 get_db_with_commit）来管理。

    参数:
      - `model`: 一个 SQLAlchemy 模型类
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """通过 ID 获取单个对象。"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
            self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """获取多个对象，支持分页。"""
        return db.query(self.model).order_by(self.model.id).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建一个新对象，并将其添加到数据库会话中。
        """
        # 使用 jsonable_encoder 将 Pydantic 模型转为字典
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.flush()  # 将更改发送到数据库，以便获取 ID 等由数据库生成的值
        db.refresh(db_obj)  # 刷新对象状态
        return db_obj

    def update(
            self,
            db: Session,
            *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新一个已存在的对象。
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # exclude_unset=True 表示只包含在 obj_in 中显式设置的字段
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        删除一个对象。
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.flush()  # 将删除操作加入事务
        return obj