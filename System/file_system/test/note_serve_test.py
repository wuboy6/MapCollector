import uuid
from typing import Tuple
from sqlmodel import SQLModel, Session
from file_system.db import engine
from file_system import *
from file_system.models import User, Map, Note
import cv2
from uuid import UUID



def test_note_functions():
    """综合测试笔记相关功能"""
    # 初始化数据库
    SQLModel.metadata.create_all(engine)

    # 创建测试用户和地图
    test_user_id = create_test_user()
    test_map_id = create_test_map()

    # 测试用例1: 正常添加笔记
    print("\n=== 测试用例1: 添加笔记 ===")
    content = "测试评注内容"
    status, note_id = add_note(test_map_id, test_user_id, content)
    assert status == 0, "添加笔记失败"
    print(f"添加成功，笔记ID: {note_id}")

    # 测试用例2: 添加无效用户笔记
    print("\n=== 测试用例2: 无效用户 ===")
    invalid_user = str(uuid.uuid4())
    status, _ = add_note(test_map_id, invalid_user, content)
    assert status == 2001, "用户存在性检查失效"

    # 测试用例3: 添加无效地图笔记
    print("\n=== 测试用例3: 无效地图 ===")
    invalid_map = str(uuid.uuid4())
    status, _ = add_note(invalid_map, test_user_id, content)
    assert status == 1002, "地图存在性检查失效"

    # 测试用例4: 获取用户笔记
    print("\n=== 测试用例4: 获取用户笔记 ===")
    status, notes = get_notes(uid=test_user_id)
    assert status == 0 and len(notes) >= 1, "笔记查询失败"
    print(f"获取到{len(notes)}条笔记")

    # 测试用例5: 删除笔记
    print("\n=== 测试用例5: 删除笔记 ===")
    status = delete_note(note_id)
    assert status == 0, "删除操作失败"

    # 验证删除结果
    status, notes = get_notes(uid=test_user_id)
    assert all(n['context'] != content for n in notes), "笔记未正确删除"

    # 清理测试数据
    cleanup_test_data(test_user_id, test_map_id)
    print("\n所有测试通过！")


# 测试辅助函数
def create_test_user() -> str:
    """创建测试用户"""
    email = "test_user@example.com"
    pwd = "test_password"
    status, uid = create_user(email, pwd)
    if status != 0:
        raise RuntimeError("测试用户创建失败")
    return uid


def create_test_map() -> str:
    """创建测试地图"""
    # 假设已有创建地图的函数
    status, map_id = add_map("测试地图", cv2.imread("E:/dev/MapCollector/test/maps/ChinaMap.jpeg"))
    if status != 0:
        raise RuntimeError("测试地图创建失败")
    return map_id


def cleanup_test_data(user_id: str, map_id: str):
    """清理测试数据"""
    with Session(engine) as session:
        # 删除用户
        if user := session.get(User, UUID(user_id)):
            session.delete(user)
        # 删除地图
        if map_data := session.get(Map, UUID(map_id)):
            session.delete(map_data)
        session.commit()


if __name__ == "__main__":
    test_note_functions()