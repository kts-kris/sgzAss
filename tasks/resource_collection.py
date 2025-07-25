#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
资源收集任务模块

负责定期收集游戏中的资源。
"""

import time
from loguru import logger
from tasks.base_task import BaseTask


class ResourceCollectionTask(BaseTask):
    """资源收集任务类，负责定期收集游戏中的资源"""
    
    def __init__(self, controller, settings):
        """初始化资源收集任务
        
        Args:
            controller: 游戏控制器实例
            settings: 任务设置
        """
        super().__init__(controller, settings)
        
        # 任务特定设置
        self.collection_interval = settings.get("collection_interval", 3600)  # 收集间隔（秒）
        
        # 任务状态
        self.collection_count = 0  # 已收集次数
        self.last_collection_time = 0  # 上次收集时间
        
        # 设置任务间隔（秒）
        self.interval = self.collection_interval
    
    def execute(self):
        """执行任务
        
        Returns:
            bool: 任务是否成功执行
        """
        current_time = time.time()
        
        # 检查是否到达收集间隔
        if current_time - self.last_collection_time < self.collection_interval:
            return False
        
        # 更新收集时间
        self.last_collection_time = current_time
        
        # 尝试收集资源
        logger.info("尝试收集资源")
        success = self.controller.collect_resources()
        
        if success:
            # 更新状态
            self.collection_count += 1
            logger.info(f"成功收集资源，已收集 {self.collection_count} 次")
        else:
            logger.warning("收集资源失败")
        
        return success
    
    def reset(self):
        """重置任务状态"""
        self.collection_count = 0
        self.last_collection_time = 0
        logger.info("资源收集任务已重置")