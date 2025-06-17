from sqlalchemy.orm import declarative_base

# 创建一个所有 ORM 模型都将继承的基础类 (Declarative Base)。
#
# `declarative_base()` 函数返回一个类，之后我们项目中的所有数据库模型
# (例如在 models.py 中定义的 Task 模型) 都会继承自这个 `Base` 类。
#
# 当模型类被定义时，SQLAlchemy 会自动将 Python 类映射到数据库的表上。
# 这个 Base 类充当了这个映射关系的注册表，跟踪所有与它关联的模型。
Base = declarative_base()
