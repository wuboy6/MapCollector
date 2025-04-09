import base64
import cv2
import numpy as np

def encode_image(mat: np.ndarray) -> str:
    """将 numpy 数组图像编码为 base64 字符串"""
    if mat is None:
        return ""
    _, buffer = cv2.imencode('.jpg', mat)
    return base64.b64encode(buffer).decode('utf-8')