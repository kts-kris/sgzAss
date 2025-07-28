#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词管理器
负责加载、缓存和优化提示词配置
"""

import yaml
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from threading import Lock

from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """提示词模板"""
    content: str
    language: str
    category: str
    version: str = "1.0"
    usage_count: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    last_optimized: Optional[str] = None


class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        self.config = get_config()
        self._prompts: Dict[str, Dict[str, PromptTemplate]] = {}
        self._cache_lock = Lock()
        self._optimization_counter = 0
        self._builtin_prompts = self._get_builtin_prompts()
        self._load_prompts()
    
    def _get_builtin_prompts(self) -> Dict[str, Dict[str, str]]:
        """获取内置提示词（作为备用）"""
        return {
            "game_analysis": {
                "zh": """
你是一个专业的三国志战略版游戏助手。请分析这张游戏截图，并提供以下信息：

1. 当前游戏界面状态（主界面、世界地图、城池界面等）
2. 可见的UI元素和按钮
3. 推荐的下一步操作
4. 游戏策略建议

请以JSON格式返回结果。
                """,
                "en": """
You are a professional Three Kingdoms strategy game assistant. Please analyze this game screenshot and provide the following information:

1. Current game interface status
2. Visible UI elements and buttons
3. Recommended next actions
4. Game strategy suggestions

Please return results in JSON format.
                """
            },
            "ui_elements": {
                "zh": """
请仔细分析这张游戏截图中的所有UI元素，包括按钮、图标、文本标签等。
重点关注可交互的元素，并准确标注它们的位置和类型。
请以JSON格式返回所有识别到的UI元素。
                """,
                "en": """
Please carefully analyze all UI elements in this game screenshot, including buttons, icons, text labels, etc.
Focus on interactive elements and accurately mark their positions and types.
Please return all identified UI elements in JSON format.
                """
            },
            "action_suggestion": {
                "zh": """
基于当前游戏状态，请提供最优的操作建议。
分析当前可执行的操作，评估优先级，并提供具体的操作步骤。
请以JSON格式返回操作建议列表。
                """,
                "en": """
Based on the current game state, please provide optimal action suggestions.
Analyze currently executable actions, evaluate priorities, and provide specific action steps.
Please return the action suggestion list in JSON format.
                """
            },
            "efficient_analysis": {
                "zh": """
作为三国志战略版专家，请快速分析截图并返回关键信息：
1. 识别界面类型
2. 定位主要可点击元素
3. 提供1-2个最优操作建议

输出要求：简洁准确，坐标精确，优先级明确。
JSON格式：{"scene":"界面类型","elements":[{"name":"元素名","x":x,"y":y}],"priority_action":"最优操作"}
                """,
                "en": """
As a Three Kingdoms strategy expert, quickly analyze the screenshot and return key information:
1. Identify interface type
2. Locate main clickable elements
3. Provide 1-2 optimal action suggestions

