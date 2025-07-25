#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视觉识别系统模块

负责游戏界面元素的识别、定位和分析。
使用OpenCV进行图像处理和模板匹配。
"""

import os
import cv2
import numpy as np
from pathlib import Path
from loguru import logger
from config import TEMPLATE_DIR, GAME_TEMPLATES


class VisionSystem:
    """视觉识别系统类，负责游戏界面元素的识别和分析"""
    
    def __init__(self, game_settings):
        """初始化视觉识别系统
        
        Args:
            game_settings: 游戏设置，包含匹配阈值等参数
        """
        self.settings = game_settings
        self.match_threshold = game_settings.get("match_threshold", 0.8)
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """加载模板图像"""
        logger.info("正在加载模板图像...")
        
        # 确保模板目录存在
        os.makedirs(TEMPLATE_DIR, exist_ok=True)
        
        # 加载所有模板
        for template_name, template_file in GAME_TEMPLATES.items():
            template_path = os.path.join(TEMPLATE_DIR, template_file)
            
            # 检查模板文件是否存在
            if not os.path.exists(template_path):
                logger.warning(f"模板文件不存在: {template_path}")
                continue
            
            try:
                # 读取模板图像
                template = cv2.imread(template_path)
                
                if template is None:
                    logger.error(f"无法读取模板图像: {template_path}")
                    continue
                
                # 转换为灰度图像
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                
                # 存储模板
                self.templates[template_name] = {
                    "color": template,
                    "gray": template_gray,
                    "height": template.shape[0],
                    "width": template.shape[1]
                }
                
                logger.debug(f"已加载模板: {template_name} ({template.shape[1]}x{template.shape[0]})")
                
            except Exception as e:
                logger.exception(f"加载模板 {template_name} 时出错: {e}")
        
        logger.info(f"模板加载完成，共 {len(self.templates)} 个模板")
    
    def find_template(self, image, template_name, threshold=None):
        """在图像中查找指定模板
        
        Args:
            image: 要搜索的图像（numpy数组）
            template_name: 模板名称
            threshold: 匹配阈值，如果为None则使用默认值
            
        Returns:
            tuple: (x, y, width, height, confidence) 匹配位置和置信度，如果未找到则返回None
        """
        if template_name not in self.templates:
            logger.error(f"模板不存在: {template_name}")
            return None
        
        if threshold is None:
            threshold = self.match_threshold
        
        try:
            # 获取模板
            template = self.templates[template_name]
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
            
            # 如果匹配度超过阈值，返回匹配位置
            if max_val >= threshold:
                x, y = max_loc
                return (x, y, template_width, template_height, max_val)
            else:
                logger.debug(f"未找到模板 {template_name}，最佳匹配度: {max_val:.4f}，阈值: {threshold:.4f}")
                return None
                
        except Exception as e:
            logger.exception(f"查找模板 {template_name} 时出错: {e}")
            return None
    
    def find_all_templates(self, image, template_name, threshold=None, max_results=10):
        """在图像中查找所有匹配指定模板的位置
        
        Args:
            image: 要搜索的图像（numpy数组）
            template_name: 模板名称
            threshold: 匹配阈值，如果为None则使用默认值
            max_results: 最大返回结果数量
            
        Returns:
            list: [(x, y, width, height, confidence), ...] 匹配位置和置信度列表
        """
        if template_name not in self.templates:
            logger.error(f"模板不存在: {template_name}")
            return []
        
        if threshold is None:
            threshold = self.match_threshold
        
        try:
            # 获取模板
            template = self.templates[template_name]
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
            
            # 将匹配位置转换为坐标列表
            for pt in zip(*locations[::-1]):
                x, y = pt
                confidence = result[y, x]
                matches.append((x, y, template_width, template_height, confidence))
            
            # 对结果进行非极大值抑制，避免重复检测
            matches = self._non_max_suppression(matches)
            
            # 按置信度排序并限制结果数量
            matches.sort(key=lambda x: x[4], reverse=True)
            matches = matches[:max_results]
            
            logger.debug(f"找到 {len(matches)} 个模板 {template_name} 的匹配")
            return matches
            
        except Exception as e:
            logger.exception(f"查找所有模板 {template_name} 时出错: {e}")
            return []
    
    def _non_max_suppression(self, matches, overlap_threshold=0.3):
        """对匹配结果进行非极大值抑制，去除重叠的检测框
        
        Args:
            matches: 匹配结果列表 [(x, y, width, height, confidence), ...]
            overlap_threshold: 重叠阈值，超过此阈值的框将被抑制
            
        Returns:
            list: 经过非极大值抑制后的匹配结果列表
        """
        if not matches:
            return []
        
        # 按置信度排序
        matches.sort(key=lambda x: x[4], reverse=True)
        
        # 转换为矩形格式 [x1, y1, x2, y2, confidence]
        boxes = [(x, y, x + w, y + h, conf) for x, y, w, h, conf in matches]
        
        # 非极大值抑制
        keep = []
        
        while boxes:
            # 取置信度最高的框
            current = boxes.pop(0)
            keep.append(current)
            
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
        
        # 转换回原始格式 [x, y, width, height, confidence]
        result = [(x1, y1, x2 - x1, y2 - y1, conf) for x1, y1, x2, y2, conf in keep]
        return result
    
    def capture_template(self, image, x, y, width, height, template_name):
        """从图像中截取区域作为新模板
        
        Args:
            image: 源图像
            x, y, width, height: 要截取的区域
            template_name: 模板名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 确保坐标有效
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                logger.error(f"无效的模板区域: ({x}, {y}, {width}, {height})")
                return False
            
            # 确保区域在图像范围内
            if x + width > image.shape[1] or y + height > image.shape[0]:
                logger.error(f"模板区域超出图像范围: ({x}, {y}, {width}, {height})")
                return False
            
            # 截取区域
            template = image[y:y+height, x:x+width].copy()
            
            # 生成文件名
            if template_name not in GAME_TEMPLATES:
                logger.warning(f"模板名称 {template_name} 不在预定义列表中")
                template_file = f"{template_name}.png"
            else:
                template_file = GAME_TEMPLATES[template_name]
            
            # 保存模板
            template_path = os.path.join(TEMPLATE_DIR, template_file)
            cv2.imwrite(template_path, template)
            
            # 更新模板缓存
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            self.templates[template_name] = {
                "color": template,
                "gray": template_gray,
                "height": template.shape[0],
                "width": template.shape[1]
            }
            
            logger.info(f"已保存新模板: {template_name} ({width}x{height})")
            return True
            
        except Exception as e:
            logger.exception(f"保存模板时出错: {e}")
            return False
    
    def analyze_screen(self, image):
        """分析游戏屏幕，识别当前界面状态和可交互元素
        
        Args:
            image: 屏幕图像
            
        Returns:
            dict: 分析结果，包含界面状态和可交互元素
        """
        result = {
            "screen_type": "unknown",
            "elements": []
        }
        
        try:
            # 尝试识别主界面
            main_menu = self.find_template(image, "main_menu")
            if main_menu:
                result["screen_type"] = "main_menu"
                result["elements"].append({
                    "type": "main_menu",
                    "position": main_menu[:4],
                    "confidence": main_menu[4]
                })
            
            # 尝试识别世界地图
            world_map = self.find_template(image, "world_map")
            if world_map:
                result["screen_type"] = "world_map"
                result["elements"].append({
                    "type": "world_map",
                    "position": world_map[:4],
                    "confidence": world_map[4]
                })
            
            # 在世界地图上查找土地和资源点
            if result["screen_type"] == "world_map":
                # 查找空闲土地
                empty_lands = self.find_all_templates(image, "empty_land")
                for land in empty_lands:
                    result["elements"].append({
                        "type": "empty_land",
                        "position": land[:4],
                        "confidence": land[4]
                    })
                
                # 查找资源点
                resources = self.find_all_templates(image, "resource_point")
                for resource in resources:
                    result["elements"].append({
                        "type": "resource_point",
                        "position": resource[:4],
                        "confidence": resource[4]
                    })
                
                # 查找部队
                armies = self.find_all_templates(image, "army_idle")
                for army in armies:
                    result["elements"].append({
                        "type": "army_idle",
                        "position": army[:4],
                        "confidence": army[4]
                    })
            
            # 查找通用按钮
            for button_name in ["confirm_button", "cancel_button", "close_button", "back_button"]:
                buttons = self.find_all_templates(image, button_name)
                for button in buttons:
                    result["elements"].append({
                        "type": button_name,
                        "position": button[:4],
                        "confidence": button[4]
                    })
            
            logger.debug(f"屏幕分析结果: {result['screen_type']}, 找到 {len(result['elements'])} 个元素")
            return result
            
        except Exception as e:
            logger.exception(f"分析屏幕时出错: {e}")
            return result