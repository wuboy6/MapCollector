from file_system.db import engine
from file_system.models import Map
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
        返回: (status_code, cv2_image)
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



