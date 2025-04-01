# 📁 config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, validator

# 核心修复：获取项目根目录绝对路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # 根据实际层级调整


class Settings(BaseSettings):
    """全局配置单例类"""

    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: int = Field(5432, env="DB_PORT")
    DB_NAME: str = Field(..., env="DB_NAME")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")

    DATABASE_URI: PostgresDsn | None = None

    @validator("DATABASE_URI", pre=True)
    def build_db_uri(cls, v, values) -> str:
        return (
            f"postgresql://{values['DB_USER']}:{values['DB_PASSWORD']}"
            f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"
        )

    class Config:
        # 固定加载路径为项目根目录
        env_file = PROJECT_ROOT / '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True


# 单例模式实现
_settings = None


def get_settings() -> Settings:
    """获取全局唯一配置实例"""
    global _settings
    if _settings is None:
        # 多环境加载逻辑
        env = os.getenv("APP_ENV", "development")
        env_files = [
            '..'/ PROJECT_ROOT / '.env',
        ]

        # 按优先级加载环境变量
        loaded = False
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=not loaded)
                loaded = True

        _settings = Settings()
    return _settings


# 在模块加载时立即初始化
settings = get_settings()