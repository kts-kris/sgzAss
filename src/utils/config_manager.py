#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
统一管理应用程序的所有配置
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"配置文件加载成功: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self.config = self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "device": {
                "connection_type": "usb",
                "device_id": None,
                "connection_timeout": 30,
                "reconnect_interval": 5,
                "max_reconnect_attempts": 3,
                "screenshot": {
                    "timeout": 15,
                    "max_retries": 3,
                    "retry_interval": 2,
                    "external_timeout": 10,
                    "quality_check": True,
                    "min_file_size": 1024
                }
            },
            "vision": {
                "vlm": {
                    "enabled": True,
                    "provider": "ollama"
                },
                "ollama_config": {
                    "base_url": "http://localhost:11434",
                    "model": "llava:latest",
                    "timeout": 60,
                    "max_retries": 3,
                    "image_max_size": [800, 600],
                    "image_quality": 75
                },
                "template_matching": {
                    "enabled": True,
                    "template_dir": "templates",
                    "confidence_threshold": 0.6,
                    "fallback_enabled": True,
                    "fallback_threshold": 0.3
                }
            },
            "automation": {
                "action_delay": 1.0,
                "max_retry_attempts": 3,
                "retry_delay": 2.0,
                "screenshot_before_action": True,
                "screenshot_after_action": True
            },
            "async_analysis": {
                "enabled": True,
                "max_concurrent_tasks": 2,
                "task_timeout": 120,
                "history_limit": 10
            },
            "continuous_mode": {
                "enabled": False,
                "interval": 5.0,
                "max_iterations": 10,
                "auto_stop_on_no_action": True
            },
            "logging": {
                "level": "INFO",
                "file_path": "logs/game_assistant.log",
                "max_file_size": "10MB",
                "backup_count": 5,
                "console_output": True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 创建嵌套字典结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置已保存到: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def reload(self):
        """重新加载配置文件"""
        self._load_config()
        logger.info("配置已重新加载")
    
    def get_device_config(self) -> Dict[str, Any]:
        """获取设备配置"""
        return self.get('device', {})
    
    def get_vision_config(self) -> Dict[str, Any]:
        """获取视觉识别配置"""
        return self.get('vision', {})
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """获取Ollama配置"""
        return self.get('vision.ollama_config', {})
    
    def get_template_config(self) -> Dict[str, Any]:
        """获取模板匹配配置"""
        return self.get('vision.template_matching', {})
    
    def get_automation_config(self) -> Dict[str, Any]:
        """获取自动化配置"""
        return self.get('automation', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})
    
    def is_vlm_enabled(self) -> bool:
        """检查VLM是否启用"""
        return self.get('vision.vlm.enabled', True)
    
    def is_template_matching_enabled(self) -> bool:
        """检查模板匹配是否启用"""
        return self.get('vision.template_matching.enabled', True)
    
    def is_async_analysis_enabled(self) -> bool:
        """检查异步分析是否启用"""
        return self.get('async_analysis.enabled', True)
    
    def is_continuous_mode_enabled(self) -> bool:
        """检查持续运行模式是否启用"""
        return self.get('continuous_mode.enabled', False)
    
    def get_screenshot_config(self) -> Dict[str, Any]:
        """获取截图配置"""
        return self.get('device.screenshot', {})
    
    def validate_config(self) -> bool:
        """验证配置的有效性
        
        Returns:
            配置是否有效
        """
        try:
            # 检查必要的配置项
            required_keys = [
                'device.connection_type',
                'vision.vlm.enabled',
                'vision.ollama_config.base_url',
                'vision.ollama_config.model'
            ]
            
            for key in required_keys:
                if self.get(key) is None:
                    logger.error(f"缺少必要的配置项: {key}")
                    return False
            
            # 检查数值范围
            timeout = self.get('vision.ollama_config.timeout', 60)
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                logger.error(f"无效的超时配置: {timeout}")
                return False
            
            # 检查模板目录
            template_dir = self.get('vision.template_matching.template_dir')
            if template_dir:
                template_path = Path(template_dir)
                if not template_path.is_absolute():
                    # 相对路径，基于项目根目录
                    project_root = Path(__file__).parent.parent.parent
                    template_path = project_root / template_dir
                
                if not template_path.exists():
                    logger.warning(f"模板目录不存在: {template_path}")
            
            logger.info("配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def reload_config(self) -> None:
        """重新加载配置文件"""
        try:
            self.config = self._load_config()
            logger.info("配置文件重新加载成功")
        except Exception as e:
            logger.error(f"配置文件重新加载失败: {e}")
            raise
    
    def update_config(self, updates: Dict[str, Any]):
        """批量更新配置
        
        Args:
            updates: 要更新的配置字典
        """
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config, updates)
        logger.info("配置已批量更新")


# 全局配置管理器实例
_config_manager = None

def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """获取全局配置管理器实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager

def reload_config():
    """重新加载全局配置"""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload()