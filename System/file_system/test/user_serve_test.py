from file_system import create_user, get_user_model, delete_user, get_user_pw
import uuid
from file_system.db import engine
from file_system.models import User
from sqlmodel import Session, select

def test_user_functions():
    """综合测试用户相关功能"""
    test_email = "test@example.com"
    test_password = "secure_hash_123"
    test_uuid = str(uuid.uuid4())

    # 测试准备：确保测试用户不存在
    cleanup_user(test_email)

    # 测试用例1: 创建新用户
    print("\n=== 测试用例1: 创建新用户 ===")
    status, uid = create_user(test_email, test_password)
    assert status == 0, "创建用户失败"
    print(f"创建成功，用户ID: {uid}")

    # 测试用例2: 重复创建相同邮箱用户
    print("\n=== 测试用例2: 重复创建 ===")
    status, _ = create_user(test_email, "another_password")
    assert status == 2002, "重复创建检查失效"
    print("重复创建测试通过")

    # 测试用例3: 获取用户凭证
    print("\n=== 测试用例3: 获取凭证 ===")
    status, fetched_uid, password_hash = get_user_pw(test_email)
    assert status == 0 and fetched_uid == uid, "凭证获取失败"
    print(f"获取到凭证哈希: {password_hash[:6]}...")

    # 测试用例4: 获取用户信息
    print("\n=== 测试用例4: 获取用户信息 ===")
    status, details = get_user_model(uid)
    assert status == 0 and details["user_email"] == test_email, "用户信息不匹配"
    print(f"用户信息: {details}")

    # 测试用例5: 删除用户
    print("\n=== 测试用例5: 删除用户 ===")
    status = delete_user(uid)
    assert status == 0, "删除操作失败"
    print("用户删除成功")

    # 测试用例6: 删除不存在用户
    print("\n=== 测试用例6: 删除不存在用户 ===")
    status = delete_user(uid)  # 已删除的UUID
    assert status == 2002, "删除不存在用户逻辑错误"
    status = delete_user("invalid_uuid")
    assert status == 2002, "无效UUID处理错误"
    print("删除不存在用户测试通过")

    # 清理测试数据
    cleanup_user(test_email)
    print("\n所有测试通过！")


def cleanup_user(email: str):
    """清理测试用户"""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if user:
            session.delete(user)
            session.commit()


if __name__ == "__main__":

    # 运行测试
    test_user_functions()