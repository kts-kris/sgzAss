#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用工具函数模块

提供文件操作、图像处理、坐标转换、数据验证等实用功能。
"""

import os
import json
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional, Union
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from loguru import logger

from ..models import Element, MatchResult, ValidationError


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path: 目录路径对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """获取时间戳字符串
    
    Args:
        format_str: 时间格式
        
    Returns:
        str: 时间戳字符串
    """
    return datetime.now().strftime(format_str)


def generate_filename(prefix: str = "", suffix: str = "", 
                     extension: str = "", include_timestamp: bool = True) -> str:
    """生成文件名
    
    Args:
        prefix: 前缀
        suffix: 后缀
        extension: 扩展名
        include_timestamp: 是否包含时间戳
        
    Returns:
        str: 生成的文件名
    """
    parts = []
    
    if prefix:
        parts.append(prefix)
    
    if include_timestamp:
        parts.append(get_timestamp())
    
    if suffix:
        parts.append(suffix)
    
    filename = "_".join(parts)
    
    if extension:
        if not extension.startswith('.'):
            extension = '.' + extension
        filename += extension
    
    return filename


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)
        
    Returns:
        str: 文件哈希值
    """
    hash_func = getattr(hashlib, algorithm.lower())()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> bool:
    """保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        indent: 缩进空格数
        
    Returns:
        bool: 保存是否成功
    """
    try:
        file_path = Path(file_path)
        ensure_dir(file_path.parent)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {e}")
        return False


