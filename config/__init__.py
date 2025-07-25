#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置包初始化文件
"""

# 从父目录的config.py导入所有配置
import sys
import os

# 添加父目录到Python路径
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入配置
from settings import (
    GAME_SETTINGS,
    DEVICE_SETTINGS, 
    LOG_SETTINGS,
    TASK_SETTINGS,
    GAME_TEMPLATES,
    BASE_DIR,
    RESOURCE_DIR,
    TEMPLATE_DIR,
    SCREENSHOT_DIR
)

# 导出所有配置
__all__ = [
    'GAME_SETTINGS',
    'DEVICE_SETTINGS',
    'LOG_SETTINGS', 
    'TASK_SETTINGS',
    'GAME_TEMPLATES',
    'BASE_DIR',
    'RESOURCE_DIR',
    'TEMPLATE_DIR',
    'SCREENSHOT_DIR'
]