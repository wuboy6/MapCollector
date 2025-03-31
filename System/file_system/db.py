from sqlmodel import create_engine, SQLModel
import os
from typing import Optional
from sqlalchemy.engine import Engine
import config

settings = config.load_config("../../.env")
# 优先读取环境变量配置
DATABASE_URL: str = str(settings.DATABASE_URI)

# 高级引擎配置
ENGINE_KWARGS = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_recycle": 3600,  # 每小时回收连接
    "pool_pre_ping": True,  # 自动检测断连
    "connect_args": {
        "options": "-c timezone=Asia/Shanghai",  # 时区设置
        "sslmode": "prefer"  # SSL模式
    }
}


def get_engine(connection_url: Optional[str] = None) -> Engine:
    """创建符合生产要求的数据库引擎"""
    return create_engine(
        connection_url or DATABASE_URL,
    ** ENGINE_KWARGS
    )

def create_tables(engine: Engine):
    """安全创建所有表结构"""
    from models import Map, User, Note  # 延迟导入模型

    try:
        SQLModel.metadata.create_all(engine)
        print("✅ 表结构创建成功")
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        exit(1)

# 全局引擎实例
engine = get_engine()

if __name__ == "__main__":
    # 开发环境初始化脚本
    import sys
    print("[系统提示] 正在初始化数据库...")

    # 安全验证
    if "prod" in DATABASE_URL:
        confirm = input("⚠️  检测到生产环境，确认继续？(y/n): ")
        if confirm.lower() != "y":
            sys.exit("操作已取消")

    create_tables(engine)