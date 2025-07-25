#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块

负责系统配置的加载、验证和管理。
支持从文件、环境变量和命令行参数加载配置。
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from loguru import logger

from ..models import ConfigurationError


@dataclass
class ConnectionConfig:
    """连接配置"""
    usb_timeout: float = 30.0
    screenshot_timeout: float = 10.0
    tunneld_port_range: tuple = field(default_factory=lambda: (49152, 65535))
    max_retry_attempts: int = 3
    retry_delay: float = 1.0
    device_udid: Optional[str] = None


@dataclass
class VisionConfig:
    """视觉识别配置"""
    template_dir: str = "templates"
    template_threshold: float = 0.8
    nms_threshold: float = 0.3
    max_templates: int = 100
    cache_templates: bool = True
    vlm_enabled: bool = False
    vlm_provider: str = "openai"  # openai, anthropic, google
    vlm_model: str = "gpt-4-vision-preview"
    vlm_api_key: Optional[str] = None
    vlm_base_url: Optional[str] = None
    vlm_timeout: float = 30.0
    vlm_max_retries: int = 3


@dataclass
class AutomationConfig:
    """自动化配置"""
    default_backend: str = "webdriver"  # webdriver, pymobiledevice
    webdriver_url: str = "http://localhost:8100"
    webdriver_timeout: float = 30.0
    default_execution_mode: str = "execute"  # suggest, execute
    action_delay: float = 0.5
    screenshot_before_action: bool = True
    screenshot_after_action: bool = False
    max_action_history: int = 100


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    file_path: Optional[str] = None
    max_file_size: str = "10 MB"
    backup_count: int = 5
    console_output: bool = True
    colored_output: bool = True


