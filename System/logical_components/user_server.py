import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, Tuple, List
from Log import  core_trace, core_info, core_warn, core_error, core_fatal
import hashlib
import file_system as fs
import os
from logical_components.map_server import map_server
import cv2
import numpy as np

# ================= 用户视图基类及子类实现 =================
class UserView(ABC):
    def __init__(self, user_id: str, user_email: str):
        self.user_id = user_id
        self.user_email = user_email
        self.last_active = time.time()
        self._lock = threading.RLock()

    def update_activity(self):
        """更新最后活跃时间"""
        with self._lock:
            self.last_active = time.time()

    @abstractmethod
    def has_permission(self, permission: str) -> bool:
        """检查用户权限"""
        pass

class NormalUser(UserView):
    def __init__(self, user_id: str, user_email: str):
        super().__init__(user_id, user_email)
        self._mapid_read_now: str = ""          # 当前查看地图ID
        self._map_list: List[str] = []          # 待查看地图队列
        self._map_list_index : int = 0 #索引
        self._map_lock = threading.RLock()      # 独立状态锁
        self.details = fs.get_user_model(user_id)[1]
        last_read = self.details["last_read"]
        if(last_read):
            self._mapid_read_now = last_read

    @property
    def current_map(self) -> str:
        """获取当前查看地图（线程安全）"""
        with self._map_lock:
            return self._mapid_read_now

    @current_map.setter
    def current_map(self, map_id: str):
        """设置当前查看地图（线程安全）"""
        with self._map_lock:
            self._mapid_read_now = map_id
            self.update_activity()  # 更新活跃时间

    def set_current_map(self, map_id: str):
        """设置当前查看地图（线程安全）"""
        with self._map_lock:
            self._mapid_read_now = map_id
            fs.set_user_model(self.user_id, {'last_read': self._mapid_read_now})
            self.update_activity()  # 更新活跃时间

    @property
    def pending_maps(self) -> List[str]:
        """获取待查看列表（线程安全）"""
        with self._map_lock:
            return self._map_list.copy()  # 返回副本避免外部修改

    def _set_pending_map(self, map_list: List[str]):
        """添加地图到待查看队列（线程安全）"""
        with self._map_lock:
            self._map_list = map_list[:]

    def search(self, query_name: str="", query_type: str="", query_media:str="", query_desc : str="", top_n: int = 10):
        with self._map_lock:
            self.update_activity()
            map_list = map_server.search(query_name, query_type, query_media, query_desc, top_n=top_n)
            self._map_list = map_list[:]
            self._map_list_index = 0
            self.current_map = self._map_list[0] if self._map_list else self.current_map
            fs.set_user_model(self.user_id,{'last_read': self._mapid_read_now})

    def next(self) -> str:
        with self._map_lock:
            self.update_activity()
            if self._map_list:
                if (self._map_list_index + 1 < len(self._map_list)):
                    self._map_list_index += 1
                    self._mapid_read_now = self._map_list[self._map_list_index]
                    fs.set_user_model(self.user_id, {'last_read': self._mapid_read_now})
                return self._mapid_read_now
            else :
                return ""

    def just(self) -> str:
        with self._map_lock:
            self.update_activity()
            self._mapid_read_now = self._map_list[self._map_list_index]
            fs.set_user_model(self.user_id, {'last_read': self._mapid_read_now})
            return self._mapid_read_now

    def before(self) -> str:
        with self._map_lock:
            self.update_activity()
            if self._map_list:
                if (self._map_list_index  > 0):
                    self._map_list_index -= 1
                    self._mapid_read_now = self._map_list[self._map_list_index]
                    fs.set_user_model(self.user_id, {'last_read': self._mapid_read_now})
                return self._mapid_read_now
            else :
                return ""

    def get_map_details_now(self) -> Tuple[Optional[np.array], Dict]:
        with self._map_lock:
            self.update_activity()
            if self._mapid_read_now:
                status, mat, details = fs.get_map(self._mapid_read_now)
                return mat, details
            else:
                return None, {}

    def get_notes_of_current_map(self) -> Optional[List[Dict]]:
        with self._map_lock:
            self.update_activity()
            status, ld = fs.get_notes(mapid=self._mapid_read_now, size=20)
            if not status:
                return ld
            else:
                return None

    def write_note(self, note: str) -> int:
        with self._map_lock:
            self.update_activity()
            status,_ = fs.add_note(mapid_str=self._mapid_read_now, uid_str=self.user_id, context=note)
            return status
#OK
    def reset_user_name(self, new_name: str)-> int:
        with self._map_lock:
            self.update_activity()
            status = fs.set_user_model(self.user_id, {"user_name":new_name})
            return status
#OK
    def reset_user_email(self, new_email: str)-> int:
        with self._map_lock:
            self.update_activity()
            status = fs.set_user_model(self.user_id, {"user_email":new_email})
            return status




    def remove_pending_map(self, map_id: str) -> bool:
        """从队列移除地图（线程安全）"""
        with self._map_lock:
            if map_id in self._map_list:
                self._map_list.remove(map_id)
                self.update_activity()
                return True
            return False

    def has_permission(self, permission: str) -> bool:
        return permission in ["read", "write"]

    def user_change_map(self,mapid_str: str, arcs: Optional[Dict] = None) -> int:
        return fs.user_change_map(mapid_str, self.user_id, arcs)

    def get_change_details_by_current_map(self) -> Tuple[int, List]:
        return fs.get_change_details(user_id=self.user_id, mapid_str=self.current_map)

    def get_change_details(self) -> Tuple[int, List]:
        return fs.get_change_details(user_id=self.user_id, mapid_str=None)

    def get_current_map_full_change_details(self)-> Tuple[int, List]:
        return fs.get_change_details(mapid_str=self.current_map, user_id=None)

class SuperUser(UserView):
    def has_permission(self, permission: str) -> bool:
        # 超级用户拥有所有权限
        return True

# ================= 用户服务单例实现 =================
class UserServer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance.__init__()
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._active_users: Dict[str, UserView] = {}
            self._cleanup_interval = 300  # 5分钟清理一次
            self._timeout = 1800  # 30分钟无活动判定为不活跃
            self._running = True
            self._lock = threading.RLock()
            self._cleanup_thread = threading.Thread(target=self._cleanup_loop)
            self._cleanup_thread.start()
            self._initialized = True
            self.map_server = map_server
            core_info("成功创建用户服务器")


    def _cleanup_loop(self):
        """后台清理线程"""
        while self._running:
            time.sleep(self._cleanup_interval)
            self.remove_inactive_users()

    def get_user_name(self, uid: str) -> str: #OK
        with self._lock:
            _, details = fs.get_user_model(uid)
            return details["user_name"]

    def register_user(self,  #OK
                      user_email: str,
                      user_pwd: str,
                      user_type: Type[UserView] = NormalUser) -> Optional[UserView]:

        """注册或更新用户"""
        with self._lock:
            status, user_id = self.login(user_email, user_pwd)

            if user_id in self._active_users:
                user = self._active_users[user_id]
                user.update_activity()
                return user

            status, user_details = fs.get_user_model(user_id)
            if status:
                return None
            user_email = user_details['user_email']


            user = user_type(user_id, user_email)
            self._active_users[user_id] = user
            return user

    def get_active_user(self, user_id: str) -> Optional[NormalUser]:
        """获取用户视图"""
        with self._lock:
            return self._active_users.get(user_id)

    def remove_inactive_users(self):
        """移除不活跃用户"""
        threshold = time.time() - self._timeout
        with self._lock:
            inactive = [
                uid for uid, user in self._active_users.items()
                if user.last_active < threshold
            ]
            for uid in inactive:
                del self._active_users[uid]
            return len(inactive)

    def shutdown(self):
        """关闭服务"""
        self._running = False
        self._cleanup_thread.join()

    def register(self, email: str, password: str) -> Tuple[int, str]: #OK
        """
        用户注册功能
        返回: (状态码, 用户UUID)
        状态码:
          - 0: 注册成功
          - 2002: 用户已存在
          - 3001: 密码强度不足
          - 1008: 系统错误
        """
        # 密码强度校验
        if not self._validate_password(password):
            core_warn(f"弱密码: {email}")
            return (3001, "")

        # 生成安全哈希
        hashed_pw = self._hash_password(password)

        # 创建数据库记录
        status, uid = fs.create_user(email, hashed_pw)

        if status == 0:
            core_info(f"用户注册成功: {email}")

            return (0, uid)
        else:
            return (status, "")

    def login(self, email: str, password: str) -> Tuple[int, str]: #OK
        """
        用户登录功能
        返回: (状态码, 用户UUID)
        状态码:
          - 0: 登录成功
          - 2001: 用户不存在
          - 3002: 密码错误
          - 1007: 系统错误
        """
        # 获取数据库记录
        status, uid, stored_hash = fs.get_user_pw(email)

        if status != 0:
            return (status, "")

        # 密码验证
        if not self._verify_password(password, stored_hash):
            core_warn(f"密码错误: {email}")
            return (3002, "")


        core_info(f"用户登录成功: {email}")
        return (0, uid)

    def _validate_password(self, password: str) -> bool: #暂时不开启密码复杂度验证
        """密码强度校验 (至少8字符，包含大小写和数字)"""
        # if len(password) < 8:
        #     return False
        # if not any(c.isupper() for c in password):
        #     return False
        # if not any(c.islower() for c in password):
        #     return False
        # return any(c.isdigit() for c in password)
        return True

    def _hash_password(self, password: str) -> str:
        """使用PBKDF2-HMAC-SHA256进行安全哈希"""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return f"{salt.hex()}:{pwd_hash.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """验证密码哈希"""
        try:
            salt, correct_hash = stored_hash.split(':')
            salt_bytes = bytes.fromhex(salt)
            new_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt_bytes,
                100000
            )
            return new_hash.hex() == correct_hash
        except:
            return False

    def _is_super_user(self, email: str) -> bool:
        """判断超级用户（示例：管理员邮箱后缀）"""
        return email.endswith("@admin.com")


# ================= 使用示例 =================
if __name__ == "__main__":
    server = UserServer()

    # _, uid = server.register(email = "2287401905@qq.com", password="www123666")

    # 注册普通用户
    user1 = server.register_user("2287401905@qq.com", "www123666", NormalUser)

    # 注册超级用户
    # admin = server.register_user("admin", "Admin", SuperUser)

    # 权限验证
    print(user1.has_permission("delete"))  # 输出: False
    # print(admin.has_permission("delete"))  # 输出: True

    # 获取用户
    # same_user = server.get_user()
    # print(same_user.username)  # 输出: Alice

    # 自动清理演示
    print("活跃用户数:", len(server._active_users))  # 输出: 2
    user1.last_active = time.time() - 2000  # 修改最后活跃时间
    server.remove_inactive_users()
    print("清理后用户数:", len(server._active_users))  # 输出: 1

    server.shutdown()