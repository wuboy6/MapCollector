from uuid import UUID
from sqlmodel import Session, select, and_, or_
from file_system.models import Note, User, Map
from file_system.db import engine
import uuid
from typing import Tuple, Optional, List
from Log import core_trace, core_info, core_warn, core_error, core_fatal

def add_note(mapid_str: str, uid_str: str, context: str) -> Tuple[int, str]:
    """
    添加地图评注
    返回: (status_code, noteid_str)
    """
    # 验证UUID格式
    try:
        mapid = UUID(mapid_str)
        uid = UUID(uid_str)
    except ValueError as e:
        return (1002 if "mapid" in str(e) else 2001, "")  # 根据错误类型细化

    try:
        with Session(engine) as session:
            # 验证用户存在
            user = session.get(User, uid)
            if not user:
                return (2001, "")

            # 验证地图存在
            map_data = session.get(Map, mapid)
            if not map_data:
                return (1002, "")

            # 创建评注记录
            new_note = Note(
                uid=uid,
                mapid=mapid,
                content=context[:511]  # 强制长度限制
            )

            session.add(new_note)
            session.commit()
            session.refresh(new_note)

            return (0, str(new_note.noteid))

    except Exception as e:
        session.rollback()
        core_error(f"添加评注失败: {str(e)}")
        return (1011, "")


def delete_note(noteid_str: str) -> int:
    """
    删除评注记录
    返回状态码:
      - 0: 成功
      - 1012: 评注不存在
      - 1013: 删除失败
    """
    try:
        note_uuid = UUID(noteid_str)
    except ValueError:
        core_warn(f"无效的NoteID格式: {noteid_str}")
        return 1012

    try:
        with Session(engine) as session:
            # 精确查询评注
            note = session.get(Note, note_uuid)

            if not note:
                core_warn(f"评注不存在: {noteid_str}")
                return 1012

            # 执行删除
            session.delete(note)
            session.commit()

            # 二次验证删除结果
            verify_delete = session.get(Note, note_uuid)
            if verify_delete is not None:
                core_error(f"评注删除后仍存在: {noteid_str}")
                return 1013

            return 0

    except Exception as e:
        core_error(f"删除评注失败: {str(e)}", exc_info=True)
        session.rollback()
        return 1013


def get_notes(
        mapid: Optional[str] = None,
        uid: Optional[str] = None,
        count: int = 0,
        size: int = 10
) -> Tuple[int, List[dict]]:
    """
    获取评注列表
    返回: (status_code, notes_list)
    """
    # 参数校验和转换
    try:
        map_uuid = UUID(mapid) if mapid else None
        user_uuid = UUID(uid) if uid else None
    except ValueError:
        return (1002 if mapid else 2001, [])

    # 校验分页参数
    count = max(0, count)
    size = max(1, min(size, 100))  # 限制最大100条

    try:
        with Session(engine) as session:
            # 验证用户存在性
            if uid and not session.get(User, user_uuid):
                return (2001, [])

            # 验证地图存在性
            if mapid and not session.get(Map, map_uuid):
                return (1002, [])

            # 构建动态查询条件
            filters = []
            if mapid and uid:
                filters.append(Note.mapid == map_uuid and Note.uid == user_uuid)
            else:
                if mapid:
                    filters.append(Note.mapid == map_uuid)
                if uid:
                    filters.append(Note.uid == user_uuid)

            # 组合查询条件
            base_query = select(Note)
            if filters:
                base_query = base_query.where(and_(*filters))

            # 执行分页查询
            notes = session.exec(
                base_query.order_by(Note.time.desc())
                .offset(count)
                .limit(size)
            ).all()

            # 构建返回数据
            result = [{
                "mapid": str(note.mapid),
                "uid": str(note.uid),
                "time": note.time.isoformat(),
                "context": note.content
            } for note in notes]

            return (0, result)

    except Exception as e:
        core_error(f"获取评注失败: {str(e)}")
        return (1014, [])