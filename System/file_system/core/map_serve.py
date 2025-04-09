from file_system.db import engine
from file_system.models import Map, User, MapChange
from typing import List, Tuple, Dict, Optional
from sqlmodel import Session, select
from Log import core_trace, core_info, core_warn, core_error, core_fatal
import uuid
from uuid import UUID
import cv2
import os
import datetime
from config import PROJECT_ROOT

MAP_STORAGE_ROOT = PROJECT_ROOT / "System/file_system/core/res/maps/"

# 允许通过arcs修改的字段列表
ALLOWED_UPDATE_FIELDS = {
    "map_name", "map_type", "media_type",
    "description", "public_time", "stars"
}

def get_map_list() -> Tuple[int,List]:
    """
        获取地图清单 API
        返回格式：
        {
            "status": int,
            "data": List[Tuple[str, str, str, str, str]]
            即 list  [(“mapid”, “map_name”, “maptype”, “mediatype”, “description”) ]
        }
    """
    try:
        with Session(engine) as session:
            # 执行查询
            statement = select(Map)
            maps = session.exec(statement).all()

            maplist = [
                {
                    "mapid" : str(map.mapid),        # 转换UUID为字符串
                    "map_name" : map.map_name,
                    "map_type" : map.map_type,
                    "media_type" : map.media_type,
                    "description" : map.description
                }
                for map in maps
            ]

            return 0, maplist
    except Exception as e:
        core_error(f"获取地图列表失败: {str(e)}")
        return (1001, [])

def get_map(mapid : str) -> Tuple[int, cv2.Mat | None, Dict]:
    """
        获取地图图像数据 (OpenCV格式)
        返回: (status, cv2_image)

        """
    try:
        mapid = UUID(mapid)  # 转换UUID
    except ValueError:
        core_warn(f"无效UUID格式:{str(mapid)}")
        return (1002, None, {})  # 无效UUID格式

    try:
        with Session(engine) as session:
            # 查询数据库
            map_data = session.get(Map, mapid)

            if not map_data:
                core_warn(f"地图不存在:{str(mapid)}")
                return (1002, None, {})  # 地图不存在

            # 验证文件路径
            if not os.path.exists(map_data.file_path):
                core_warn(f"文件不存在:{str(mapid)}")
                return (1002, None, {})  # 文件不存在

            # 使用OpenCV读取TIFF
            img = cv2.imread(map_data.file_path, cv2.IMREAD_UNCHANGED)

            if img is None:
                core_warn(f"文件读取失败:{str(mapid)}")
                return (1002, None, {})  # 文件读取失败

            params = {
                "map_name": map_data.map_name,
                "map_type": map_data.map_type,
                "media_type": map_data.media_type,
                "description": map_data.description,
                "public_time": map_data.public_time.isoformat() if map_data.public_time else None,
                "collect_time": map_data.collect_time.isoformat(),
                "stars": map_data.stars
            }

            return (0, img, params)  # 成功返回OpenCV图像

    except Exception as e:
        print(f"Error: {str(e)}")
        return (1002, None, {})  # 其他错误



def add_map(name: str, cv_image: cv2.Mat) -> Tuple[int, str]:
    """
    添加地图并返回ID
    返回: (status_code, mapid_str)
    """
    try:
        # 生成唯一ID和文件名
        map_uuid = uuid.uuid4()
        mapid_str = str(map_uuid)
        filename = f"{mapid_str}.tiff"
        file_path = os.path.join(MAP_STORAGE_ROOT, filename)

        # 创建存储目录
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 保存图像文件
        if not cv2.imwrite(file_path, cv_image):
            core_warn(f"文件保存失败: {file_path}")
            return (1003, "")

        # 创建数据库记录
        new_map = Map(
            mapid=map_uuid,
            map_name=name,
            file_path=file_path,
            row=cv_image.shape[0],
            col=cv_image.shape[1]
        )

        with Session(engine) as session:
            session.add(new_map)
            session.commit()
            session.refresh(new_map)

            return (0, mapid_str)

    except Exception as e:
        # 回滚操作：删除已保存文件
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as file_e:
                core_warn(f"文件回滚失败: {str(file_e)}")

        core_warn(f"添加地图失败: {str(e)}")
        return (1004, "")


