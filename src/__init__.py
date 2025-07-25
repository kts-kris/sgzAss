#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
iPad自动化控制系统

一个基于pymobiledevice3的iPad自动化控制解决方案，支持：
- USB连接和屏幕截图
- 模板匹配和VLM视觉识别
- 多种自动化执行模式
- 复杂任务流程编排

主要组件：
- models: 数据类型和异常定义
- services: 核心服务（连接、视觉、自动化）
- core: 业务逻辑（控制器、任务管理器）
- utils: 工具函数（配置、日志、辅助函数）
"""

__version__ = "2.0.0"
__author__ = "iPad Automation Team"
__description__ = "iPad自动化控制系统 - 基于pymobiledevice3的重构版本"

# 导入核心组件
from .models import (
    # 数据类型
    ExecutionMode, ActionType, ElementType, ConnectionStatus,
    Element, ActionSuggestion, Action, MatchResult, AnalysisResult,
    ExecutionResult, DeviceInfo, VLMResult, TaskConfig, SystemStatus,
    
    # 异常类
    iPadAutomationError, ConnectionError, ScreenshotError, VisionError,
    VLMError, ActionError, WebDriverError, ConfigurationError, TaskError,
    ValidationError
)

from .services import (
    ConnectionService, TunneldManager, VisionService, AutomationService,
    AutomationBackend, WebDriverBackend, PyMobileDeviceBackend
)

from .core import (
    iPadController, TaskManager, Task, TaskStep, TaskCondition,
    TaskStatus, ConditionType
)

from .utils import (
    # 配置管理
    ConfigManager, SystemConfig, get_config_manager, get_config,
    
    # 日志工具
    LoggerManager, setup_logger, get_logger, PerformanceTimer,
    
    # 通用工具
    ensure_dir, save_image, load_image, validate_element,
    format_duration, retry_on_exception
)

# 便捷导入
from .core import iPadController as Controller
from .core import TaskManager as Manager
from .utils import get_config as config
from .utils import get_logger as logger

__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    '__description__',
    
    # 核心类
    'iPadController',
    'TaskManager',
    'Controller',  # 别名
    'Manager',     # 别名
    
    # 数据类型
    'ExecutionMode',
    'ActionType', 
    'ElementType',
    'ConnectionStatus',
    'TaskStatus',
    'ConditionType',
    'Element',
    'Action',
    'MatchResult',
    'AnalysisResult',
    'ExecutionResult',
    'DeviceInfo',
    'VLMResult',
    'TaskConfig',
    'SystemStatus',
    'Task',
    'TaskStep',
    'TaskCondition',
    'ActionSuggestion',
    
    # 服务类
    'ConnectionService',
    'TunneldManager',
    'VisionService',
    'AutomationService',
    'AutomationBackend',
    'WebDriverBackend',
    'PyMobileDeviceBackend',
    
    # 异常类
    'iPadAutomationError',
    'ConnectionError',
    'ScreenshotError',
    'VisionError',
    'VLMError',
    'ActionError',
    'WebDriverError',
    'ConfigurationError',
    'TaskError',
    'ValidationError',
    
    # 工具类
    'ConfigManager',
    'SystemConfig',
    'LoggerManager',
    'PerformanceTimer',
    
    # 便捷函数
    'get_config_manager',
    'get_config',
    'config',      # 别名
    'setup_logger',
    'get_logger',
    'logger',      # 别名
    'ensure_dir',
    'save_image',
    'load_image',
    'validate_element',
    'format_duration',
    'retry_on_exception'
]


def create_controller(config_file: str = None, 
                     execution_mode: ExecutionMode = ExecutionMode.AUTO,
                     automation_backend: str = "webdriver") -> iPadController:
    """创建iPad控制器实例
    
    Args:
        config_file: 配置文件路径
        execution_mode: 执行模式
        automation_backend: 自动化后端
        
    Returns:
        iPadController: 控制器实例
    """
    # 初始化日志系统
    setup_logger()
    
    # 创建控制器
    controller = iPadController(execution_mode=execution_mode)
    
    # 设置自动化后端
    if hasattr(controller, 'set_automation_backend'):
        controller.set_automation_backend(automation_backend)
    
    return controller


def create_task_manager(controller: iPadController = None,
                       config_file: str = None) -> TaskManager:
    """创建任务管理器实例
    
    Args:
        controller: iPad控制器实例
        config_file: 配置文件路径
        
    Returns:
        TaskManager: 任务管理器实例
    """
    if controller is None:
        controller = create_controller(config_file=config_file)
    
    return TaskManager(controller)


def quick_start(config_file: str = None, 
               execution_mode: ExecutionMode = ExecutionMode.AUTO) -> tuple:
    """快速启动，返回控制器和任务管理器
    
    Args:
        config_file: 配置文件路径
        execution_mode: 执行模式
        
    Returns:
        tuple: (controller, task_manager)
    """
    controller = create_controller(config_file, execution_mode)
    task_manager = create_task_manager(controller)
    
    return controller, task_manager


# 添加便捷函数到__all__
__all__.extend([
    'create_controller',
    'create_task_manager', 
    'quick_start'
])