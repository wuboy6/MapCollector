import cv2
import numpy as np
import rasterio
from typing import Union, List
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from shapely.geometry import shape
import fiona
from Log import core_trace, core_info, core_warn, core_error, core_fatal


class MatReader:
    """
    地理数据读取器 (高质量矢量渲染版)
    功能：
    - 栅格数据：支持 TIFF/PNG/JPG
    - 矢量数据：支持 Shapefile/GeoJSON
    - 矢量渲染使用 matplotlib 引擎
    """

    def __init__(self,
                 vector_line_width: float = 1.5,
                 vector_color: str = 'black',
                 dpi: int = 100):
        core_info(f"初始化地图读取器: line_width={vector_line_width}, color={vector_color}, dpi={dpi}")
        self.line_width = vector_line_width
        self.vector_color = vector_color
        self.dpi = dpi

    def read_data(self, file_path: str) -> Union[cv2.Mat, np.array]:
        """统一数据读取入口"""
        core_trace(f"开始处理文件: {file_path}")
        try:
            if self._is_raster(file_path):
                core_info(f"识别为栅格文件: {file_path}")
                return self._read_raster(file_path)
            elif self._is_vector(file_path):
                core_info(f"识别为矢量文件: {file_path}")
                return self._render_vector(file_path)
            else:
                core_error(f"不支持的格式: {file_path}")
                raise ValueError(f"不支持的格式: {file_path}")
        except Exception as e:
            core_fatal(f"文件处理失败: {file_path} - {str(e)}")
            raise

    def _is_raster(self, path: str) -> bool:
        result = path.lower().endswith(('.tif', '.tiff', '.png', '.jpg', '.jpeg'))
        core_trace(f"检测栅格格式: {path} -> {result}")
        return result

    def _is_vector(self, path: str) -> bool:
        result = path.lower().endswith(('.shp', '.geojson'))
        core_trace(f"检测矢量格式: {path} -> {result}")
        return result

    def _read_raster(self, path: str) -> np.ndarray:
        """读取栅格数据"""
        try:
            core_info(f"打开栅格文件: {path}")
            with rasterio.open(path) as src:
                data = src.read()
                if data.shape[0] == 1:
                    core_info(f"单波段栅格处理: {path}")
                    return data[0].astype(np.uint8)
                else:
                    core_info(f"合并多波段数据: {path} ({data.shape[0]} 波段)")
                    return cv2.merge([
                        data[i].astype(np.uint8)
                        for i in range(min(3, data.shape[0]))
                    ])[:, :, ::-1]
        except Exception as e:
            core_error(f"栅格读取失败: {path} - {str(e)}")
            raise

    def _render_vector(self, path: str) -> np.ndarray:
        """高质量矢量渲染"""
        try:
            core_info(f"开始渲染矢量: {path}")
            geometries = self._parse_vector(path)
            core_info(f"解析到 {len(geometries)} 个几何要素")

            bounds = self._get_combined_bounds(geometries)
            core_info(f"计算边界范围: {bounds}")

            height_px = 1080
            width_px = int(height_px * (bounds[2] - bounds[0]) / (bounds[3] - bounds[1]))
            core_info(f"设置画布尺寸: {width_px}x{height_px}")

            fig = Figure(figsize=(width_px / self.dpi, height_px / self.dpi), dpi=self.dpi)
            ax = fig.add_axes((0., 0., 1., 1.), frameon=False)
            ax.set_xlim(bounds[0], bounds[2])
            ax.set_ylim(bounds[1], bounds[3])
            ax.axis('off')

            core_info("开始绘制矢量要素")
            for geom in geometries:
                if geom.geom_type == 'Polygon':
                    x, y = geom.exterior.xy
                    ax.plot(x, y,
                            linewidth=self.line_width,
                            color=self.vector_color,
                            solid_capstyle='round',
                            antialiased=True)

            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            return cv2.cvtColor(
                np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8).reshape((height_px, width_px, 4)),
                cv2.COLOR_RGBA2BGR
            )
        except Exception as e:
            core_error(f"矢量渲染失败: {path} - {str(e)}")
            raise

    def _parse_vector(self, path: str) -> List:
        """解析矢量文件"""
        try:
            core_info(f"打开矢量文件: {path}")
            with fiona.open(path) as src:
                geometries = [shape(feat['geometry']) for feat in src]
                core_info(f"成功解析 {len(geometries)} 个几何要素")
                return geometries
        except Exception as e:
            core_error(f"矢量解析失败: {path} - {str(e)}")
            raise

    def _get_combined_bounds(self, geometries: List) -> tuple:
        """计算合并边界"""
        try:
            xmins, ymins, xmaxs, ymaxs = zip(*[geom.bounds for geom in geometries])
            bounds = (min(xmins), min(ymins), max(xmaxs), max(ymaxs))
            core_trace(f"合并边界计算结果: {bounds}")
            return bounds
        except Exception as e:
            core_error(f"边界计算失败: {str(e)}")
            raise

if __name__ == "__main__":
    from config import PROJECT_ROOT
    # 创建读取器 (可自定义样式)
    reader = MatReader(
        vector_line_width=2.0,
        vector_color='darkred',
        dpi=150
    )

    path_name = str(PROJECT_ROOT / "test/maps/矢量地图/WHRD.shp")
    print(path_name)
    # 读取矢量文件
    vector_img = reader.read_data(str(PROJECT_ROOT / "test/maps/矢量地图/WHHP_2015.shp"))
    jpg_img = reader.read_data(str(PROJECT_ROOT / "test/maps/中国地图/中国标准地图.jpeg"))

    # 显示结果
    cv2.imshow("High Quality Vector", jpg_img)
    cv2.imshow("Victor", vector_img)
    cv2.waitKey(0)