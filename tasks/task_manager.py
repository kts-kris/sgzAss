#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务管理器模块

负责管理和执行各种自动化任务，如土地占领、部队移动、资源收集等。
"""

import time
from loguru import logger
from tasks.land_occupation import LandOccupationTask
from tasks.army_movement import ArmyMovementTask
from tasks.resource_collection import ResourceCollectionTask


class TaskManager:
    """任务管理器类，负责管理和执行各种自动化任务"""
    
    def __init__(self, controller, task_settings):
        """初始化任务管理器
        
        Args:
            controller: 游戏控制器实例
            task_settings: 任务设置
        """
        self.controller = controller
        self.settings = task_settings
        
        # 初始化任务列表
        self.tasks = {}
        self._init_tasks()
        
        # 任务执行状态
        self.last_execution_time = {}
    
    def _init_tasks(self):
        """初始化任务列表"""
        # 土地占领任务
        land_settings = self.settings.get("land_occupation", {})
        if land_settings.get("enabled", True):
            self.tasks["land_occupation"] = LandOccupationTask(
                self.controller,
                land_settings
            )
            logger.info("已启用土地占领任务")
        
        # 部队移动任务
        army_settings = self.settings.get("army_movement", {})
        if army_settings.get("enabled", True):
            self.tasks["army_movement"] = ArmyMovementTask(
                self.controller,
                army_settings
            )
            logger.info("已启用部队移动任务")
        
        # 资源收集任务
        resource_settings = self.settings.get("resource_collection", {})
        if resource_settings.get("enabled", True):
            self.tasks["resource_collection"] = ResourceCollectionTask(
                self.controller,
                resource_settings
            )
            logger.info("已启用资源收集任务")
    
    def enable_only(self, task_names):
        """只启用指定的任务，禁用其他任务
        
        Args:
            task_names: 要启用的任务名称列表
        """
        for task_name in self.tasks.keys():
            if task_name in task_names:
                self.tasks[task_name].enabled = True
                logger.info(f"已启用任务: {task_name}")
            else:
                self.tasks[task_name].enabled = False
                logger.info(f"已禁用任务: {task_name}")
    
    def run_cycle(self):
        """运行一个任务循环"""
        current_time = time.time()
        
        for task_name, task in self.tasks.items():
            if not task.enabled:
                continue
            
            # 检查任务是否应该执行
            last_time = self.last_execution_time.get(task_name, 0)
            if current_time - last_time < task.interval:
                continue
            
            # 执行任务
            logger.debug(f"执行任务: {task_name}")
            success = task.execute()
            
            # 更新执行时间
            self.last_execution_time[task_name] = current_time
            
            # 如果任务成功，可以考虑给予一些奖励（如减少下次执行间隔）
            if success:
                logger.info(f"任务 {task_name} 执行成功")
            else:
                logger.warning(f"任务 {task_name} 执行失败")