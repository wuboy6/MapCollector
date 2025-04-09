from api.base_api import UserServer, MapServer
from utils import encode_image
from typing import Optional, Dict, List, Tuple

# 单例实例
user_server = UserServer()
map_server = MapServer()

# 用户服务
def register_user(email: str, password: str) -> Tuple[int, str]:
    return user_server.register(email, password)

def login_user(email: str, password: str) -> Tuple[int, str]:
    return 0, user_server.register_user(email, password).user_id

def get_user_name(uid: str) -> str:
    return user_server.get_user_name(uid)

def reset_user_name(uid: str, new_name: str) -> int:
    user = user_server.get_active_user(uid)
    if user:
        return user.reset_user_name(new_name)
    return 1007  # 用户不存在

def reset_user_email(uid: str, new_email: str) -> int:
    user = user_server.get_active_user(uid)
    if user:
        return user.reset_user_email(new_email)
    return 1007  # 用户不存在

# 地图服务
def get_map_list() -> List[Dict]:
    return map_server.get_map_list()

def get_map_details(mapid: str) -> Dict:
    mat, details = map_server.get_map(mapid)
    image_base64 = encode_image(mat)
    return {"mapid": mapid, "details": details, "image": image_base64}

def add_map(file_path: str, map_name: str) -> Tuple[int, str]:
    return map_server.add_map(file_path, map_name)

# 用户视图服务
def get_change_details_by_current_map(uid: str) -> Tuple[int, List]:
    user = user_server.get_active_user(uid)
    return user.get_change_details_by_current_map()


def get_change_details(uid: str) -> Tuple[int, List]:
    user = user_server.get_active_user(uid)
    return user.get_change_details()

def get_current_map_full_change_details(uid: str) -> Tuple[int, List]:
    user = user_server.get_active_user(uid)
    return user.get_current_map_full_change_details()

def set_current_map(uid: str, mapid: str) -> None:
    user = user_server.get_active_user(uid)
    user.set_current_map(mapid)

def user_search(uid: str, query_name: str, query_type: str, query_media: str, query_desc: str, top_n: int) -> int:
    user = user_server.get_active_user(uid)
    if user:
        user.search(query_name, query_type, query_media, query_desc, top_n)
        return 0
    return 1007  # 用户不存在

def user_next(uid: str) -> str:
    user = user_server.get_active_user(uid)
    if user:
        return user.next()
    return ""

def user_before(uid: str) -> str:
    user = user_server.get_active_user(uid)
    if user:
        return user.before()
    return ""

def get_current_map_details(uid: str) -> Dict:
    user = user_server.get_active_user(uid)
    if user:
        mat, details = user.get_map_details_now()
        image_base64 = encode_image(mat)
        return {"mapid": user.current_map, "details": details, "image": image_base64}
    return {}

def get_current_map_notes(uid: str) -> Optional[List[Dict]]:
    user = user_server.get_active_user(uid)
    if user:
        return user.get_notes_of_current_map()
    return None

def write_note(uid: str, note: str) -> int:
    user = user_server.get_active_user(uid)
    if user:
        return user.write_note(note)
    return 1007  # 用户不存在

def user_change_map(uid: str, mapid: str, arcs: Optional[Dict]) -> int:
    user = user_server.get_active_user(uid)
    if user:
        return user.user_change_map(mapid, arcs)
    return 1007  # 用户不存在