Output requirements: Concise and accurate, precise coordinates, clear priorities.
JSON format: {"scene":"interface_type","elements":[{"name":"element_name","x":x,"y":y}],"priority_action":"optimal_action"}
                """
            }
        }
    
    def _load_prompts(self):
        """加载提示词配置"""
        try:
            config_path = Path(self.config.prompt.config_file)
            if not config_path.is_absolute():
                # 相对路径，基于项目根目录
                project_root = Path(__file__).parent.parent.parent
                config_path = project_root / config_path
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    prompt_data = yaml.safe_load(f)
                
                self._parse_prompt_data(prompt_data)
                logger.info(f"提示词配置加载成功: {config_path}")
            else:
                logger.warning(f"提示词配置文件不存在: {config_path}，使用内置提示词")
                self._load_builtin_prompts()
        
        except Exception as e:
            logger.error(f"加载提示词配置失败: {e}")
            if self.config.prompt.fallback_to_builtin:
                logger.info("回退到内置提示词")
                self._load_builtin_prompts()
            else:
                raise
    
    def _parse_prompt_data(self, data: Dict[str, Any]):
        """解析提示词数据"""
        with self._cache_lock:
            self._prompts.clear()
            
            # 解析各类提示词
            for category in ['game_analysis', 'ui_elements', 'action_suggestion', 'efficient_analysis']:
                if category in data:
                    self._prompts[category] = {}
                    for lang, content in data[category].items():
                        if isinstance(content, str):
                            self._prompts[category][lang] = PromptTemplate(
                                content=content.strip(),
                                language=lang,
                                category=category
                            )
            
            # 解析自定义提示词
            if 'custom' in data:
                for custom_name, custom_data in data['custom'].items():
                    if isinstance(custom_data, dict):
                        self._prompts[custom_name] = {}
                        for lang, content in custom_data.items():
                            if isinstance(content, str):
                                self._prompts[custom_name][lang] = PromptTemplate(
                                    content=content.strip(),
                                    language=lang,
                                    category=custom_name
                                )
    
    def _load_builtin_prompts(self):
        """加载内置提示词"""
        with self._cache_lock:
            self._prompts.clear()
            for category, lang_prompts in self._builtin_prompts.items():
                self._prompts[category] = {}
                for lang, content in lang_prompts.items():
                    self._prompts[category][lang] = PromptTemplate(
                        content=content.strip(),
                        language=lang,
                        category=category
                    )
    
    def get_prompt(self, category: str, language: Optional[str] = None, 
                   analysis_type: Optional[str] = None) -> str:
        """获取提示词"""
        if language is None:
            language = self.config.prompt.default_language
        
        # 优先使用指定的分析类型
        if analysis_type and analysis_type in self._prompts:
            category = analysis_type
        
        with self._cache_lock:
            if category in self._prompts:
                if language in self._prompts[category]:
                    template = self._prompts[category][language]
                    template.usage_count += 1
                    return template.content
                
                # 回退到默认语言
                default_lang = self.config.prompt.default_language
                if default_lang in self._prompts[category]:
                    template = self._prompts[category][default_lang]
                    template.usage_count += 1
                    return template.content
                
                # 回退到任意可用语言
                if self._prompts[category]:
                    template = next(iter(self._prompts[category].values()))
                    template.usage_count += 1
                    return template.content
        
        # 最后回退到内置提示词
        if category in self._builtin_prompts:
            if language in self._builtin_prompts[category]:
                return self._builtin_prompts[category][language]
            if self.config.prompt.default_language in self._builtin_prompts[category]:
                return self._builtin_prompts[category][self.config.prompt.default_language]
            if self._builtin_prompts[category]:
                return next(iter(self._builtin_prompts[category].values()))
        
        logger.warning(f"未找到提示词: category={category}, language={language}")
        return "请分析这张游戏截图。"  # 默认提示词
    
    def get_optimized_prompt(self, category: str, language: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None) -> str:
        """获取优化后的提示词"""
        base_prompt = self.get_prompt(category, language)
        
        if not self.config.prompt.enable_optimization:
            return base_prompt
        
        # 根据上下文优化提示词
        if context:
            optimized = self._optimize_prompt_with_context(base_prompt, context)
            return optimized
        
        return base_prompt
    
    def _optimize_prompt_with_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """根据上下文优化提示词"""
        # 简单的优化策略：根据历史成功率调整
        if context.get('recent_failures', 0) > 2:
            # 如果最近失败较多，使用更详细的提示词
            if "请详细分析" not in prompt:
                prompt = "请详细分析并" + prompt.lstrip("请")
        
        elif context.get('avg_response_time', 0) > 5.0:
            # 如果响应时间较长，使用更简洁的提示词
            if len(prompt) > self.config.prompt.max_prompt_length:
                # 简化提示词
                lines = prompt.split('\n')
                essential_lines = [line for line in lines if any(keyword in line for keyword in 
                                 ['JSON', '格式', '分析', '识别', '建议'])]
                if essential_lines:
                    prompt = '\n'.join(essential_lines[:3])  # 保留前3个关键行
        
        return prompt
    
    def update_prompt_performance(self, category: str, language: str, 
                                success: bool, response_time: float):
        """更新提示词性能统计"""
        with self._cache_lock:
            if category in self._prompts and language in self._prompts[category]:
                template = self._prompts[category][language]
                
                # 更新成功率
                total_uses = template.usage_count
                if total_uses > 0:
                    current_success_rate = template.success_rate
                    new_success_rate = (current_success_rate * (total_uses - 1) + (1.0 if success else 0.0)) / total_uses
                    template.success_rate = new_success_rate
                
                # 更新平均响应时间
                if total_uses > 0:
                    current_avg_time = template.avg_response_time
                    new_avg_time = (current_avg_time * (total_uses - 1) + response_time) / total_uses
                    template.avg_response_time = new_avg_time
                
                # 检查是否需要优化
                self._optimization_counter += 1
                if (self._optimization_counter >= self.config.prompt.optimization_frequency and 
                    self.config.prompt.enable_optimization):
                    self._optimize_prompts()
                    self._optimization_counter = 0
    
    def _optimize_prompts(self):
        """优化提示词（基于性能统计）"""
        logger.info("开始优化提示词...")
        
        with self._cache_lock:
            for category, lang_templates in self._prompts.items():
                for lang, template in lang_templates.items():
                    if template.usage_count >= 5:  # 至少使用5次才进行优化
                        if template.success_rate < 0.7:  # 成功率低于70%
                            logger.info(f"提示词成功率较低，需要优化: {category}.{lang} (成功率: {template.success_rate:.2f})")
                            # 这里可以实现具体的优化逻辑
                        
                        elif template.avg_response_time > 10.0:  # 响应时间超过10秒
                            logger.info(f"提示词响应时间较长，需要优化: {category}.{lang} (平均时间: {template.avg_response_time:.2f}s)")
                            # 这里可以实现具体的优化逻辑
    
    def reload_prompts(self):
        """重新加载提示词配置"""
        logger.info("重新加载提示词配置...")
        self._load_prompts()
    
    def get_available_categories(self) -> List[str]:
        """获取可用的提示词类别"""
        with self._cache_lock:
            return list(self._prompts.keys())
    
    def get_available_languages(self, category: str) -> List[str]:
        """获取指定类别的可用语言"""
        with self._cache_lock:
            if category in self._prompts:
                return list(self._prompts[category].keys())
            return []
    
    def get_prompt_stats(self) -> Dict[str, Any]:
        """获取提示词使用统计"""
        stats = {
            "total_categories": len(self._prompts),
            "total_prompts": sum(len(lang_templates) for lang_templates in self._prompts.values()),
            "categories": {}
        }
        
        with self._cache_lock:
            for category, lang_templates in self._prompts.items():
                category_stats = {
                    "languages": list(lang_templates.keys()),
                    "total_usage": sum(t.usage_count for t in lang_templates.values()),
                    "avg_success_rate": sum(t.success_rate for t in lang_templates.values()) / len(lang_templates) if lang_templates else 0,
                    "avg_response_time": sum(t.avg_response_time for t in lang_templates.values()) / len(lang_templates) if lang_templates else 0
                }
                stats["categories"][category] = category_stats
        
        return stats


# 全局提示词管理器实例
_prompt_manager = None
_manager_lock = Lock()


def get_prompt_manager() -> PromptManager:
    """获取全局提示词管理器实例"""
    global _prompt_manager
    if _prompt_manager is None:
        with _manager_lock:
            if _prompt_manager is None:
                _prompt_manager = PromptManager()
    return _prompt_manager


def reload_prompt_manager():
    """重新加载提示词管理器"""
    global _prompt_manager
    with _manager_lock:
        if _prompt_manager is not None:
            _prompt_manager.reload_prompts()
        else:
            _prompt_manager = PromptManager()