def delete_map(mapid_str: str) -> int:
    """
    删除地图
    返回: status_code
    """
    try:
        map_uuid = UUID(mapid_str)
    except ValueError:
        core_warn(f"无效UUID格式: {mapid_str}")
        return 1002

    try:
        with Session(engine) as session:
            # 获取地图记录
            map_data = session.get(Map, map_uuid)
            if not map_data:
                return 1002

            # 删除文件
            file_path = map_data.file_path
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as file_e:
                    core_warn(f"文件删除失败: {str(file_e)}")
                    return 1005

            # 删除数据库记录
            session.delete(map_data)
            session.commit()
            return 0

    except Exception as e:
        core_warn(f"删除操作失败: {str(e)}")
        session.rollback()
        return 1005



def change_map(mapid_str: str, arcs: Optional[Dict] = None) -> int:
    """
    通过字典参数修改地图属性
    返回: 状态码 (0: 成功, 1002: 找不到地图, 1006: 修改失败)
    """
    try:
        map_uuid = UUID(mapid_str)
    except ValueError:
        return 1002  # 无效UUID格式

    if not arcs:
        return 0  # 无修改请求直接返回成功

    try:
        with Session(engine) as session:
            # 获取地图记录
            map_data = session.get(Map, map_uuid)
            if not map_data:
                return 1002

            # 过滤有效字段
            valid_updates = {}
            for key, value in arcs.items():
                if key in ALLOWED_UPDATE_FIELDS:
                    # 特殊处理日期字段
                    if key == "public_time":
                        if isinstance(value, str):
                            value = datetime.datetime.fromisoformat(value)
                        elif not isinstance(value, datetime.datetime):
                            raise ValueError("public_time必须是datetime或ISO字符串")
                    valid_updates[key] = value

            if not valid_updates:
                return 0  # 无有效更新字段

            # 执行批量更新
            for key, value in valid_updates.items():
                setattr(map_data, key, value)

            session.commit()
            return 0

    except ValueError as ve:
        core_warn(f"参数格式错误: {str(ve)}")
        return 1006
    except Exception as e:
        core_warn(f"修改失败: {str(e)}")
        session.rollback()
        return 1006


def user_change_map(mapid_str: str, user_id: str, arcs: Optional[Dict] = None) -> int:
    """

    """
    # 记录函数调用入口
    core_trace(f"Function entry: user_change_map(mapid={mapid_str}, user={user_id}, arcs={arcs})")

    # 参数验证阶段
    try:
        mapid = UUID(mapid_str)
        core_trace(f"MapID转换成功: {mapid}")
    except (ValueError, TypeError) as e:
        core_error(f"无效的MapID格式: {mapid_str} | 错误: {str(e)}")
        return 1002

    try:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        if not isinstance(user_uuid, UUID):
            raise ValueError
        core_trace(f"用户ID转换成功: {user_uuid}")
    except (ValueError, TypeError) as e:
        core_error(f"无效的用户ID格式: {user_id} | 错误: {str(e)}")
        return 2001

    try:
        with Session(engine) as session:
            # 用户存在性检查
            user = session.get(User, user_uuid)
            if not user:
                core_error(f"用户不存在: {user_uuid}")
                return 2001
            core_trace(f"用户验证通过: {user_uuid}")

            # 地图存在性检查
            map_obj = session.get(Map, mapid)
            if not map_obj:
                core_error(f"地图不存在: {mapid}")
                return 1002
            core_info(f"开始处理地图修改 | 地图: {mapid} | 用户: {user_uuid}")

            # 字段更新处理
            if arcs:
                allowed_fields = {'map_name', 'map_type', 'media_type', 'description', 'public_time'}
                changes = {}
                core_trace(f"待更新字段: {set(arcs.keys())}")

                for field in allowed_fields:
                    if field in arcs:
                        new_value = arcs[field]

                        # 特殊处理时间字段
                        if field == 'public_time':
                            if isinstance(new_value, str):
                                try:
                                    new_value = datetime.datetime.fromisoformat(new_value)
                                    core_trace(f"时间格式转换成功: {new_value}")
                                except ValueError as e:
                                    core_warn(f"忽略无效时间格式: {new_value} | 字段: {field}")
                                    continue
                            elif not isinstance(new_value, datetime.datetime):
                                core_warn(f"非预期时间类型: {type(new_value)} | 字段: {field}")
                                continue

                        # 记录字段变更
                        original_value = getattr(map_obj, field)
                        if original_value != new_value:
                            changes[field] = {
                                'old': original_value,
                                'new': new_value
                            }
                            setattr(map_obj, field, new_value)
                            core_info(f"字段更新: {field} | 旧值: {original_value} | 新值: {new_value}")

                # 记录变更历史
                if changes:
                    map_change = MapChange(
                        mapid=mapid,
                        uid=user_uuid,
                         ** {k: v['new'] for k, v in changes.items()}
                    )
                    session.add(map_change)
                    core_info(f"创建变更记录: {map_change.change_id}")

                    session.commit()
                    core_info(f"事务提交成功 | 修改字段数: {len(changes)}")
                else:
                    core_trace("未检测到有效变更，跳过提交")

            return 0

    except Exception as e:
        core_fatal(f"数据库操作异常 | 错误类型: {type(e).__name__} | 详情: {str(e)}")
        raise  # 根据业务需求决定是否抛出异常
    finally:
        core_trace("结束地图修改流程")

