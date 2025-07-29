#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词管理器
负责加载、缓存和优化提示词配置
"""

import yaml
import os
import logging
import time
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
        """获取内置提示词（作为备用）- 从配置文件读取"""
        # 不再硬编码提示词，而是从配置文件读取
        # 如果配置文件不存在或读取失败，返回空字典
        return {}
    
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
            
            # 递归解析所有提示词数据
            def parse_nested_prompts(data_dict, parent_key=""):
                for key, value in data_dict.items():
                    current_key = f"{parent_key}.{key}" if parent_key else key
                    
                    if isinstance(value, dict):
                        # 检查是否是语言映射（包含zh、en等语言键）
                        if any(lang_key in value for lang_key in ['zh', 'en', 'ja', 'ko']):
                            # 这是一个提示词定义
                            self._prompts[current_key] = {}
                            for lang, content in value.items():
                                if isinstance(content, str):
                                    self._prompts[current_key][lang] = PromptTemplate(
                                        content=content.strip(),
                                        language=lang,
                                        category=current_key
                                    )
                        else:
                            # 继续递归解析
                            parse_nested_prompts(value, current_key)
            
            # 解析所有数据
            parse_nested_prompts(data)
    
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
        
        # 处理嵌套路径，如 automation_actions.tap
        def get_nested_value(data, path):
            keys = path.split('.')
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        
        with self._cache_lock:
            # 首先尝试直接匹配
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
            
            # 尝试嵌套路径匹配
            nested_prompts = get_nested_value(self._prompts, category)
            if nested_prompts and isinstance(nested_prompts, dict):
                if language in nested_prompts:
                    # 如果是PromptTemplate对象
                    if hasattr(nested_prompts[language], 'content'):
                        template = nested_prompts[language]
                        template.usage_count += 1
                        return template.content
                    # 如果是字符串
                    elif isinstance(nested_prompts[language], str):
                        return nested_prompts[language]
                
                # 回退到默认语言
                default_lang = self.config.prompt.default_language
                if default_lang in nested_prompts:
                    if hasattr(nested_prompts[default_lang], 'content'):
                        template = nested_prompts[default_lang]
                        template.usage_count += 1
                        return template.content
                    elif isinstance(nested_prompts[default_lang], str):
                        return nested_prompts[default_lang]
        
        # 最后回退到内置提示词
        if category in self._builtin_prompts:
            if language in self._builtin_prompts[category]:
                return self._builtin_prompts[category][language]
            if self.config.prompt.default_language in self._builtin_prompts[category]:
                return self._builtin_prompts[category][self.config.prompt.default_language]
            if self._builtin_prompts[category]:
                return next(iter(self._builtin_prompts[category].values()))
        
        logger.warning(f"未找到提示词: category={category}, language={language}")
        # 尝试从配置文件获取默认提示词
        try:
            return self.get_prompt("default_prompts.fallback", language)
        except:
            # 最后的兜底提示词，从配置中获取
            fallback_prompts = self._prompts.get("default_prompts", {}).get("fallback", {})
            if language and language in fallback_prompts:
                return fallback_prompts[language]
            elif "zh" in fallback_prompts:
                return fallback_prompts["zh"]
            else:
                # 最终兜底，从配置文件读取
                try:
                    final_fallback = self._prompts.get("default_prompts", {}).get("fallback", {})
                    if language and language in final_fallback:
                        return final_fallback[language]
                    elif "zh" in final_fallback:
                        return final_fallback["zh"]
                except Exception:
                    pass
                return self._get_fallback_text("fallback", language)  # 从配置文件读取兜底
    
    def get_optimized_prompt(self, category: str, language: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None) -> str:
        """获取优化后的提示词"""
        base_prompt = self.get_prompt(category, language)
        
        if not self.config.prompt.enable_optimization:
            return base_prompt
        
        # 根据上下文优化提示词
        if context:
            optimized = self._optimize_prompt_with_context(base_prompt, context, language)
            return optimized
        
        return base_prompt
    
    def _get_detailed_prefix(self, language: Optional[str] = None) -> str:
        """获取详细分析前缀"""
        try:
            detailed_prefix = self._prompts.get("default_prompts", {}).get("detailed_prefix", {})
            if language and language in detailed_prefix:
                return detailed_prefix[language]
            elif "zh" in detailed_prefix:
                return detailed_prefix["zh"]
            elif "en" in detailed_prefix:
                return detailed_prefix["en"]
        except Exception:
            pass
        # 从配置文件读取兜底值
        return self._get_fallback_text("detailed_prefix", language)
    
    def _get_analysis_prefix(self, language: Optional[str] = None) -> str:
        """获取分析前缀"""
        try:
            analysis_prefix = self._prompts.get("default_prompts", {}).get("analysis_prefix", {})
            if language and language in analysis_prefix:
                return analysis_prefix[language]
            elif "zh" in analysis_prefix:
                return analysis_prefix["zh"]
            elif "en" in analysis_prefix:
                return analysis_prefix["en"]
        except Exception:
            pass
        # 从配置文件读取兜底值
        return self._get_fallback_text("analysis_prefix", language)
    
    def _get_fallback_text(self, text_type: str, language: Optional[str] = None) -> str:
        """从配置文件获取兜底文本"""
        try:
            fallback_prompts = self._prompts.get("default_prompts", {}).get("fallback", {})
            if language and language in fallback_prompts:
                return fallback_prompts[language]
            elif "zh" in fallback_prompts:
                return fallback_prompts["zh"]
            elif "en" in fallback_prompts:
                return fallback_prompts["en"]
        except Exception:
            pass
        
        # 最后的兜底，但这应该很少被使用
        if language == "en":
            return "Please analyze"
        return "请分析"
    
    def _optimize_prompt_with_context(self, prompt: str, context: Dict[str, Any], language: Optional[str] = None) -> str:
        """根据上下文优化提示词"""
        # 简单的优化策略：根据历史成功率调整
        if context.get('recent_failures', 0) > 2:
            # 如果最近失败较多，使用更详细的提示词
            detailed_prefix = self._get_detailed_prefix(language)
            analysis_prefix = self._get_analysis_prefix(language)
            if analysis_prefix not in prompt:
                # 安全地处理提示词前缀，避免破坏原有格式
                if prompt.startswith("请"):
                    cleaned_prompt = prompt[1:].strip()
                elif prompt.startswith("Please "):
                    cleaned_prompt = prompt[7:].strip()
                else:
                    cleaned_prompt = prompt
                # 确保前缀和内容之间有适当的连接
                analysis_text = self._get_fallback_text("analysis_prefix", language)
                if cleaned_prompt and not cleaned_prompt.startswith(analysis_text):
                    prompt = detailed_prefix + cleaned_prompt
                else:
                    prompt = detailed_prefix + analysis_text + cleaned_prompt
        
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
        should_optimize = False
        
        with self._cache_lock:
            if category in self._prompts and language in self._prompts[category]:
                template = self._prompts[category][language]
                
                # 先增加使用计数
                template.usage_count += 1
                total_uses = template.usage_count
                
                # 更新成功率
                if total_uses == 1:
                    # 第一次使用
                    template.success_rate = 1.0 if success else 0.0
                else:
                    # 计算新的成功率
                    current_success_rate = template.success_rate
                    new_success_rate = (current_success_rate * (total_uses - 1) + (1.0 if success else 0.0)) / total_uses
                    template.success_rate = new_success_rate
                
                # 更新平均响应时间
                if total_uses == 1:
                    # 第一次使用
                    template.avg_response_time = response_time
                else:
                    # 计算新的平均响应时间
                    current_avg_time = template.avg_response_time
                    new_avg_time = (current_avg_time * (total_uses - 1) + response_time) / total_uses
                    template.avg_response_time = new_avg_time
                
                # 检查是否需要优化（但不在锁内执行优化）
                self._optimization_counter += 1
                if (self._optimization_counter >= self.config.prompt.optimization_frequency and 
                    self.config.prompt.enable_optimization):
                    should_optimize = True
                    self._optimization_counter = 0
        
        # 在锁外执行优化，避免死锁
        if should_optimize:
            try:
                self._optimize_prompts()
            except Exception as e:
                logger.error(f"提示词优化失败: {e}")
    
    def _optimize_prompts(self):
        """优化提示词（基于性能统计）"""
        logger.info("开始优化提示词...")
        
        optimization_count = 0
        
        with self._cache_lock:
            for category, lang_templates in self._prompts.items():
                for lang, template in lang_templates.items():
                    if template.usage_count >= 5:  # 至少使用5次才进行优化
                        if template.success_rate < 0.7:  # 成功率低于70%
                            logger.info(f"提示词成功率较低，正在优化: {category}.{lang} (成功率: {template.success_rate:.2f})")
                            # 简单的优化策略：添加更详细的指导
                            analysis_prefix = self._get_analysis_prefix(lang)
                            if analysis_prefix not in template.content:
                                template.content = analysis_prefix + template.content
                            template.last_optimized = str(int(time.time()))
                            optimization_count += 1
                        
                        elif template.avg_response_time > 10.0:  # 响应时间超过10秒
                            logger.info(f"提示词响应时间较长，正在优化: {category}.{lang} (平均时间: {template.avg_response_time:.2f}s)")
                            # 简化提示词以减少响应时间
                            if len(template.content) > 100:
                                template.content = template.content[:100] + "..."
                            template.last_optimized = str(int(time.time()))
                            optimization_count += 1
        
        logger.info(f"提示词优化完成，共优化了 {optimization_count} 个提示词")
        return optimization_count > 0
    
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