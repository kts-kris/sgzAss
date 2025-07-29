#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板匹配服务
用于基于预定义模板识别游戏界面元素
"""

import json
import os
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TemplateMatcher:
    """模板匹配器"""
    
    def __init__(self, template_dir: str = None):
        """初始化模板匹配器
        
        Args:
            template_dir: 模板文件目录路径
        """
        if template_dir is None:
            # 默认模板目录
            current_dir = Path(__file__).parent.parent.parent
            template_dir = current_dir / "templates"
        
        self.template_dir = Path(template_dir)
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """加载所有模板文件"""
        if not self.template_dir.exists():
            logger.warning(f"模板目录不存在: {self.template_dir}")
            return
        
        template_files = list(self.template_dir.glob("*.json"))
        logger.info(f"发现 {len(template_files)} 个模板文件")
        
        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                template_name = template_file.stem
                self.templates[template_name] = template_data
                logger.info(f"加载模板: {template_name}")
                
            except Exception as e:
                logger.error(f"加载模板文件失败 {template_file}: {e}")
    
    def match_elements(self, screenshot_analysis: Dict, confidence_threshold: float = 0.6) -> Dict:
        """基于模板匹配界面元素
        
        Args:
            screenshot_analysis: 截图分析结果
            confidence_threshold: 置信度阈值
            
        Returns:
            匹配结果字典
        """
        if not self.templates:
            logger.warning("没有可用的模板")
            return self._create_empty_result()
        
        best_match = None
        best_score = 0
        
        # 遍历所有模板寻找最佳匹配
        for template_name, template_data in self.templates.items():
            score = self._calculate_template_score(screenshot_analysis, template_data)
            logger.debug(f"模板 {template_name} 匹配分数: {score}")
            
            if score > best_score:
                best_score = score
                best_match = (template_name, template_data)
        
        if best_match and best_score >= confidence_threshold:
            template_name, template_data = best_match
            logger.info(f"使用模板: {template_name} (分数: {best_score:.2f})")
            return self._apply_template(screenshot_analysis, template_data, best_score)
        else:
            logger.info(f"没有找到合适的模板 (最高分数: {best_score:.2f})")
            return self._create_fallback_result(screenshot_analysis)
    
    def _calculate_template_score(self, analysis: Dict, template: Dict) -> float:
        """计算模板匹配分数
        
        Args:
            analysis: 截图分析结果
            template: 模板数据
            
        Returns:
            匹配分数 (0-1)
        """
        score = 0.0
        total_weight = 0.0
        
        # 获取分析文本内容
        text_content = ""
        if "description" in analysis:
            text_content += analysis["description"].lower()
        if "scene" in analysis:
            text_content += " " + analysis["scene"].lower()
        
        # 检查模板元素匹配
        template_elements = template.get("elements", [])
        for element in template_elements:
            element_weight = 1.0
            element_score = 0.0
            
            # 关键词匹配
            keywords = element.get("keywords", [])
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_content)
            if keywords:
                element_score += (keyword_matches / len(keywords)) * 0.8
            
            # 类型匹配
            element_type = element.get("type", "")
            if element_type in text_content:
                element_score += 0.2
            
            score += element_score * element_weight
            total_weight += element_weight
        
        # 归一化分数
        if total_weight > 0:
            score = score / total_weight
        
        return min(score, 1.0)
    
    def _apply_template(self, analysis: Dict, template: Dict, confidence: float) -> Dict:
        """应用模板生成结果
        
        Args:
            analysis: 原始分析结果
            template: 匹配的模板
            confidence: 匹配置信度
            
        Returns:
            应用模板后的结果
        """
        result = {
            "scene": analysis.get("scene", "未知界面"),
            "description": analysis.get("description", ""),
            "elements": [],
            "suggestions": [],
            "confidence": confidence,
            "template_used": template.get("name", "未知模板")
        }
        
        # 基于模板生成元素
        template_elements = template.get("elements", [])
        for element_template in template_elements:
            if self._should_include_element(analysis, element_template):
                element = self._create_element_from_template(element_template)
                result["elements"].append(element)
        
        # 基于模板生成建议
        template_actions = template.get("actions", [])
        for action_template in template_actions:
            if self._should_include_action(result["elements"], action_template):
                suggestion = self._create_suggestion_from_template(action_template)
                result["suggestions"].append(suggestion)
        
        # 按优先级排序建议
        result["suggestions"].sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        return result
    
    def _should_include_element(self, analysis: Dict, element_template: Dict) -> bool:
        """判断是否应该包含某个元素"""
        # 获取分析文本
        text_content = ""
        if "description" in analysis:
            text_content += analysis["description"].lower()
        if "scene" in analysis:
            text_content += " " + analysis["scene"].lower()
        
        # 检查关键词匹配
        keywords = element_template.get("keywords", [])
        if not keywords:
            return True  # 没有关键词限制则包含
        
        # 至少匹配一个关键词
        return any(keyword.lower() in text_content for keyword in keywords)
    
    def _should_include_action(self, elements: List[Dict], action_template: Dict) -> bool:
        """判断是否应该包含某个动作"""
        target_element = action_template.get("target_element")
        if not target_element:
            return True  # 没有目标元素限制则包含
        
        # 检查目标元素是否存在
        return any(element.get("name") == target_element for element in elements)
    
    def _create_element_from_template(self, element_template: Dict) -> Dict:
        """从模板创建元素"""
        # 基于位置提示计算坐标
        position_hints = element_template.get("position_hints", {})
        x, y = self._calculate_position_from_hints(position_hints)
        
        return {
            "name": element_template.get("name", "未知元素"),
            "type": element_template.get("type", "unknown"),
            "x": x,
            "y": y,
            "width": 100,  # 默认宽度
            "height": 50,  # 默认高度
            "confidence": element_template.get("confidence_threshold", 0.7)
        }
    
    def _create_suggestion_from_template(self, action_template: Dict) -> Dict:
        """从模板创建建议"""
        return {
            "action": action_template.get("action_type", "tap"),
            "description": action_template.get("description", ""),
            "priority": action_template.get("priority", 1),
            "confidence": 0.8
        }
    
    def _calculate_position_from_hints(self, hints: Dict) -> Tuple[int, int]:
        """根据位置提示计算坐标"""
        # 假设屏幕尺寸 (可以从配置获取)
        screen_width = 800
        screen_height = 600
        
        x = screen_width // 2  # 默认中心
        y = screen_height // 2
        
        # 水平位置
        if hints.get("left_side"):
            x = screen_width // 4
        elif hints.get("right_side"):
            x = screen_width * 3 // 4
        elif hints.get("center_horizontal"):
            x = screen_width // 2
        
        # 垂直位置
        if hints.get("top_area"):
            y = screen_height // 4
        elif hints.get("bottom_area"):
            y = screen_height * 3 // 4
        elif hints.get("center"):
            y = screen_height // 2
        
        # 角落位置
        if hints.get("corner"):
            if hints.get("top_left"):
                x, y = 50, 50
            elif hints.get("top_right"):
                x, y = screen_width - 50, 50
            elif hints.get("bottom_left"):
                x, y = 50, screen_height - 50
            elif hints.get("bottom_right"):
                x, y = screen_width - 50, screen_height - 50
        
        return x, y
    
    def _create_empty_result(self) -> Dict:
        """创建空结果"""
        return {
            "scene": "未知界面",
            "description": "",
            "elements": [],
            "suggestions": [],
            "confidence": 0.0,
            "template_used": None
        }
    
    def _create_fallback_result(self, analysis: Dict) -> Dict:
        """创建回退结果"""
        return {
            "scene": analysis.get("scene", "未知界面"),
            "description": analysis.get("description", ""),
            "elements": [
                {
                    "name": "screen_center",
                    "type": "unknown",
                    "x": 400,
                    "y": 300,
                    "width": 100,
                    "height": 50,
                    "confidence": 0.3
                }
            ],
            "suggestions": [
                {
                    "action": "tap",
                    "description": "点击屏幕中心进行交互",
                    "priority": 1,
                    "confidence": 0.3
                }
            ],
            "confidence": 0.3,
            "template_used": "fallback"
        }
    
    def get_available_templates(self) -> List[str]:
        """获取可用模板列表"""
        return list(self.templates.keys())
    
    def reload_templates(self):
        """重新加载模板"""
        self.templates.clear()
        self._load_templates()
        logger.info("模板已重新加载")