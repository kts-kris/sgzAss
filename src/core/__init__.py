#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
核心模块

包含主要的业务逻辑组件：
- iPadController: 主控制器，整合所有服务
- TaskManager: 任务管理器，负责复杂任务流程编排
"""

from .controller import iPadController
from .task_manager import (
    TaskManager, Task, TaskStep, TaskCondition,
    TaskStatus, ConditionType
)

__all__ = [
    'iPadController',
    'TaskManager',
    'Task',
    'TaskStep', 
    'TaskCondition',
    'TaskStatus',
    'ConditionType'
]