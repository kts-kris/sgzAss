#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
土地占领任务模块

负责自动寻找并占领土地或资源点。
"""

import time
from loguru import logger
from tasks.base_task import BaseTask


class LandOccupationTask(BaseTask):
    """土地占领任务类，负责自动寻找并占领土地或资源点"""
    
    def __init__(self, controller, settings):
        """初始化土地占领任务
        
        Args:
            controller: 游戏控制器实例
            settings: 任务设置
        """
        super().__init__(controller, settings)
        
        # 任务特定设置
        self.target_count = settings.get("target_count", 10)  # 目标占领数量
        self.prefer_resources = settings.get("prefer_resources", True)  # 优先占领资源点
        self.max_distance = settings.get("max_distance", 500)  # 最大搜索距离（像素）
        
        # 任务状态
        self.occupied_count = 0  # 已占领数量
        self.last_success_time = 0  # 上次成功占领的时间
        
        # 设置任务间隔（秒）
        self.interval = 10  # 每10秒尝试一次占领
    
    def execute(self):
        """执行任务
        
        Returns:
            bool: 任务是否成功执行
        """
        # 检查是否已达到目标占领数量
        if self.occupied_count >= self.target_count:
            logger.info(f"已达到目标占领数量: {self.target_count}")
            return True
        
        # 尝试占领土地
        logger.info(f"尝试占领土地 ({self.occupied_count + 1}/{self.target_count})")
        success = self.controller.find_and_occupy_land(
            prefer_resources=self.prefer_resources,
            max_distance=self.max_distance
        )
        
        if success:
            # 更新状态
            self.occupied_count += 1
            self.last_success_time = time.time()
            logger.info(f"成功占领土地，当前进度: {self.occupied_count}/{self.target_count}")
            
            # 如果连续成功，可以减少间隔时间，加快占领速度
            if self.interval > 5:
                self.interval = max(5, self.interval - 1)
        else:
            logger.warning("占领土地失败")
            
            # 如果失败，增加间隔时间，避免频繁尝试
            self.interval = min(30, self.interval + 5)
        
        return success
    
    def reset(self):
        """重置任务状态"""
        self.occupied_count = 0
        self.last_success_time = 0
        self.interval = 10
        logger.info("土地占领任务已重置")