# 📁 config.py
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, validator


class Settings(BaseSettings):
    """智能配置类，支持多环境自动识别"""

    # 数据库配置
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: int = Field(5432, env="DB_PORT")
    DB_NAME: str = Field(..., env="DB_NAME")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")

    # 生成完整 DSN
    DATABASE_URI: PostgresDsn | None = None

    @validator("DATABASE_URI", pre=True)
    def build_db_uri(cls, v, values) -> str:
        """动态生成 PostgreSQL 连接字符串"""
        return (
            f"postgresql://{values['DB_USER']}:{values['DB_PASSWORD']}"
            f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"
        )

    class Config:
        # 自动加载 .env 和 .env.local 文件
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 初始化配置
def load_config(env_file=".env") -> Settings:
    """加载配置并自动识别环境"""
    # 1. 加载基础配置
    load_dotenv(env_file)

    # 2. 加载环境特定配置（如 .env.production）
    env_name = os.getenv("APP_ENV", "development")
    env_specific = f".env.{env_name}"
    if os.path.exists(env_specific):
        load_dotenv(env_specific, override=True)

    return Settings()