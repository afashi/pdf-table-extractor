import celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Iterator
from contextlib import contextmanager
import logging

from ..core.config import settings

# 设置一个日志记录器
log = logging.getLogger(__name__)

# 创建数据库引擎
# create_engine 是 SQLAlchemy 的核心接口，用于连接数据库。
print(settings.effective_alembic_database_url)
engine = create_engine(
    settings.postgres.url,
    pool_size=15,
    max_overflow=30,
    pool_timeout=300,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# 创建一个 SessionLocal 类
# sessionmaker 是一个工厂，用于生成新的 Session 对象。
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,

    # --- 性能优化 ---
    # 设置为 False 后，在 commit() 之后，对象不会被标记为“过期”。
    # 这避免了在访问已提交对象时产生不必要的数据库查询来刷新对象状态。
    expire_on_commit=False,
)


# --- 模式一：手动事务控制 (适用于 GET 或复杂逻辑) ---
@contextmanager
def get_db() -> Iterator[Session]:
    """
    获取数据库会话，需手动管理事务。

    这个依赖项只负责创建和关闭会话。
    事务的 commit, rollback 需要在业务代码中手动调用。
    适用于只读操作或需要精细控制事务的复杂场景。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 模式二：自动事务控制 (适用于 POST, PUT, DELETE) ---
@contextmanager
def get_db_with_commit() -> Iterator[Session]:
    """
    获取数据库会话，并自动管理事务（请求-事务模式）。

    - 如果业务代码成功执行，事务会自动提交。
    - 如果发生异常，事务会自动回滚。
    这是推荐用于所有“写”操作的默认依赖项。
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        log.error("数据库事务回滚，错误: %s", e)
        db.rollback()
        raise
    finally:
        db.close()


class DBTask(celery.Task):
    """
    一个抽象的Celery Task基类，它能自动完成以下工作:
    1. 注入一个数据库会话 (Session)。
    2. 如果任务成功，自动提交事务 (commit)。
    3. 如果任务失败，自动回滚事务 (rollback)。
    4. 无论成功与否，都确保会话被关闭 (close)。
    """
    abstract = True

    def __call__(self, *args, **kwargs):
        """
        在任务执行时，这个方法会被调用。
        我们在这里封装了完整的数据库事务管理逻辑。
        """
        print("<<<<< DBTask is being called! Creating database session... >>>>>")

        db = SessionLocal()
        try:
            # 将数据库会话作为第一个位置参数注入
            kwargs['db'] = db
            result = super().__call__(*args, **kwargs)
            # 如果任务函数成功执行（没有抛出异常），则提交事务
            db.commit()
            return result
        except Exception as e:
            log.error("数据库事务回滚，错误: %s", e)
            # 如果任务执行过程中发生任何异常，则回滚事务
            db.rollback()
            # 重新抛出异常，以便Celery知道任务失败了，并进行相应的处理（如重试）
            raise
        finally:
            # 最后，无论如何都要关闭会话，释放连接
            db.close()
