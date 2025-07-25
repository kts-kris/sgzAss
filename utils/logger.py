#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志工具模块

提供日志记录功能，支持控制台输出和文件记录。
"""

import os
import sys
from loguru import logger


def setup_logger(log_settings, debug=False):
    """设置日志记录器
    
    Args:
        log_settings: 日志设置
        debug: 是否启用调试模式
        
    Returns:
        logger: 配置好的日志记录器
    """
    # 移除默认处理器
    logger.remove()
    
    # 设置日志级别
    log_level = log_settings.get("log_level", "INFO")
    if debug:
        log_level = "DEBUG"
    
    # 添加控制台处理器
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 添加文件处理器
    log_file = log_settings.get("log_file")
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        # 添加文件处理器
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=log_settings.get("rotation", "500 MB"),
            compression="zip",
            retention="10 days"
        )
    
    logger.info(f"日志系统初始化完成，日志级别: {log_level}")
    return logger