def load_json(file_path: Union[str, Path]) -> Optional[Any]:
    """加载JSON文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Any: 加载的数据，失败时返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败: {e}")
        return None


def save_image(image: np.ndarray, file_path: Union[str, Path], 
              quality: int = 95) -> bool:
    """保存图像
    
    Args:
        image: 图像数组
        file_path: 保存路径
        quality: JPEG质量 (1-100)
        
    Returns:
        bool: 保存是否成功
    """
    try:
        file_path = Path(file_path)
        ensure_dir(file_path.parent)
        
        # 转换颜色空间 (OpenCV使用BGR，PIL使用RGB)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # 使用PIL保存
        pil_image = Image.fromarray(image_rgb)
        
        if file_path.suffix.lower() in ['.jpg', '.jpeg']:
            pil_image.save(file_path, 'JPEG', quality=quality)
        else:
            pil_image.save(file_path)
        
        return True
    except Exception as e:
        logger.error(f"保存图像失败: {e}")
        return False


def load_image(file_path: Union[str, Path]) -> Optional[np.ndarray]:
    """加载图像
    
    Args:
        file_path: 图像路径
        
    Returns:
        np.ndarray: 图像数组，失败时返回None
    """
    try:
        image = cv2.imread(str(file_path))
        if image is None:
            logger.error(f"无法加载图像: {file_path}")
        return image
    except Exception as e:
        logger.error(f"加载图像失败: {e}")
        return None


def resize_image(image: np.ndarray, target_size: Tuple[int, int], 
                keep_aspect_ratio: bool = True) -> np.ndarray:
    """调整图像大小
    
    Args:
        image: 输入图像
        target_size: 目标大小 (width, height)
        keep_aspect_ratio: 是否保持宽高比
        
    Returns:
        np.ndarray: 调整后的图像
    """
    if not keep_aspect_ratio:
        return cv2.resize(image, target_size)
    
    h, w = image.shape[:2]
    target_w, target_h = target_size
    
    # 计算缩放比例
    scale = min(target_w / w, target_h / h)
    
    # 计算新尺寸
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # 调整大小
    resized = cv2.resize(image, (new_w, new_h))
    
    # 如果需要，添加边框以达到目标尺寸
    if new_w != target_w or new_h != target_h:
        # 创建目标尺寸的黑色图像
        result = np.zeros((target_h, target_w, image.shape[2]), dtype=image.dtype)
        
        # 计算居中位置
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        
        # 将调整后的图像放置在中心
        result[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return result
    
    return resized


def crop_image(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    """裁剪图像
    
    Args:
        image: 输入图像
        x: 左上角x坐标
        y: 左上角y坐标
        width: 宽度
        height: 高度
        
    Returns:
        np.ndarray: 裁剪后的图像
    """
    h, w = image.shape[:2]
    
    # 确保坐标在有效范围内
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    x2 = max(x + 1, min(x + width, w))
    y2 = max(y + 1, min(y + height, h))
    
    return image[y:y2, x:x2]


def draw_rectangle(image: np.ndarray, x: int, y: int, width: int, height: int,
                  color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
    """在图像上绘制矩形
    
    Args:
        image: 输入图像
        x: 左上角x坐标
        y: 左上角y坐标
        width: 宽度
        height: 高度
        color: 颜色 (B, G, R)
        thickness: 线条粗细
        
    Returns:
        np.ndarray: 绘制后的图像
    """
    result = image.copy()
    cv2.rectangle(result, (x, y), (x + width, y + height), color, thickness)
    return result


def draw_circle(image: np.ndarray, x: int, y: int, radius: int = 5,
               color: Tuple[int, int, int] = (0, 0, 255), thickness: int = -1) -> np.ndarray:
    """在图像上绘制圆形
    
    Args:
        image: 输入图像
        x: 圆心x坐标
        y: 圆心y坐标
        radius: 半径
        color: 颜色 (B, G, R)
        thickness: 线条粗细，-1表示填充
        
    Returns:
        np.ndarray: 绘制后的图像
    """
    result = image.copy()
    cv2.circle(result, (x, y), radius, color, thickness)
    return result


def draw_text(image: np.ndarray, text: str, x: int, y: int,
             color: Tuple[int, int, int] = (255, 255, 255), 
             font_scale: float = 0.7, thickness: int = 2) -> np.ndarray:
    """在图像上绘制文本
    
    Args:
        image: 输入图像
        text: 文本内容
        x: 文本位置x坐标
        y: 文本位置y坐标
        color: 颜色 (B, G, R)
        font_scale: 字体大小
        thickness: 线条粗细
        
    Returns:
        np.ndarray: 绘制后的图像
    """
    result = image.copy()
    cv2.putText(result, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
               font_scale, color, thickness)
    return result


def calculate_distance(point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
    """计算两点间距离
    
    Args:
        point1: 第一个点 (x, y)
        point2: 第二个点 (x, y)
        
    Returns:
        float: 距离
    """
    x1, y1 = point1
    x2, y2 = point2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def calculate_center(x: int, y: int, width: int, height: int) -> Tuple[int, int]:
    """计算矩形中心点
    
    Args:
        x: 左上角x坐标
        y: 左上角y坐标
        width: 宽度
        height: 高度
        
    Returns:
        Tuple[int, int]: 中心点坐标 (x, y)
    """
    center_x = x + width // 2
    center_y = y + height // 2
    return center_x, center_y


def is_point_in_rect(point: Tuple[int, int], rect: Tuple[int, int, int, int]) -> bool:
    """检查点是否在矩形内
    
    Args:
        point: 点坐标 (x, y)
        rect: 矩形 (x, y, width, height)
        
    Returns:
        bool: 是否在矩形内
    """
    px, py = point
    rx, ry, rw, rh = rect
    
    return rx <= px <= rx + rw and ry <= py <= ry + rh


def calculate_overlap_area(rect1: Tuple[int, int, int, int], 
                          rect2: Tuple[int, int, int, int]) -> float:
    """计算两个矩形的重叠面积
    
    Args:
        rect1: 第一个矩形 (x, y, width, height)
        rect2: 第二个矩形 (x, y, width, height)
        
    Returns:
        float: 重叠面积
    """
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    # 计算重叠区域
    left = max(x1, x2)
    top = max(y1, y2)
    right = min(x1 + w1, x2 + w2)
    bottom = min(y1 + h1, y2 + h2)
    
    # 检查是否有重叠
    if left >= right or top >= bottom:
        return 0.0
    
    return (right - left) * (bottom - top)


def calculate_iou(rect1: Tuple[int, int, int, int], 
                 rect2: Tuple[int, int, int, int]) -> float:
    """计算两个矩形的IoU (Intersection over Union)
    
    Args:
        rect1: 第一个矩形 (x, y, width, height)
        rect2: 第二个矩形 (x, y, width, height)
        
    Returns:
        float: IoU值 (0-1)
    """
    overlap_area = calculate_overlap_area(rect1, rect2)
    
    if overlap_area == 0:
        return 0.0
    
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    area1 = w1 * h1
    area2 = w2 * h2
    union_area = area1 + area2 - overlap_area
    
    return overlap_area / union_area if union_area > 0 else 0.0


def validate_coordinates(x: int, y: int, image_width: int, image_height: int) -> bool:
    """验证坐标是否在图像范围内
    
    Args:
        x: x坐标
        y: y坐标
        image_width: 图像宽度
        image_height: 图像高度
        
    Returns:
        bool: 坐标是否有效
    """
    return 0 <= x < image_width and 0 <= y < image_height


def validate_rectangle(x: int, y: int, width: int, height: int,
                      image_width: int, image_height: int) -> bool:
    """验证矩形是否在图像范围内
    
    Args:
        x: 左上角x坐标
        y: 左上角y坐标
        width: 宽度
        height: 高度
        image_width: 图像宽度
        image_height: 图像高度
        
    Returns:
        bool: 矩形是否有效
    """
    return (0 <= x < image_width and 
            0 <= y < image_height and
            width > 0 and height > 0 and
            x + width <= image_width and
            y + height <= image_height)


def clamp_coordinates(x: int, y: int, image_width: int, image_height: int) -> Tuple[int, int]:
    """将坐标限制在图像范围内
    
    Args:
        x: x坐标
        y: y坐标
        image_width: 图像宽度
        image_height: 图像高度
        
    Returns:
        Tuple[int, int]: 限制后的坐标
    """
    x = max(0, min(x, image_width - 1))
    y = max(0, min(y, image_height - 1))
    return x, y


def clamp_rectangle(x: int, y: int, width: int, height: int,
                   image_width: int, image_height: int) -> Tuple[int, int, int, int]:
    """将矩形限制在图像范围内
    
    Args:
        x: 左上角x坐标
        y: 左上角y坐标
        width: 宽度
        height: 高度
        image_width: 图像宽度
        image_height: 图像高度
        
    Returns:
        Tuple[int, int, int, int]: 限制后的矩形
    """
    x = max(0, min(x, image_width - 1))
    y = max(0, min(y, image_height - 1))
    
    max_width = image_width - x
    max_height = image_height - y
    
    width = max(1, min(width, max_width))
    height = max(1, min(height, max_height))
    
    return x, y, width, height


def create_temp_file(suffix: str = "", prefix: str = "ipad_automation_", 
                    dir: Optional[str] = None) -> str:
    """创建临时文件
    
    Args:
        suffix: 文件后缀
        prefix: 文件前缀
        dir: 临时目录
        
    Returns:
        str: 临时文件路径
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    os.close(fd)  # 关闭文件描述符
    return path


