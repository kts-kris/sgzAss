#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具模块

包含系统配置管理、日志工具和通用辅助函数：
- config: 配置管理器和配置类
- logger: 日志管理器和日志工具
- helpers: 通用工具函数
"""

from .config import (
    ConfigManager, SystemConfig, ConnectionConfig, VisionConfig,
    AutomationConfig, LoggingConfig, get_config_manager, get_config
)
from .logger import (
    LoggerManager, get_logger_manager, setup_logger, get_logger,
    log_performance, log_action, PerformanceTimer, performance_timer
)
from .helpers import (
    ensure_dir, get_timestamp, generate_filename, calculate_file_hash,
    save_json, load_json, save_image, load_image, resize_image, crop_image,
    draw_rectangle, draw_circle, draw_text, calculate_distance, calculate_center,
    is_point_in_rect, calculate_overlap_area, calculate_iou, validate_coordinates,
    validate_rectangle, clamp_coordinates, clamp_rectangle, create_temp_file,
    create_temp_dir, cleanup_temp_files, format_duration, format_file_size,
    validate_element, validate_match_result, safe_divide, retry_on_exception
)

__all__ = [
    # 配置管理
    'ConfigManager',
    'SystemConfig',
    'ConnectionConfig', 
    'VisionConfig',
    'AutomationConfig',
    'LoggingConfig',
    'get_config_manager',
    'get_config',
    
    # 日志工具
    'LoggerManager',
    'get_logger_manager',
    'setup_logger',
    'get_logger',
    'log_performance',
    'log_action',
    'PerformanceTimer',
    'performance_timer',
    
    # 通用工具
    'ensure_dir',
    'get_timestamp',
    'generate_filename',
    'calculate_file_hash',
    'save_json',
    'load_json',
    'save_image',
    'load_image',
    'resize_image',
    'crop_image',
    'draw_rectangle',
    'draw_circle',
    'draw_text',
    'calculate_distance',
    'calculate_center',
    'is_point_in_rect',
    'calculate_overlap_area',
    'calculate_iou',
    'validate_coordinates',
    'validate_rectangle',
    'clamp_coordinates',
    'clamp_rectangle',
    'create_temp_file',
    'create_temp_dir',
    'cleanup_temp_files',
    'format_duration',
    'format_file_size',
    'validate_element',
    'validate_match_result',
    'safe_divide',
    'retry_on_exception'
]