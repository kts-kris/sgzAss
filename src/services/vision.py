#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视觉识别服务模块

提供统一的视觉识别接口，支持模板匹配和VLM大模型识别。
基于OpenCV进行图像处理和模板匹配，预留VLM扩展接口。
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Union
from loguru import logger

from ..models import (
    MatchResult, AnalysisResult, Element, ElementType, VisionError,
    VLMResult, VLMError
)


class VisionService:
    """视觉识别服务类，提供统一的图像识别接口"""
    
    def __init__(self, template_dir: str = "templates", match_threshold: float = 0.8):
        """初始化视觉识别服务
        
        Args:
            template_dir: 模板图像目录路径
            match_threshold: 默认匹配阈值
        """
        self.template_dir = Path(template_dir)
        self.match_threshold = match_threshold
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.vlm_enabled = False
        self.vlm_client = None
        
        # 确保模板目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载模板
        self._load_templates()
    
    def _load_templates(self) -> None:
        """加载所有模板图像"""
        logger.info(f"正在从 {self.template_dir} 加载模板图像...")
        
        template_count = 0
        for template_file in self.template_dir.glob("*.png"):
            try:
                template_name = template_file.stem
                template = cv2.imread(str(template_file))
                
                if template is None:
                    logger.warning(f"无法读取模板图像: {template_file}")
                    continue
                
                # 转换为灰度图像
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                
                # 存储模板
                self.templates[template_name] = {
                    "color": template,
                    "gray": template_gray,
                    "height": template.shape[0],
                    "width": template.shape[1],
                    "path": str(template_file)
                }
                
                template_count += 1
                logger.debug(f"已加载模板: {template_name} ({template.shape[1]}x{template.shape[0]})")
                
            except Exception as e:
                logger.error(f"加载模板 {template_file} 时出错: {e}")
        
        logger.info(f"模板加载完成，共 {template_count} 个模板")
    
    def enable_vlm(self, vlm_client: Any) -> None:
        """启用VLM大模型识别
        
        Args:
            vlm_client: VLM客户端实例
        """
        self.vlm_client = vlm_client
        self.vlm_enabled = True
        logger.info("VLM大模型识别已启用")
    
    def disable_vlm(self) -> None:
        """禁用VLM大模型识别"""
        self.vlm_enabled = False
        self.vlm_client = None
        logger.info("VLM大模型识别已禁用")
    
    def find_element(self, image: np.ndarray, element_name: str, 
                    threshold: Optional[float] = None,
                    use_vlm: bool = False) -> Optional[MatchResult]:
        """在图像中查找指定元素
        
        Args:
            image: 要搜索的图像（numpy数组）
            element_name: 元素名称
            threshold: 匹配阈值，如果为None则使用默认值
            use_vlm: 是否使用VLM进行识别
            
        Returns:
            MatchResult: 匹配结果，如果未找到则返回None
        """
        try:
            if use_vlm and self.vlm_enabled:
                return self._find_element_vlm(image, element_name)
            else:
                return self._find_element_template(image, element_name, threshold)
        except Exception as e:
            logger.error(f"查找元素 {element_name} 时出错: {e}")
            raise VisionError(f"查找元素失败: {e}")
    
    def find_all_elements(self, image: np.ndarray, element_name: str,
                         threshold: Optional[float] = None,
                         max_results: int = 10,
                         use_vlm: bool = False) -> List[MatchResult]:
        """在图像中查找所有匹配的元素
        
        Args:
            image: 要搜索的图像
            element_name: 元素名称
            threshold: 匹配阈值
            max_results: 最大返回结果数量
            use_vlm: 是否使用VLM进行识别
            
        Returns:
            List[MatchResult]: 匹配结果列表
        """
        try:
            if use_vlm and self.vlm_enabled:
                return self._find_all_elements_vlm(image, element_name, max_results)
            else:
                return self._find_all_elements_template(image, element_name, threshold, max_results)
        except Exception as e:
            logger.error(f"查找所有元素 {element_name} 时出错: {e}")
            raise VisionError(f"查找所有元素失败: {e}")
    
    def analyze_screen(self, image: np.ndarray, use_vlm: bool = False) -> AnalysisResult:
        """分析屏幕内容，识别界面状态和可交互元素
        
        Args:
            image: 屏幕图像
            use_vlm: 是否使用VLM进行分析
            
        Returns:
            AnalysisResult: 分析结果
        """
        try:
            if use_vlm and self.vlm_enabled:
                return self._analyze_screen_vlm(image)
            else:
                return self._analyze_screen_template(image)
        except Exception as e:
            logger.error(f"分析屏幕时出错: {e}")
            raise VisionError(f"屏幕分析失败: {e}")
    
    def _find_element_template(self, image: np.ndarray, element_name: str,
                              threshold: Optional[float] = None) -> Optional[MatchResult]:
        """使用模板匹配查找元素"""
        if element_name not in self.templates:
            logger.warning(f"模板不存在: {element_name}")
            return None
        
        if threshold is None:
            threshold = self.match_threshold
        
        # 获取模板
        template = self.templates[element_name]
        template_gray = template["gray"]
        template_width = template["width"]
        template_height = template["height"]
        
        # 转换图像为灰度
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image
        
        # 执行模板匹配
        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # 查找最佳匹配位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 如果匹配度超过阈值，返回匹配结果
        if max_val >= threshold:
            x, y = max_loc
            return MatchResult(
                element_name=element_name,
                x=x,
                y=y,
                width=template_width,
                height=template_height,
                confidence=max_val,
                method="template"
            )
        else:
            logger.debug(f"未找到元素 {element_name}，最佳匹配度: {max_val:.4f}，阈值: {threshold:.4f}")
            return None
    
    def _find_all_elements_template(self, image: np.ndarray, element_name: str,
                                   threshold: Optional[float] = None,
                                   max_results: int = 10) -> List[MatchResult]:
        """使用模板匹配查找所有元素"""
        if element_name not in self.templates:
            logger.warning(f"模板不存在: {element_name}")
            return []
        
        if threshold is None:
            threshold = self.match_threshold
        
        # 获取模板
        template = self.templates[element_name]
        template_gray = template["gray"]
        template_width = template["width"]
        template_height = template["height"]
        
        # 转换图像为灰度
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image
        
        # 执行模板匹配
        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # 查找所有匹配位置
        locations = np.where(result >= threshold)
        matches = []
        
        # 将匹配位置转换为MatchResult列表
        for pt in zip(*locations[::-1]):
            x, y = pt
            confidence = result[y, x]
            matches.append(MatchResult(
                element_name=element_name,
                x=x,
                y=y,
                width=template_width,
                height=template_height,
                confidence=confidence,
                method="template"
            ))
        
        # 对结果进行非极大值抑制
        matches = self._non_max_suppression(matches)
        
        # 按置信度排序并限制结果数量
        matches.sort(key=lambda x: x.confidence, reverse=True)
        matches = matches[:max_results]
        
        logger.debug(f"找到 {len(matches)} 个元素 {element_name} 的匹配")
        return matches
    
    def _analyze_screen_template(self, image: np.ndarray) -> AnalysisResult:
        """使用模板匹配分析屏幕"""
        elements = []
        screen_type = "unknown"
        
        # 预定义的界面类型和对应的模板
        screen_templates = {
            "main_menu": "main_menu",
            "world_map": "world_map",
            "battle": "battle_ui",
            "city": "city_view"
        }
        
        # 识别界面类型
        for screen_name, template_name in screen_templates.items():
            match = self._find_element_template(image, template_name)
            if match:
                screen_type = screen_name
                elements.append(Element(
                    type=ElementType.UI,
                    name=template_name,
                    x=match.x,
                    y=match.y,
                    width=match.width,
                    height=match.height,
                    confidence=match.confidence
                ))
                break
        
        # 查找通用UI元素
        ui_elements = ["confirm_button", "cancel_button", "close_button", "back_button"]
        for element_name in ui_elements:
            matches = self._find_all_elements_template(image, element_name)
            for match in matches:
                elements.append(Element(
                    type=ElementType.BUTTON,
                    name=element_name,
                    x=match.x,
                    y=match.y,
                    width=match.width,
                    height=match.height,
                    confidence=match.confidence
                ))
        
        # 根据界面类型查找特定元素
        if screen_type == "world_map":
            # 查找地图元素
            map_elements = ["empty_land", "resource_point", "army_idle"]
            for element_name in map_elements:
                matches = self._find_all_elements_template(image, element_name)
                for match in matches:
                    elements.append(Element(
                        type=ElementType.INTERACTIVE,
                        name=element_name,
                        x=match.x,
                        y=match.y,
                        width=match.width,
                        height=match.height,
                        confidence=match.confidence
                    ))
        
        # 创建操作建议（空列表，因为模板匹配不提供建议）
        suggestions = []
        
        # 将screen_type存储在raw_data中
        raw_data = {
            "screen_type": screen_type,
            "method": "template"
        }
        
        return AnalysisResult(
            success=True,
            confidence=max([e.confidence for e in elements], default=0.0),
            elements=elements,
            suggestions=suggestions,
            analysis_time=0.0,  # TODO: 添加实际的分析时间计算
            raw_data=raw_data
        )
    
    def _find_element_vlm(self, image: np.ndarray, element_name: str) -> Optional[MatchResult]:
        """使用VLM查找元素（预留接口）"""
        if not self.vlm_enabled or not self.vlm_client:
            raise VLMError("VLM未启用或客户端未配置")
        
        # TODO: 实现VLM元素查找逻辑
        logger.warning("VLM元素查找功能尚未实现")
        return None
    
    def _find_all_elements_vlm(self, image: np.ndarray, element_name: str,
                              max_results: int = 10) -> List[MatchResult]:
        """使用VLM查找所有元素（预留接口）"""
        if not self.vlm_enabled or not self.vlm_client:
            raise VLMError("VLM未启用或客户端未配置")
        
        # TODO: 实现VLM所有元素查找逻辑
        logger.warning("VLM所有元素查找功能尚未实现")
        return []
    
    def _analyze_screen_vlm(self, image: np.ndarray) -> AnalysisResult:
        """使用VLM分析屏幕（预留接口）"""
        if not self.vlm_enabled or not self.vlm_client:
            raise VLMError("VLM未启用或客户端未配置")
        
        # TODO: 实现VLM屏幕分析逻辑
        logger.warning("VLM屏幕分析功能尚未实现")
        # 创建操作建议（空列表，因为VLM功能尚未实现）
        suggestions = []
        
        # 将screen_type存储在raw_data中
        raw_data = {
            "screen_type": "unknown",
            "method": "vlm"
        }
        
        return AnalysisResult(
            success=False,
            confidence=0.0,
            elements=[],
            suggestions=suggestions,
            analysis_time=0.0,
            raw_data=raw_data
        )
    
    def _non_max_suppression(self, matches: List[MatchResult],
                            overlap_threshold: float = 0.3) -> List[MatchResult]:
        """对匹配结果进行非极大值抑制，去除重叠的检测框"""
        if not matches:
            return []
        
        # 按置信度排序
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        # 转换为矩形格式 [x1, y1, x2, y2, match_obj]
        boxes = [(m.x, m.y, m.x + m.width, m.y + m.height, m) for m in matches]
        
        # 非极大值抑制
        keep = []
        
        while boxes:
            # 取置信度最高的框
            current = boxes.pop(0)
            keep.append(current[4])  # 保存MatchResult对象
            
            # 计算与其他框的重叠度，保留重叠度小的框
            i = 0
            while i < len(boxes):
                # 计算交集区域
                x1 = max(current[0], boxes[i][0])
                y1 = max(current[1], boxes[i][1])
                x2 = min(current[2], boxes[i][2])
                y2 = min(current[3], boxes[i][3])
                
                # 计算交集面积
                w = max(0, x2 - x1)
                h = max(0, y2 - y1)
                intersection = w * h
                
                # 计算两个框的面积
                area1 = (current[2] - current[0]) * (current[3] - current[1])
                area2 = (boxes[i][2] - boxes[i][0]) * (boxes[i][3] - boxes[i][1])
                
                # 计算重叠度（交并比）
                overlap = intersection / float(area1 + area2 - intersection)
                
                # 如果重叠度大于阈值，删除该框
                if overlap > overlap_threshold:
                    boxes.pop(i)
                else:
                    i += 1
        
        return keep
    
    def save_template(self, image: np.ndarray, x: int, y: int,
                     width: int, height: int, template_name: str) -> bool:
        """从图像中截取区域作为新模板
        
        Args:
            image: 源图像
            x, y, width, height: 要截取的区域
            template_name: 模板名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 验证坐标
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                raise VisionError(f"无效的模板区域: ({x}, {y}, {width}, {height})")
            
            if x + width > image.shape[1] or y + height > image.shape[0]:
                raise VisionError(f"模板区域超出图像范围: ({x}, {y}, {width}, {height})")
            
            # 截取区域
            template = image[y:y+height, x:x+width].copy()
            
            # 保存模板
            template_path = self.template_dir / f"{template_name}.png"
            cv2.imwrite(str(template_path), template)
            
            # 更新模板缓存
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            self.templates[template_name] = {
                "color": template,
                "gray": template_gray,
                "height": template.shape[0],
                "width": template.shape[1],
                "path": str(template_path)
            }
            
            logger.info(f"已保存新模板: {template_name} ({width}x{height})")
            return True
            
        except Exception as e:
            logger.error(f"保存模板时出错: {e}")
            raise VisionError(f"保存模板失败: {e}")
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息
        
        Args:
            template_name: 模板名称
            
        Returns:
            Dict: 模板信息，如果模板不存在则返回None
        """
        if template_name not in self.templates:
            return None
        
        template = self.templates[template_name]
        return {
            "name": template_name,
            "width": template["width"],
            "height": template["height"],
            "path": template["path"]
        }
    
    def list_templates(self) -> List[str]:
        """获取所有可用模板名称列表
        
        Returns:
            List[str]: 模板名称列表
        """
        return list(self.templates.keys())