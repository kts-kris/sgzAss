#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务基类模块

为所有任务提供通用功能和接口。
"""

from abc import ABC, abstractmethod
from loguru import logger


class BaseTask(ABC):
    """任务基类，为所有任务提供通用功能和接口"""
    
    def __init__(self, controller, settings):
        """初始化任务基类
        
        Args:
            controller: 游戏控制器实例
            settings: 任务设置
        """
        self.controller = controller
        self.settings = settings
        self.enabled = True  # 任务是否启用
        self.interval = 60  # 默认任务执行间隔（秒）
    
    @abstractmethod
    def execute(self):
        """执行任务
        
        Returns:
            bool: 任务是否成功执行
        """
        pass
    
    @abstractmethod
    def reset(self):
        """重置任务状态"""
        pass
    
    def enable(self):
        """启用任务"""
        self.enabled = True
        logger.info(f"{self.__class__.__name__} 已启用")
    
    def disable(self):
        """禁用任务"""
        self.enabled = False
        logger.info(f"{self.__class__.__name__} 已禁用")
    
    def is_enabled(self):
        """检查任务是否启用
        
        Returns:
            bool: 任务是否启用
        """
        return self.enabled