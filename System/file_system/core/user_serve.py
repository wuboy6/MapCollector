from uuid import UUID, uuid4
from sqlmodel import Session, select
from file_system.models import User
from file_system.db import engine
from typing import Tuple, Dict
from Log import core_trace, core_info, core_warn, core_error, core_fatal


def get_user_pw(u_email: str) -> Tuple[int, str, str]:
    """
    通过邮箱获取用户凭证
    返回: (status_code, uuid_str, hashed_pw_str)
    状态码:
      - 0: 成功
      - 2001: 用户不存在
      - 1007: 系统错误
    """
    try:
        with Session(engine) as session:
            # 精确匹配邮箱（区分大小写）
            user = session.exec(
                select(User).where(User.email == u_email)
            ).first()

            if not user:
                core_warn(f"用户不存在: {u_email}")
                return (2001, "", "")

            return (
                0,
                str(user.uid),
                user.hashed_passward  # 注意字段名是 hashed_passward
            )

    except Exception as e:
        core_error(f"凭证获取失败: {str(e)}")
        return (1007, "", "")

def create_user(u_email: str, hashed_pw: str) -> Tuple[int, str]:
    """
    创建用户并返回UUID
    返回: (status_code, uuid_str)
    状态码:
      - 0: 成功
      - 2002: 用户已存在
      - 1008: 创建失败
    """
    try:
        with Session(engine) as session:
            # 检查用户是否存在
            existing_user = session.exec(
                select(User).where(User.email == u_email)
            ).first()

            if existing_user:
                core_warn(f"用户已存在: {u_email}")
                return (2002, "")

            # 创建新用户 (处理 last_read 字段)
            new_user = User(
                email=u_email,
                hashed_passward=hashed_pw,  # 注意字段名是 hashed_passward
                last_read=None
            )

            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            return (0, str(new_user.uid))

    except Exception as e:
        core_error(f"用户创建失败: {str(e)}")
        session.rollback()
        return (1008, "")


def delete_user(uuid_str: str) -> int:
    """
    注销用户
    返回状态码:
      - 0: 成功
      - 2002: 用户不存在
      - 1009: 删除失败
    """
    try:
        user_uuid = UUID(uuid_str)
    except ValueError:
        core_warn(f"无效UUID格式: {uuid_str}")
        return 2002  # 视为用户不存在

    try:
        with Session(engine) as session:
            # 精确查询用户
            user = session.get(User, user_uuid)

            if not user:
                core_warn(f"用户不存在: {user_uuid}")
                return 2002

            # 执行删除
            session.delete(user)
            session.commit()

            # 二次验证删除结果
            if session.get(User, user_uuid) is not None:
                core_error(f"用户删除后仍存在: {user_uuid}")
                return 1009

            return 0

    except Exception as e:
        core_error(f"用户删除失败: {str(e)}")
        session.rollback()
        return 1009


def get_user_model(uuid_str: str) -> Tuple[int, Dict]:
    """
    获取用户详细信息
    返回: (status_code, user_details)
    状态码:
      - 0: 成功
      - 2001: 用户不存在
      - 1010: 系统错误
    """
    try:
        user_uuid = UUID(uuid_str)
    except ValueError:
        core_warn(f"无效UUID格式: {uuid_str}")
        return (2001, {})

    try:
        with Session(engine) as session:
            user = session.get(User, user_uuid)

            if not user:
                core_warn(f"用户不存在: {user_uuid}")
                return (2001, {})

            # 构建详情字典（排除敏感字段）
            details = {
                "user_name": user.name if user.name else "Collector",
                "user_email": user.email,
                "last_read": str(user.last_read) if user.last_read else None
            }

            return (0, details)

    except Exception as e:
        core_error(f"用户详情获取失败: {str(e)}")
        return (1010, {})