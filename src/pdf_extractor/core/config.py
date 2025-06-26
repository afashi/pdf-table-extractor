from pydantic import BaseModel, PostgresDsn, AmqpDsn, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# --- 嵌套配置模型 ---
class PostgresSettings(BaseModel):
    """PostgreSQL 数据库配置"""
    user: str = "pdf_user"
    password: str = "pdf_password"
    server: str = "db"
    port: int = 5432
    db: str = "pdf_parser_db"

    # 使用 @computed_field 派生出最终的 DSN
    # 它会被 Pydantic 验证和缓存，行为更像一个真正的字段
    @computed_field
    @property
    def url(self) -> str:
        """生成并验证数据库连接 DSN"""
        return f"postgresql+psycopg:://{self.user}:{self.password}@{self.server}:{self.port}/{self.db}"


class RabbitMQSettings(BaseModel):
    """RabbitMQ 配置"""
    host: str = "127.0.0.1"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    vhost: str = "/"
    queue_name: str = "pdf_parsing_queue"
    exchange_name: str = "pdf_parser_exchange"

    @computed_field
    @property
    def url(self) -> str:
        """生成并验证 RabbitMQ 连接 URL"""
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}{self.vhost}"


# --- 主配置 ---
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        env_nested_delimiter="__",
        extra="ignore"
    )

    project_name: str = "PDF Table Extractor Service"
    api_v1_str: str = "/api/v1"
    log_level: str = "INFO"
    max_pdf_parse_time_seconds: int = 3000

    # 嵌套配置
    postgres: PostgresSettings = PostgresSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()

    # Alembic 特殊处理
    alembic_database_url: Optional[PostgresDsn] = None

    @computed_field
    @property
    def effective_alembic_database_url(self) -> str:
        """如果 Alembic URL 未设置，则使用主数据库 URL"""
        # 注意要将 pydantic 的 URL 类型转为 str
        return str(self.alembic_database_url or self.postgres.url)


settings = Settings()

# --- 如何使用 ---
# print(settings.postgres.url)
# print(settings.rabbitmq.queue_name)
# print(settings.effective_alembic_database_url)
