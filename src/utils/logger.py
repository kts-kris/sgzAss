#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志工具模块

提供统一的日志配置和管理功能。
支持控制台输出、文件输出、日志轮转等功能。
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from .config import get_config, LoggingConfig


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        """初始化日志管理器"""
        self._initialized = False
        self._handlers: Dict[str, int] = {}
    
    def setup_logger(self, config: Optional[LoggingConfig] = None):
        """设置日志配置
        
        Args:
            config: 日志配置，如果为None则使用系统配置
        """
        if self._initialized:
            return
        
        if config is None:
            system_config = get_config()
            config = system_config.logging
        
        # 移除默认处理器
        logger.remove()
        
        # 设置控制台输出
        if config.console_output:
            console_format = self._get_console_format(config)
            console_level = getattr(config, 'console_level', config.level)
            handler_id = logger.add(
                sys.stderr,
                format=console_format,
                level=console_level.upper(),
                colorize=config.colored_output,
                backtrace=True,
                diagnose=True
            )
            self._handlers['console'] = handler_id
        
        # 设置文件输出
        if config.file_path:
            file_path = Path(config.file_path).expanduser().resolve()
            
            # 确保日志目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            handler_id = logger.add(
                str(file_path),
                format=config.format,
                level=config.level.upper(),
                rotation=config.max_file_size,
                retention=config.backup_count,
                compression="zip",
                backtrace=True,
                diagnose=True,
                encoding="utf-8"
            )
            self._handlers['file'] = handler_id
        
        self._initialized = True
        logger.info("日志系统初始化完成")
    
    def _get_console_format(self, config: LoggingConfig) -> str:
        """获取控制台日志格式
        
        Args:
            config: 日志配置
            
        Returns:
            str: 控制台日志格式
        """
        if config.colored_output:
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
        else:
            return config.format
    
    def add_file_handler(self, file_path: str, level: str = "INFO",
                        format_str: Optional[str] = None,
                        rotation: str = "10 MB",
                        retention: int = 5) -> int:
        """添加文件处理器
        
        Args:
            file_path: 日志文件路径
            level: 日志级别
            format_str: 日志格式
            rotation: 轮转大小
            retention: 保留文件数
            
        Returns:
            int: 处理器ID
        """
        if format_str is None:
            config = get_config().logging
            format_str = config.format
        
        file_path = Path(file_path).expanduser().resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler_id = logger.add(
            str(file_path),
            format=format_str,
            level=level.upper(),
            rotation=rotation,
            retention=retention,
            compression="zip",
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
        
        logger.info(f"添加文件日志处理器: {file_path}")
        return handler_id
    
    def remove_handler(self, handler_id: int):
        """移除日志处理器
        
        Args:
            handler_id: 处理器ID
        """
        try:
            logger.remove(handler_id)
            logger.info(f"移除日志处理器: {handler_id}")
        except ValueError:
            logger.warning(f"日志处理器不存在: {handler_id}")
    
    def set_level(self, level: str, console_level: Optional[str] = None):
        """设置日志级别
        
        Args:
            level: 文件日志级别
            console_level: 控制台日志级别，如果为None则使用level
        """
        # 移除现有处理器
        for handler_id in list(self._handlers.values()):
            self.remove_handler(handler_id)
        
        self._handlers.clear()
        self._initialized = False
        
        # 重新设置日志
        config = get_config().logging
        config.level = level
        if console_level is not None:
            config.console_level = console_level
        self.setup_logger(config)
    
    def set_console_level(self, level: str):
        """单独设置控制台日志级别
        
        Args:
            level: 控制台日志级别
        """
        if 'console' in self._handlers:
            # 移除现有控制台处理器
            self.remove_handler(self._handlers['console'])
            del self._handlers['console']
            
            # 重新添加控制台处理器
            config = get_config().logging
            config.console_level = level
            
            if config.console_output:
                console_format = self._get_console_format(config)
                handler_id = logger.add(
                    sys.stderr,
                    format=console_format,
                    level=level.upper(),
                    colorize=config.colored_output,
                    backtrace=True,
                    diagnose=True
                )
                self._handlers['console'] = handler_id
                logger.info(f"控制台日志级别已设置为: {level}")
    
    def set_file_level(self, level: str):
        """单独设置文件日志级别
        
        Args:
            level: 文件日志级别
        """
        if 'file' in self._handlers:
            # 移除现有文件处理器
            self.remove_handler(self._handlers['file'])
            del self._handlers['file']
            
            # 重新添加文件处理器
            config = get_config().logging
            config.level = level
            
            if config.file_path:
                file_path = Path(config.file_path).expanduser().resolve()
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                handler_id = logger.add(
                    str(file_path),
                    format=config.format,
                    level=level.upper(),
                    rotation=config.max_file_size,
                    retention=config.backup_count,
                    compression="zip",
                    backtrace=True,
                    diagnose=True,
                    encoding="utf-8"
                )
                self._handlers['file'] = handler_id
                logger.info(f"文件日志级别已设置为: {level}")
    
    def get_logger(self, name: Optional[str] = None):
        """获取日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            logger: 日志器实例
        """
        if not self._initialized:
            self.setup_logger()
        
        if name:
            return logger.bind(name=name)
        else:
            return logger
    
    def create_performance_logger(self, file_path: str = "performance.log") -> int:
        """创建性能日志器
        
        Args:
            file_path: 性能日志文件路径
            
        Returns:
            int: 处理器ID
        """
        performance_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "PERF | "
            "{extra[operation]} | "
            "{extra[duration]:.3f}s | "
            "{message}"
        )
        
        return self.add_file_handler(
            file_path=file_path,
            level="INFO",
            format_str=performance_format,
            rotation="50 MB",
            retention=10
        )
    
    def create_error_logger(self, file_path: str = "errors.log") -> int:
        """创建错误日志器
        
        Args:
            file_path: 错误日志文件路径
            
        Returns:
            int: 处理器ID
        """
        error_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level} | "
            "{name}:{function}:{line} | "
            "{message}\n"
            "{exception}"
        )
        
        return self.add_file_handler(
            file_path=file_path,
            level="ERROR",
            format_str=error_format,
            rotation="20 MB",
            retention=20
        )
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """记录性能日志
        
        Args:
            operation: 操作名称
            duration: 执行时间（秒）
            details: 详细信息
        """
        perf_logger = logger.bind(operation=operation, duration=duration)
        perf_logger.info(details or f"{operation} 执行完成")
    
    def log_action(self, action_type: str, target: str, result: str, 
                  duration: float = 0, details: Dict[str, Any] = None):
        """记录操作日志
        
        Args:
            action_type: 操作类型
            target: 操作目标
            result: 操作结果
            duration: 执行时间
            details: 详细信息
        """
        action_logger = logger.bind(
            action_type=action_type,
            target=target,
            result=result,
            duration=duration
        )
        
        message = f"{action_type} -> {target}: {result}"
        if details:
            message += f" | {details}"
        
        if result.lower() in ['success', 'completed', '成功', '完成']:
            action_logger.info(message)
        elif result.lower() in ['failed', 'error', '失败', '错误']:
            action_logger.error(message)
        else:
            action_logger.warning(message)
    
    def is_initialized(self) -> bool:
        """检查日志系统是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized


# 全局日志管理器实例
_logger_manager: Optional[LoggerManager] = None


def get_logger_manager() -> LoggerManager:
    """获取全局日志管理器实例
    
    Returns:
        LoggerManager: 日志管理器实例
    """
    global _logger_manager
    
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    
    return _logger_manager


def setup_logger(config: Optional[LoggingConfig] = None):
    """设置日志系统
    
    Args:
        config: 日志配置
    """
    get_logger_manager().setup_logger(config)


def get_logger(name: Optional[str] = None):
    """获取日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        logger: 日志器实例
    """
    return get_logger_manager().get_logger(name)


def log_performance(operation: str, duration: float, details: str = ""):
    """记录性能日志
    
    Args:
        operation: 操作名称
        duration: 执行时间（秒）
        details: 详细信息
    """
    get_logger_manager().log_performance(operation, duration, details)


def log_action(action_type: str, target: str, result: str, 
              duration: float = 0, details: Dict[str, Any] = None):
    """记录操作日志
    
    Args:
        action_type: 操作类型
        target: 操作目标
        result: 操作结果
        duration: 执行时间
        details: 详细信息
    """
    get_logger_manager().log_action(action_type, target, result, duration, details)


def set_log_level(level: str, console_level: Optional[str] = None):
    """设置日志级别
    
    Args:
        level: 文件日志级别
        console_level: 控制台日志级别，如果为None则使用level
    """
    get_logger_manager().set_level(level, console_level)


def set_console_log_level(level: str):
    """设置控制台日志级别
    
    Args:
        level: 控制台日志级别
    """
    get_logger_manager().set_console_level(level)


def set_file_log_level(level: str):
    """设置文件日志级别
    
    Args:
        level: 文件日志级别
    """
    get_logger_manager().set_file_level(level)


class PerformanceTimer:
    """性能计时器上下文管理器"""
    
    def __init__(self, operation: str, details: str = "", 
                 auto_log: bool = True, logger_name: Optional[str] = None):
        """初始化性能计时器
        
        Args:
            operation: 操作名称
            details: 详细信息
            auto_log: 是否自动记录日志
            logger_name: 日志器名称
        """
        self.operation = operation
        self.details = details
        self.auto_log = auto_log
        self.logger = get_logger(logger_name)
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        """进入上下文"""
        import time
        self.start_time = time.time()
        self.logger.debug(f"开始执行: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        import time
        self.duration = time.time() - self.start_time
        
        if self.auto_log:
            if exc_type is None:
                log_performance(self.operation, self.duration, self.details)
                self.logger.debug(f"完成执行: {self.operation} ({self.duration:.3f}s)")
            else:
                self.logger.error(f"执行失败: {self.operation} ({self.duration:.3f}s) - {exc_val}")
    
    def get_duration(self) -> Optional[float]:
        """获取执行时间
        
        Returns:
            float: 执行时间（秒），如果未完成则返回None
        """
        return self.duration


def performance_timer(operation: str, details: str = "", 
                     auto_log: bool = True, logger_name: Optional[str] = None):
    """性能计时器装饰器
    
    Args:
        operation: 操作名称
        details: 详细信息
        auto_log: 是否自动记录日志
        logger_name: 日志器名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceTimer(operation, details, auto_log, logger_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator