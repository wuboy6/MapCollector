import cv2
import numpy as np
import rasterio
from typing import Union, List
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from shapely.geometry import shape
import fiona


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
        self.line_width = vector_line_width
        self.vector_color = vector_color
        self.dpi = dpi

    def read_data(self, file_path: str) -> Union[cv2.Mat, np.array]:
        """统一数据读取入口"""
        try:
            if self._is_raster(file_path):
                return self._read_raster(file_path)
            elif self._is_vector(file_path):
                return self._render_vector(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to process file: {file_path} - {str(e)}")

    def _is_raster(self, path: str) -> bool:
        return path.lower().endswith(('.tif', '.tiff', '.png', '.jpg', '.jpeg'))

    def _is_vector(self, path: str) -> bool:
        return path.lower().endswith(('.shp', '.geojson'))

    def _read_raster(self, path: str) -> np.ndarray:
        """读取栅格数据"""
        try:
            with rasterio.open(path) as src:
                data = src.read()
                if data.shape[0] == 1:
                    return data[0].astype(np.uint8)
                else:
                    return cv2.merge([
                        data[i].astype(np.uint8)
                        for i in range(min(3, data.shape[0]))
                    ])[:, :, ::-1]
        except Exception as e:
            raise RuntimeError(f"Raster read failed: {path} - {str(e)}")

    def _render_vector(self, path: str) -> np.ndarray:
        """高质量矢量渲染"""
        try:
            geometries = self._parse_vector(path)
            bounds = self._get_combined_bounds(geometries)

            height_px = 1080
            width_px = int(height_px * (bounds[2] - bounds[0]) / (bounds[3] - bounds[1]))

            fig = Figure(figsize=(width_px / self.dpi, height_px / self.dpi), dpi=self.dpi)
            ax = fig.add_axes((0., 0., 1., 1.), frameon=False)
            ax.set_xlim(bounds[0], bounds[2])
            ax.set_ylim(bounds[1], bounds[3])
            ax.axis('off')

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
            raise RuntimeError(f"Vector render failed: {path} - {str(e)}")

    def _parse_vector(self, path: str) -> List:
        """解析矢量文件"""
        try:
            with fiona.open(path) as src:
                return [shape(feat['geometry']) for feat in src]
        except Exception as e:
            raise RuntimeError(f"Vector parse failed: {path} - {str(e)}")

    def _get_combined_bounds(self, geometries: List) -> tuple:
        """计算合并边界"""
        xmins, ymins, xmaxs, ymaxs = zip(*[geom.bounds for geom in geometries])
        return min(xmins), min(ymins), max(xmaxs), max(ymaxs)