@dataclass
class SystemConfig:
    """系统配置"""
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    automation: AutomationConfig = field(default_factory=AutomationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # 全局设置
    debug_mode: bool = False
    performance_monitoring: bool = True
    auto_save_screenshots: bool = False
    screenshot_dir: str = "resources"
    data_dir: str = "data"
    temp_dir: str = "temp"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = SystemConfig()
        
        # 默认配置文件路径
        if not self.config_file:
            self.config_file = self._find_config_file()
        
        # 加载配置
        self._load_config()
    
    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        # 可能的配置文件位置
        possible_paths = [
            "config.yaml",
            "config.yml", 
            "config.json",
            "~/.ipad_automation/config.yaml",
            "~/.ipad_automation/config.yml",
            "~/.ipad_automation/config.json",
            "/etc/ipad_automation/config.yaml",
            "/etc/ipad_automation/config.yml",
            "/etc/ipad_automation/config.json"
        ]
        
        for path in possible_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                logger.info(f"找到配置文件: {expanded_path}")
                return str(expanded_path)
        
        logger.info("未找到配置文件，使用默认配置")
        return None
    
    def _load_config(self):
        """加载配置"""
        try:
            # 从文件加载
            if self.config_file and Path(self.config_file).exists():
                self._load_from_file()
            
            # 从环境变量加载
            self._load_from_env()
            
            # 验证配置
            self._validate_config()
            
            logger.info("配置加载完成")
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise ConfigurationError(f"配置加载失败: {e}")
    
    def _load_from_file(self):
        """从文件加载配置"""
        config_path = Path(self.config_file)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ConfigurationError(f"不支持的配置文件格式: {config_path.suffix}")
            
            # 更新配置
            self._update_config_from_dict(data)
            
            logger.debug(f"从文件加载配置: {config_path}")
            
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            raise ConfigurationError(f"读取配置文件失败: {e}")
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            # 连接配置
            'IPAD_USB_TIMEOUT': ('connection.usb_timeout', float),
            'IPAD_SCREENSHOT_TIMEOUT': ('connection.screenshot_timeout', float),
            'IPAD_DEVICE_UDID': ('connection.device_udid', str),
            
            # 视觉配置
            'IPAD_TEMPLATE_DIR': ('vision.template_dir', str),
            'IPAD_TEMPLATE_THRESHOLD': ('vision.template_threshold', float),
            'IPAD_VLM_ENABLED': ('vision.vlm_enabled', bool),
            'IPAD_VLM_PROVIDER': ('vision.vlm_provider', str),
            'IPAD_VLM_MODEL': ('vision.vlm_model', str),
            'IPAD_VLM_API_KEY': ('vision.vlm_api_key', str),
            'IPAD_VLM_BASE_URL': ('vision.vlm_base_url', str),
            
            # 自动化配置
            'IPAD_DEFAULT_BACKEND': ('automation.default_backend', str),
            'IPAD_WEBDRIVER_URL': ('automation.webdriver_url', str),
            'IPAD_EXECUTION_MODE': ('automation.default_execution_mode', str),
            
            # 日志配置
            'IPAD_LOG_LEVEL': ('logging.level', str),
            'IPAD_LOG_FILE': ('logging.file_path', str),
            
            # 全局设置
            'IPAD_DEBUG_MODE': ('debug_mode', bool),
            'IPAD_SCREENSHOT_DIR': ('screenshot_dir', str),
            'IPAD_DATA_DIR': ('data_dir', str)
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # 类型转换
                    if value_type == bool:
                        value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == float:
                        value = float(env_value)
                    elif value_type == int:
                        value = int(env_value)
                    else:
                        value = env_value
                    
                    # 设置配置值
                    self._set_nested_config(config_path, value)
                    
                    logger.debug(f"从环境变量加载配置: {env_var} = {value}")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"环境变量 {env_var} 值无效: {env_value}, 错误: {e}")
    
    def _update_config_from_dict(self, data: Dict[str, Any]):
        """从字典更新配置"""
        def update_nested(obj, updates):
            for key, value in updates.items():
                if hasattr(obj, key):
                    current_value = getattr(obj, key)
                    if isinstance(current_value, (ConnectionConfig, VisionConfig, 
                                                AutomationConfig, LoggingConfig)):
                        if isinstance(value, dict):
                            update_nested(current_value, value)
                        else:
                            logger.warning(f"配置项 {key} 应该是字典类型")
                    else:
                        setattr(obj, key, value)
                else:
                    logger.warning(f"未知的配置项: {key}")
        
        update_nested(self.config, data)
    
    def _set_nested_config(self, path: str, value: Any):
        """设置嵌套配置值"""
        parts = path.split('.')
        obj = self.config
        
        # 导航到父对象
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                logger.warning(f"配置路径不存在: {path}")
                return
        
        # 设置最终值
        final_key = parts[-1]
        if hasattr(obj, final_key):
            setattr(obj, final_key, value)
        else:
            logger.warning(f"配置项不存在: {path}")
    
    def _validate_config(self):
        """验证配置"""
        # 验证连接配置
        if self.config.connection.usb_timeout <= 0:
            raise ConfigurationError("USB超时时间必须大于0")
        
        if self.config.connection.screenshot_timeout <= 0:
            raise ConfigurationError("截图超时时间必须大于0")
        
        # 验证视觉配置
        if not (0 < self.config.vision.template_threshold <= 1):
            raise ConfigurationError("模板匹配阈值必须在0到1之间")
        
        if not (0 < self.config.vision.nms_threshold <= 1):
            raise ConfigurationError("NMS阈值必须在0到1之间")
        
        # 验证自动化配置
        valid_backends = ['webdriver', 'pymobiledevice']
        if self.config.automation.default_backend not in valid_backends:
            raise ConfigurationError(f"无效的自动化后端: {self.config.automation.default_backend}")
        
        valid_modes = ['suggest', 'execute']
        if self.config.automation.default_execution_mode not in valid_modes:
            raise ConfigurationError(f"无效的执行模式: {self.config.automation.default_execution_mode}")
        
        # 验证日志配置
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.logging.level.upper() not in valid_levels:
            raise ConfigurationError(f"无效的日志级别: {self.config.logging.level}")
        
        # 验证VLM配置
        if self.config.vision.vlm_enabled:
            if not self.config.vision.vlm_api_key:
                logger.warning("VLM已启用但未设置API密钥")
            
            valid_providers = ['openai', 'anthropic', 'google']
            if self.config.vision.vlm_provider not in valid_providers:
                raise ConfigurationError(f"无效的VLM提供商: {self.config.vision.vlm_provider}")
    
    def get_config(self) -> SystemConfig:
        """获取系统配置
        
        Returns:
            SystemConfig: 系统配置对象
        """
        return self.config
    
    def save_config(self, file_path: Optional[str] = None):
        """保存配置到文件
        
        Args:
            file_path: 保存路径，默认使用当前配置文件路径
        """
        save_path = file_path or self.config_file
        
        if not save_path:
            save_path = "config.yaml"
        
        save_path = Path(save_path)
        
        try:
            # 确保目录存在
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为字典
            config_dict = asdict(self.config)
            
            # 保存文件
            with open(save_path, 'w', encoding='utf-8') as f:
                if save_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_dict, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
                elif save_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                else:
                    # 默认使用YAML格式
                    yaml.dump(config_dict, f, default_flow_style=False,
                             allow_unicode=True, indent=2)
            
            logger.info(f"配置已保存到: {save_path}")
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise ConfigurationError(f"保存配置失败: {e}")
    
    def reload_config(self):
        """重新加载配置"""
        logger.info("重新加载配置")
        self._load_config()
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置
        
        Args:
            updates: 要更新的配置项
        """
        self._update_config_from_dict(updates)
        self._validate_config()
        logger.info("配置已更新")
    
    def get_template_dir(self) -> Path:
        """获取模板目录路径
        
        Returns:
            Path: 模板目录路径
        """
        template_dir = Path(self.config.vision.template_dir)
        if not template_dir.is_absolute():
            template_dir = Path(self.config.data_dir) / template_dir
        
        return template_dir.expanduser().resolve()
    
    def get_screenshot_dir(self) -> Path:
        """获取截图目录路径
        
        Returns:
            Path: 截图目录路径
        """
        screenshot_dir = Path(self.config.screenshot_dir)
        if not screenshot_dir.is_absolute():
            screenshot_dir = Path(self.config.data_dir) / screenshot_dir
        
        return screenshot_dir.expanduser().resolve()
    
    def get_data_dir(self) -> Path:
        """获取数据目录路径
        
        Returns:
            Path: 数据目录路径
        """
        return Path(self.config.data_dir).expanduser().resolve()
    
    def get_temp_dir(self) -> Path:
        """获取临时目录路径
        
        Returns:
            Path: 临时目录路径
        """
        return Path(self.config.temp_dir).expanduser().resolve()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """获取全局配置管理器实例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    
    return _config_manager


def get_config(config_file: Optional[str] = None) -> SystemConfig:
    """获取系统配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        SystemConfig: 系统配置对象
    """
    return get_config_manager(config_file).get_config()