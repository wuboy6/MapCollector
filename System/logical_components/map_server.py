import file_system as fs
from mat_reader import MatReader
from dispatcher import ThreadPool
import atexit
from Log import core_trace, core_info, core_warn, core_error, core_fatal
from search_engine import MapSearchEngine
from typing import List, Tuple, Dict
import cv2

class MapServer:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not self.__initialized:
            self.__initialized = True
            self.__init_resources()
            atexit.register(self.__cleanup)

    def __init_resources(self):
        """初始化地图服务资源"""
        self._mat_reader = MatReader
        self._thread_pool = ThreadPool(4)
        status, self._maps = fs.get_map_list()
        if status:
            core_error(f"status:{status} 地图数据获取失败")
            self._maps = []
        self.search_engine = MapSearchEngine(self._maps)  # 共享内存
        core_info("MapServer初始化完成")

    def get_map_list(self) -> List:
        return self._maps[:]

    def get_map(self, mapid) -> Tuple[cv2.Mat|None, Dict]:
        status, mat, content = fs.get_map(mapid)
        return mat, content

    def search(self,query : str, top_n : int = 10) -> List[str]:
        return self.search_engine.search_maps(query, top_n)



    def __cleanup(self):
        """安全释放资源"""
        core_trace("正在清理地图服务资源...")

    #def get_map_type_list(self) -> List[Dict[str: str]]:


map_server = MapServer()


if __name__ == "__main__":

    assert id(map_server.search_engine.maplist) == id(map_server._maps)
    tops = map_server.search("矢量")
    mat, content = map_server.get_map(tops[0])
    print(len(tops))
    print(tops[0])
    cv2.imshow("top1", mat)
    cv2.waitKey(0)
