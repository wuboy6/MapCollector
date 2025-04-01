import cv2
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Optional
from config import PROJECT_ROOT
from file_system.db import engine
from file_system.models import Map
from sqlmodel import Session
import uuid
import datetime
from logical_components.mat_reader import MatReader
from file_system import add_map, change_map, get_map_list

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("map_importer")

MEDIA_TYPE_MAPPING = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.bmp': 'image/bmp',
    '.shp': 'image/shp'
}





def import_maps(source_dir: Path) -> None:
    """主导入函数"""
    if not source_dir.exists():
        logger.error(f"源目录不存在: {source_dir}")
        return

    mat_reader = MatReader()

    # 遍历所有地图类型文件夹
    for map_type_dir in source_dir.iterdir():
        if not map_type_dir.is_dir():
            continue

        map_type = map_type_dir.name
        logger.info(f"正在处理地图类型: {map_type}")

        # 遍历该类型下所有文件
        for img_file in map_type_dir.glob('*'):
            if not img_file.is_file():
                continue

            # 解析文件信息
            map_name = img_file.stem
            file_ext = img_file.suffix.lower()
            media_type = MEDIA_TYPE_MAPPING.get(file_ext, 'application/octet-stream')

            if file_ext not in MEDIA_TYPE_MAPPING:
                continue

            # 读取图像文件
            cv_image = mat_reader.read_data(str(img_file))
            if cv_image is None:
                continue

            _,id = add_map(map_name, cv_image)
            change_map(id, {"map_type":str(map_type), "media_type":str(media_type), "description": f"导入{map_name},用于调试"})




if __name__ == "__main__":
    maps_dir = PROJECT_ROOT / "test/maps/"
    import_maps(maps_dir)
    print("地图导入完成")
    map_list = get_map_list()
    for d in map_list:
        print(d)
