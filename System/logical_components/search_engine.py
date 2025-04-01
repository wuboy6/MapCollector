from typing import List, Dict, Set
import difflib
from Log import  core_trace, core_info, core_warn, core_error, core_fatal


class MapSearchEngine:
    """
    一个用于通过地图名称、地图类型、介质类型、介绍等信息进行搜索的类。
    """

    def __init__(self, maplist):
        """
        :param maplist: 包含字典的列表，结构如下：
                       [
                           {
                               "mapid": str,
                               "map_name": str,
                               "map_type": str,
                               "media_type": str,
                               "description": str
                           },
                           ...
                       ]
        在Python中，列表默认按引用传递，因而能够与调用者共享内存。
        """
        core_info("初始化 MapSearchEngine，并存储 maplist 引用。")
        self.maplist = maplist  # 与外部共享内存

    def _calculate_similarity(self, target_str, query_str):
        """
        使用 SequenceMatcher 来计算两个字符串之间的相似度，返回 0~1 的分数
        """
        return difflib.SequenceMatcher(None, target_str, query_str).ratio()

    def _get_map_score(self, map_info, query_name="", query_type="", query_media="", query_desc=""):
        """
        根据给定的查询条件计算地图信息的综合匹配度分数
        """
        score = 0.0

        # 对名称进行相似度判断
        if query_name:
            score += self._calculate_similarity(map_info.get("map_name", ""), query_name)

        # 对地图类型进行相似度判断
        if query_type:
            score += self._calculate_similarity(map_info.get("map_type", ""), query_type)

        # 对介质类型进行相似度判断
        if query_media:
            score += self._calculate_similarity(map_info.get("media_type", ""), query_media)

        # 对介绍进行相似度判断
        if query_desc:
            score += self._calculate_similarity(map_info.get("description", ""), query_desc)

        return score

    def search_maps(self,
                    query : str,
                    num_results : int=5) -> List[str]:
        """
        根据给定查询信息，返回相似度最高的地图ID集合（不超过 num_results 个）
        :param query_name: 地图名称的查询关键词
        :param query_type: 地图类型的查询关键词
        :param query_media: 地图介质类型的查询关键词
        :param query_desc: 地图介绍的查询关键词
        :param num_results: 指定返回结果的最大数量
        :return: 按相似度排序后的 mapid 列表
        """
        query_name = query
        query_type = query
        query_media = query
        query_desc = query
        core_trace(f"开始搜索，查询条件：name={query_name} type={query_type} media={query_media} desc={query_desc}")

        # 对地图进行评分
        scored_maps = []
        for map_info in self.maplist:
            score = self._get_map_score(
                map_info,
                query_name=query_name,
                query_type=query_type,
                query_media=query_media,
                query_desc=query_desc
            )
            scored_maps.append((map_info["mapid"], score))

        # 根据分数排序，并截取 top N
        scored_maps.sort(key=lambda x: x[1], reverse=True)
        top_results = scored_maps[:num_results]

        core_info(f"搜索完成，共匹配到 {len(scored_maps)} 条，返回前 {len(top_results)} 条。")
        # 返回 mapid 列表
        return [item[0] for item in top_results]