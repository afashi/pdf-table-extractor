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
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,

    # --- 连接池配置 ---
    # 连接池中保持的最小连接数。
    pool_size=settings.DB_POOL_SIZE,

    # 连接池中允许超出 pool_size 的最大连接数。
    max_overflow=settings.DB_MAX_OVERFLOW,

    # 自动回收空闲连接的时间（秒），防止因防火墙或DB自身超时导致连接失效。
    pool_recycle=3600,

    # 在每次从连接池获取连接时，先进行一次简单的 "ping" 查询来检查连接是否有效。
    pool_pre_ping=True,

    # 获取连接的超时时间（秒）。
    pool_timeout=30,

    # --- 连接参数优化 ---
    # 为底层数据库驱动（如 psycopg2）传递额外参数。
    connect_args={
        # 设置TCP连接超时时间（秒），防止在数据库无响应时应用无限等待。
        "connect_timeout": 5
    }
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