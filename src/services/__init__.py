#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
服务模块

提供核心服务类的统一导入接口。
包含连接服务、视觉识别服务和自动化执行服务。
"""

from .connection import ConnectionService, TunneldManager
from .vision import VisionService
from .automation import (
    AutomationService, AutomationBackend, 
    WebDriverBackend, PyMobileDeviceBackend
)

__all__ = [
    # 连接服务
    "ConnectionService",
    "TunneldManager",
    
    # 视觉识别服务
    "VisionService",
    
    # 自动化执行服务
    "AutomationService",
    "AutomationBackend",
    "WebDriverBackend",
    "PyMobileDeviceBackend",
]