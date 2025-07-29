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
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field, asdict
from loguru import logger

from ..models import ConfigurationError


@dataclass
class ConnectionConfig:
    """连接配置"""
    connection_mode: str = "usb"  # usb, wifi, auto
    timeout: float = 30.0  # 连接超时时间
    retry_count: int = 3  # 重试次数
    usb_timeout: float = 30.0
    screenshot_timeout: float = 10.0
    tunneld_port_range: tuple = field(default_factory=lambda: (49152, 65535))
    max_retry_attempts: int = 3
    retry_delay: float = 1.0
    device_udid: Optional[str] = None


@dataclass
class OllamaConfig:
    """Ollama VLM配置"""
    host: str = "localhost"
    port: int = 11434
    model: str = "qwen2.5vl:latest"
    timeout: float = 60.0
    max_retries: int = 3
    image_max_size: tuple = field(default_factory=lambda: (1024, 1024))
    image_quality: int = 85


@dataclass
class VisionConfig:
    """视觉识别配置"""
    template_dir: str = "resources/templates"
    template_threshold: float = 0.8
    nms_threshold: float = 0.3
    max_templates: int = 100
    cache_templates: bool = True
    enable_vlm: bool = True  # 修改为 enable_vlm 以匹配 CLI 代码
    vlm_enabled: bool = True
    vlm_provider: str = "ollama"  # openai, anthropic, google, ollama
    vlm_model: str = "gpt-4-vision-preview"
    vlm_api_key: Optional[str] = None
    vlm_base_url: Optional[str] = None
    vlm_timeout: float = 30.0
    vlm_max_retries: int = 3
    ollama_config: OllamaConfig = field(default_factory=OllamaConfig)
    
    # 模板匹配配置
    template_matching: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "template_dir": "templates",
        "confidence_threshold": 0.7,
        "fallback_enabled": True,
        "fallback_threshold": 0.5
    })


@dataclass
class ActionConfig:
    """操作配置"""
    delay: float = 0.5
    click_duration: float = 0.1
    swipe_duration: float = 1.0
    long_press_duration: float = 2.0


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
    actions: ActionConfig = field(default_factory=ActionConfig)


@dataclass
class ContinuousModeConfig:
    """持续运行模式配置"""
    enabled: bool = False
    default_interval: float = 60.0  # 默认60秒间隔，避免API调用超时
    min_interval: float = 30.0      # 最小30秒间隔，确保API调用稳定
    max_iterations: int = 0
    auto_execute: bool = False
    priority_threshold: float = 0.7
    save_results: bool = True
    results_dir: str = "logs/continuous_results"


@dataclass
class AutoAnalysisConfig:
    """自动分析配置"""
    enabled: bool = False
    interval: float = 5.0
    priority: int = 0


@dataclass
class AsyncAnalysisConfig:
    """异步分析配置"""
    enabled: bool = True
    max_concurrent_analyses: int = 3
    history_limit: int = 100
    auto_analysis: AutoAnalysisConfig = field(default_factory=AutoAnalysisConfig)
    continuous_mode: ContinuousModeConfig = field(default_factory=ContinuousModeConfig)
    prompt_optimization_enabled: bool = True
    min_history_count: int = 5
    optimization_interval: int = 50
    auto_optimize: bool = False
    console_output_enabled: bool = True
    file_output_enabled: bool = True
    output_file_path: str = "logs/analysis_results.log"
    max_elements_display: int = 5
    max_suggestions_display: int = 3


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"  # 文件日志等级
    console_level: str = "INFO"  # 控制台日志等级
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    file_path: Optional[str] = None
    max_file_size: str = "10 MB"
    backup_count: int = 5
    console_output: bool = True
    colored_output: bool = True


@dataclass
class ScreenshotConfig:
    """截图管理配置"""
    max_keep_count: int = 3  # 最大保留截图数量
    auto_cleanup: bool = True  # 是否自动清理
    cleanup_patterns: List[str] = field(default_factory=lambda: [
        "screenshot_*.png", "analysis_*.png", "auto_screenshot_*.png"
    ])  # 清理文件模式
    cleanup_on_save: bool = True  # 保存时自动清理
    keep_analysis_screenshots: bool = True  # 保留分析截图


@dataclass
class PromptConfig:
    """提示词配置"""
    config_file: str = "prompts.yaml"  # 提示词配置文件路径
    default_language: str = "zh"  # 默认语言
    enable_optimization: bool = True  # 是否启用提示词优化
    cache_prompts: bool = True  # 是否缓存提示词
    optimization_frequency: int = 10  # 优化频率
    max_prompt_length: int = 1000  # 最大提示词长度
    fallback_to_builtin: bool = True  # 配置文件加载失败时是否回退到内置提示词


