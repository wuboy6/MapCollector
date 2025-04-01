from sqlmodel import SQLModel
from file_system.db import  engine

def test_user_functions():
    SQLModel.metadata.drop_all(engine)  # 清除旧表

if __name__ == "__main__":
    test_user_functions()