def get_change_details(mapid_str: Optional[str],user_id : Optional[str]) -> Tuple[int, List]:
    """
    :param mapid_str:
    :param user_id:
    :return: status:
        0 OK
        1002 地图不存在
        2001 用户不存在
            details:
        [{'uid':...,'mapid':...,'user_name':...,'map_name':...,'其他'}]

    """
    # 通过依赖注入或全局engine获取session（此处需要你实际配置数据库连接）
    with Session(engine) as session:
        # --------------------------
        # 1. 参数验证与UUID转换
        # --------------------------
        mapid_uuid, user_uuid = None, None

        # 处理地图ID
        if mapid_str.strip():
            try:
                mapid_uuid = UUID(mapid_str)
                if not session.get(Map, mapid_uuid):
                    return (1002, [])  # 地图不存在
            except ValueError:
                return (1002, [])  # 无效的UUID格式

        # 处理用户ID
        if user_id.strip():
            try:
                user_uuid = UUID(user_id)
                if not session.get(User, user_uuid):
                    return (2001, [])  # 用户不存在
            except ValueError:
                return (2001, [])  # 无效的UUID格式

        # --------------------------
        # 2. 构建动态查询条件
        # --------------------------
        query = select(MapChange)
        conditions = []

        if mapid_uuid:
            conditions.append(MapChange.mapid == mapid_uuid)
        if user_uuid:
            conditions.append(MapChange.uid == user_uuid)

        if conditions:
            query = query.where(*conditions)

        # --------------------------
        # 3. 获取并处理查询结果
        # --------------------------
        changes = session.exec(query).all()
        details = []

        for change in changes:
            # 关联查询用户和地图基础信息
            user = session.get(User, change.uid)
            map_data = session.get(Map, change.mapid)

            # 构造基础信息（已通过前期验证，此处不会为空）
            detail = {
                "uid": str(change.uid),
                "mapid": str(change.mapid),
                "user_name": user.name,
                "map_name": map_data.map_name,
                "change_time": change.change_time.isoformat()
            }

            # 动态添加非空修改字段
            if change.public_time:
                detail["public_time"] = change.public_time.isoformat()
            if change.map_name:
                detail["new_map_name"] = change.map_name
            if change.map_type:
                detail["new_map_type"] = change.map_type
            if change.media_type:
                detail["new_media_type"] = change.media_type
            if change.description:
                detail["new_description"] = change.description

            details.append(detail)

        return (0, details)

# test/ use_example:
if __name__ == "__main__":
    mat1 = cv2.imread("E:/dev/MapCollector/test/maps/ChinaMap.jpeg")
    status, id1 = add_map("中国地图", mat1)
    if status == 0 :
        print(type(id1))
        print(id1)
    status, id2 = add_map("中国地图", cv2.imread("E:/dev/MapCollector/test/maps/ChinaViewMap.jpg"))
    status, l1 = get_map_list()
    id1 = l1[0][0]
    [print(l) for l in l1]
    _ = change_map(id1, {"map_type": "地形图", "media_type": "纸质", "description": "网上找的一张中国地图", "public_time": "2023-07-20 14:30:45"})
    _, map1, args = get_map(id1)
    print(map1)
    cv2.imshow(args["map_name"],map1)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print(args)