def create_temp_dir(prefix: str = "ipad_automation_", 
                   dir: Optional[str] = None) -> str:
    """创建临时目录
    
    Args:
        prefix: 目录前缀
        dir: 父目录
        
    Returns:
        str: 临时目录路径
    """
    return tempfile.mkdtemp(prefix=prefix, dir=dir)


def cleanup_temp_files(temp_paths: List[str]):
    """清理临时文件
    
    Args:
        temp_paths: 临时文件路径列表
    """
    for path in temp_paths:
        try:
            path_obj = Path(path)
            if path_obj.is_file():
                path_obj.unlink()
                logger.debug(f"删除临时文件: {path}")
            elif path_obj.is_dir():
                import shutil
                shutil.rmtree(path)
                logger.debug(f"删除临时目录: {path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败 {path}: {e}")


def format_duration(seconds: float) -> str:
    """格式化时间长度
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化的时间字符串
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m{secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h{minutes}m{secs:.0f}s"


def format_file_size(bytes_size: int) -> str:
    """格式化文件大小
    
    Args:
        bytes_size: 字节数
        
    Returns:
        str: 格式化的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}PB"


def validate_element(element: Element) -> bool:
    """验证元素对象
    
    Args:
        element: 元素对象
        
    Returns:
        bool: 是否有效
    """
    try:
        if not element.name:
            return False
        
        if element.x < 0 or element.y < 0:
            return False
        
        if element.width <= 0 or element.height <= 0:
            return False
        
        if not (0 <= element.confidence <= 1):
            return False
        
        return True
    except Exception:
        return False


def validate_match_result(result: MatchResult) -> bool:
    """验证匹配结果
    
    Args:
        result: 匹配结果
        
    Returns:
        bool: 是否有效
    """
    try:
        if not result.template_name:
            return False
        
        if not (0 <= result.confidence <= 1):
            return False
        
        if result.x < 0 or result.y < 0:
            return False
        
        if result.width <= 0 or result.height <= 0:
            return False
        
        return True
    except Exception:
        return False


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """安全除法
    
    Args:
        a: 被除数
        b: 除数
        default: 除数为0时的默认值
        
    Returns:
        float: 除法结果
    """
    return a / b if b != 0 else default


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, 
                      exceptions: Tuple = (Exception,)):
    """重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔
        exceptions: 需要重试的异常类型
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次执行失败，{delay}秒后重试: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败")
            
            raise last_exception
        
        return wrapper
    return decorator