@dataclass
class SystemConfig:
    """系统配置"""
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    automation: AutomationConfig = field(default_factory=AutomationConfig)
    async_analysis: AsyncAnalysisConfig = field(default_factory=AsyncAnalysisConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    screenshot: ScreenshotConfig = field(default_factory=ScreenshotConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    
    # 全局设置
    debug_mode: bool = False
    performance_monitoring: bool = True
    auto_save_screenshots: bool = False
    save_analysis_screenshots: bool = True  # 是否保存分析时的截图
    screenshot_dir: str = "resources"
    data_dir: str = "data"
    temp_dir: str = "temp"
    
    def get_vlm_config(self) -> OllamaConfig:
        """获取VLM配置"""
        return self.vision.ollama_config


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
            'IPAD_CONNECTION_MODE': ('connection.connection_mode', str),
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
        # 定义SystemConfig中已知的顶级配置项
        known_top_level_keys = {
            'connection', 'vision', 'automation', 'async_analysis', 
            'logging', 'screenshot', 'prompt', 'debug_mode', 
            'performance_monitoring', 'auto_save_screenshots', 
            'save_analysis_screenshots', 'screenshot_dir', 'data_dir', 'temp_dir'
        }
        
        def update_nested(obj, updates, path=""):
            for key, value in updates.items():
                current_path = f"{path}.{key}" if path else key
                
                if hasattr(obj, key):
                    current_value = getattr(obj, key)
                    if isinstance(current_value, (ConnectionConfig, VisionConfig, 
                                                AutomationConfig, AsyncAnalysisConfig,
                                                LoggingConfig, OllamaConfig, ContinuousModeConfig,
                                                ScreenshotConfig, PromptConfig, ActionConfig, AutoAnalysisConfig)):
                        if isinstance(value, dict):
                            update_nested(current_value, value, current_path)
                        else:
                            logger.warning(f"配置项 {current_path} 应该是字典类型")
                    else:
                        setattr(obj, key, value)
                        logger.debug(f"更新配置项: {current_path} = {value}")
                else:
                    # 只对顶级未知配置项发出警告，忽略嵌套的未知配置项
                    if not path and key not in known_top_level_keys:
                        logger.debug(f"跳过未知的顶级配置项: {key}")
        
        # 只处理已知的顶级配置项
        filtered_data = {k: v for k, v in data.items() if k in known_top_level_keys}
        update_nested(self.config, filtered_data)
    
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
        valid_connection_modes = ['usb', 'wifi', 'auto']
        if self.config.connection.connection_mode not in valid_connection_modes:
            raise ConfigurationError(f"无效的连接模式: {self.config.connection.connection_mode}")
        
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
            valid_providers = ['openai', 'anthropic', 'google', 'ollama']
            if self.config.vision.vlm_provider not in valid_providers:
                raise ConfigurationError(f"无效的VLM提供商: {self.config.vision.vlm_provider}")
            
            # 验证非Ollama提供商的API密钥
            if self.config.vision.vlm_provider != 'ollama' and not self.config.vision.vlm_api_key:
                logger.warning(f"VLM提供商 {self.config.vision.vlm_provider} 已启用但未设置API密钥")
            
            # 验证Ollama配置
            if self.config.vision.vlm_provider == 'ollama':
                ollama_config = self.config.vision.ollama_config
                if ollama_config.port <= 0 or ollama_config.port > 65535:
                    raise ConfigurationError(f"无效的Ollama端口: {ollama_config.port}")
                if ollama_config.timeout <= 0:
                    raise ConfigurationError("Ollama超时时间必须大于0")
                if not ollama_config.model:
                    raise ConfigurationError("Ollama模型名称不能为空")
        
        # 验证异步分析配置
        if self.config.async_analysis.enabled:
            if self.config.async_analysis.max_concurrent_analyses <= 0:
                raise ConfigurationError("最大并发分析任务数必须大于0")
            if self.config.async_analysis.history_limit <= 0:
                raise ConfigurationError("分析历史记录限制必须大于0")
            if self.config.async_analysis.auto_analysis.interval <= 0:
                raise ConfigurationError("自动分析间隔必须大于0")
            if self.config.async_analysis.min_history_count <= 0:
                raise ConfigurationError("最少历史记录数必须大于0")
            if self.config.async_analysis.optimization_interval <= 0:
                raise ConfigurationError("优化间隔必须大于0")
    
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
    
    def get_vlm_config(self) -> OllamaConfig:
        """获取VLM配置
        
        Returns:
            OllamaConfig: VLM配置对象
        """
        return self.config.get_vlm_config()


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