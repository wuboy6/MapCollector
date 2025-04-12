import file_system as fs
from logical_components.mat_reader import MatReader
from dispatcher import ThreadPool
import atexit
from Log import core_trace, core_info, core_warn, core_error, core_fatal
from logical_components.search_engine import MapSearchEngine
from typing import List, Tuple, Dict, Optional
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
        self._mat_reader = MatReader()
        self._thread_pool = ThreadPool(4)
        status, self._maps = fs.get_map_list()
        if status:
            core_error(f"status:{status} 地图数据获取失败")
            self._maps = []
        self.search_engine = MapSearchEngine(self._maps)  # 共享内存
        core_info("MapServer初始化完成")

    def load_mat(self, file_pate: str):
        return self._mat_reader.read_data(file_pate)

    def add_map(self, file_path: str, map_name: str) -> Tuple[int, str]:
        mat = self.load_mat(file_path)
        details =  fs.add_map(map_name, mat)
        _, self._maps = fs.get_map_list()
        self.search_engine = MapSearchEngine(self._maps)
        return details

    def change_map(self,mapid_str: str, arcs: Optional[Dict] = None) -> int :
        return fs.change_map(mapid_str, arcs)
#OK
    def get_map_list(self) -> List:
        return self._maps[:]


    def get_map(self, mapid) -> Tuple[cv2.Mat|None, Dict]:
        status, mat, content = fs.get_map(mapid)
        return mat, content

    def search(self,query_name: str="", query_type: str="", query_media:str="", query_desc : str="", top_n : int = 10) -> List[str]:
        return self.search_engine.search_maps(query_name, query_type, query_media, query_desc, num_results=top_n)



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
