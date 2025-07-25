#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
部队移动任务模块

负责自动检测空闲部队并指挥其移动。
"""

import time
from loguru import logger
from tasks.base_task import BaseTask


class ArmyMovementTask(BaseTask):
    """部队移动任务类，负责自动检测空闲部队并指挥其移动"""
    
    def __init__(self, controller, settings):
        """初始化部队移动任务
        
        Args:
            controller: 游戏控制器实例
            settings: 任务设置
        """
        super().__init__(controller, settings)
        
        # 任务特定设置
        self.idle_army_check_interval = settings.get("idle_army_check_interval", 300)  # 检查空闲部队的间隔（秒）
        self.movement_strategy = settings.get("movement_strategy", "nearest")  # 移动策略
        
        # 任务状态
        self.moved_count = 0  # 已移动部队数量
        self.last_check_time = 0  # 上次检查时间
        
        # 设置任务间隔（秒）
        self.interval = self.idle_army_check_interval
    
    def execute(self):
        """执行任务
        
        Returns:
            bool: 任务是否成功执行
        """
        current_time = time.time()
        
        # 检查是否到达检查间隔
        if current_time - self.last_check_time < self.idle_army_check_interval:
            return False
        
        # 更新检查时间
        self.last_check_time = current_time
        
        # 尝试移动空闲部队
        logger.info(f"检查空闲部队，移动策略: {self.movement_strategy}")
        success = self.controller.move_idle_army(strategy=self.movement_strategy)
        
        if success:
            # 更新状态
            self.moved_count += 1
            logger.info(f"成功移动部队，已移动 {self.moved_count} 次")
        else:
            logger.info("未找到空闲部队或移动失败")
        
        return success
    
    def reset(self):
        """重置任务状态"""
        self.moved_count = 0
        self.last_check_time = 0
        logger.info("部队移动任务已重置")