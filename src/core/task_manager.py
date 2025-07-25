#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务管理器模块

负责管理和编排复杂的自动化任务流程。
支持任务调度、条件判断、循环执行和错误处理。
"""

import asyncio
import time
from typing import List, Optional, Dict, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from loguru import logger

from ..models import (
    Action, ActionType, ExecutionResult, ExecutionMode,
    Element, AnalysisResult, TaskError
)
from .controller import iPadController


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 等待执行
    RUNNING = "running"          # 正在执行
    COMPLETED = "completed"      # 执行完成
    FAILED = "failed"            # 执行失败
    CANCELLED = "cancelled"      # 已取消
    PAUSED = "paused"            # 已暂停


class ConditionType(Enum):
    """条件类型枚举"""
    ELEMENT_EXISTS = "element_exists"        # 元素存在
    ELEMENT_NOT_EXISTS = "element_not_exists"  # 元素不存在
    SCREEN_TYPE = "screen_type"              # 屏幕类型
    CUSTOM = "custom"                        # 自定义条件


@dataclass
class TaskCondition:
    """任务条件"""
    type: ConditionType
    target: str
    timeout: float = 10.0
    check_interval: float = 1.0
    custom_checker: Optional[Callable] = None
    description: str = ""


@dataclass
class TaskStep:
    """任务步骤"""
    name: str
    action: Optional[Action] = None
    condition: Optional[TaskCondition] = None
    retry_count: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    stop_on_failure: bool = True
    description: str = ""
    
    # 执行状态
    status: TaskStatus = field(default=TaskStatus.PENDING, init=False)
    start_time: Optional[float] = field(default=None, init=False)
    end_time: Optional[float] = field(default=None, init=False)
    execution_result: Optional[ExecutionResult] = field(default=None, init=False)
    error_message: Optional[str] = field(default=None, init=False)


@dataclass
class Task:
    """自动化任务"""
    name: str
    steps: List[TaskStep]
    description: str = ""
    max_execution_time: float = 300.0  # 最大执行时间（秒）
    
    # 执行状态
    status: TaskStatus = field(default=TaskStatus.PENDING, init=False)
    start_time: Optional[float] = field(default=None, init=False)
    end_time: Optional[float] = field(default=None, init=False)
    current_step_index: int = field(default=0, init=False)
    execution_results: List[ExecutionResult] = field(default_factory=list, init=False)
    error_message: Optional[str] = field(default=None, init=False)


class TaskManager:
    """任务管理器类"""
    
    def __init__(self, controller: iPadController):
        """初始化任务管理器
        
        Args:
            controller: iPad控制器实例
        """
        self.controller = controller
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 全局设置
        self.default_retry_count = 3
        self.default_timeout = 30.0
        self.default_check_interval = 1.0
    
    def create_task(self, name: str, description: str = "") -> Task:
        """创建新任务
        
        Args:
            name: 任务名称
            description: 任务描述
            
        Returns:
            Task: 创建的任务对象
        """
        if name in self.tasks:
            raise TaskError(f"任务已存在: {name}")
        
        task = Task(name=name, steps=[], description=description)
        self.tasks[name] = task
        
        logger.info(f"创建任务: {name}")
        return task
    
    def add_action_step(self, task_name: str, step_name: str, action: Action,
                       retry_count: int = None, timeout: float = None,
                       stop_on_failure: bool = True, description: str = "") -> TaskStep:
        """向任务添加操作步骤
        
        Args:
            task_name: 任务名称
            step_name: 步骤名称
            action: 要执行的操作
            retry_count: 重试次数
            timeout: 超时时间
            stop_on_failure: 失败时是否停止
            description: 步骤描述
            
        Returns:
            TaskStep: 创建的任务步骤
        """
        if task_name not in self.tasks:
            raise TaskError(f"任务不存在: {task_name}")
        
        task = self.tasks[task_name]
        
        step = TaskStep(
            name=step_name,
            action=action,
            retry_count=retry_count or self.default_retry_count,
            timeout=timeout or self.default_timeout,
            stop_on_failure=stop_on_failure,
            description=description
        )
        
        task.steps.append(step)
        logger.debug(f"向任务 {task_name} 添加操作步骤: {step_name}")
        
        return step
    
    def add_condition_step(self, task_name: str, step_name: str, condition: TaskCondition,
                          timeout: float = None, stop_on_failure: bool = True,
                          description: str = "") -> TaskStep:
        """向任务添加条件步骤
        
        Args:
            task_name: 任务名称
            step_name: 步骤名称
            condition: 要检查的条件
            timeout: 超时时间
            stop_on_failure: 失败时是否停止
            description: 步骤描述
            
        Returns:
            TaskStep: 创建的任务步骤
        """
        if task_name not in self.tasks:
            raise TaskError(f"任务不存在: {task_name}")
        
        task = self.tasks[task_name]
        
        step = TaskStep(
            name=step_name,
            condition=condition,
            timeout=timeout or condition.timeout,
            stop_on_failure=stop_on_failure,
            description=description
        )
        
        task.steps.append(step)
        logger.debug(f"向任务 {task_name} 添加条件步骤: {step_name}")
        
        return step
    
    def add_wait_step(self, task_name: str, step_name: str, duration: float,
                     description: str = "") -> TaskStep:
        """向任务添加等待步骤
        
        Args:
            task_name: 任务名称
            step_name: 步骤名称
            duration: 等待时间（秒）
            description: 步骤描述
            
        Returns:
            TaskStep: 创建的任务步骤
        """
        wait_action = Action(
            action_type=ActionType.WAIT,
            parameters={"duration": duration},
            description=description or f"等待 {duration} 秒"
        )
        
        return self.add_action_step(
            task_name, step_name, wait_action,
            retry_count=1, stop_on_failure=False, description=description
        )
    
    def add_tap_element_step(self, task_name: str, step_name: str, element_name: str,
                            use_vlm: bool = False, retry_count: int = None,
                            timeout: float = None, description: str = "") -> TaskStep:
        """向任务添加点击元素步骤
        
        Args:
            task_name: 任务名称
            step_name: 步骤名称
            element_name: 元素名称
            use_vlm: 是否使用VLM识别
            retry_count: 重试次数
            timeout: 超时时间
            description: 步骤描述
            
        Returns:
            TaskStep: 创建的任务步骤
        """
        # 创建自定义操作，包含元素查找和点击逻辑
        action = Action(
            action_type=ActionType.TAP,
            description=description or f"点击元素: {element_name}",
            metadata={"element_name": element_name, "use_vlm": use_vlm}
        )
        
        return self.add_action_step(
            task_name, step_name, action,
            retry_count=retry_count, timeout=timeout, description=description
        )
    
    async def execute_task(self, task_name: str) -> bool:
        """执行指定任务
        
        Args:
            task_name: 任务名称
            
        Returns:
            bool: 执行是否成功
        """
        if task_name not in self.tasks:
            raise TaskError(f"任务不存在: {task_name}")
        
        task = self.tasks[task_name]
        
        if task.status == TaskStatus.RUNNING:
            logger.warning(f"任务 {task_name} 正在执行中")
            return False
        
        # 创建异步任务
        async_task = asyncio.create_task(self._execute_task_impl(task))
        self.running_tasks[task_name] = async_task
        
        try:
            result = await async_task
            return result
        finally:
            # 清理运行中的任务记录
            if task_name in self.running_tasks:
                del self.running_tasks[task_name]
    
    async def _execute_task_impl(self, task: Task) -> bool:
        """任务执行的内部实现"""
        logger.info(f"开始执行任务: {task.name}")
        
        task.status = TaskStatus.RUNNING
        task.start_time = time.time()
        task.current_step_index = 0
        task.execution_results.clear()
        task.error_message = None
        
        try:
            # 执行所有步骤
            for i, step in enumerate(task.steps):
                task.current_step_index = i
                
                logger.info(f"执行步骤 {i+1}/{len(task.steps)}: {step.name}")
                
                # 检查任务是否被取消
                if task.status == TaskStatus.CANCELLED:
                    logger.info(f"任务 {task.name} 已被取消")
                    return False
                
                # 执行步骤
                success = await self._execute_step(step)
                
                if not success and step.stop_on_failure:
                    logger.error(f"步骤 {step.name} 执行失败，停止任务执行")
                    task.status = TaskStatus.FAILED
                    task.error_message = step.error_message
                    return False
                
                # 检查总执行时间
                if time.time() - task.start_time > task.max_execution_time:
                    logger.error(f"任务 {task.name} 执行超时")
                    task.status = TaskStatus.FAILED
                    task.error_message = "任务执行超时"
                    return False
            
            # 所有步骤执行完成
            task.status = TaskStatus.COMPLETED
            logger.info(f"任务 {task.name} 执行完成")
            return True
            
        except Exception as e:
            logger.error(f"任务 {task.name} 执行出错: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            return False
        
        finally:
            task.end_time = time.time()
            execution_time = task.end_time - task.start_time
            logger.info(f"任务 {task.name} 执行耗时: {execution_time:.2f}秒")
    
    async def _execute_step(self, step: TaskStep) -> bool:
        """执行单个步骤"""
        step.status = TaskStatus.RUNNING
        step.start_time = time.time()
        step.error_message = None
        
        try:
            # 根据步骤类型执行
            if step.action:
                success = await self._execute_action_step(step)
            elif step.condition:
                success = await self._execute_condition_step(step)
            else:
                logger.error(f"步骤 {step.name} 没有定义操作或条件")
                success = False
            
            if success:
                step.status = TaskStatus.COMPLETED
                logger.debug(f"步骤 {step.name} 执行成功")
            else:
                step.status = TaskStatus.FAILED
                logger.error(f"步骤 {step.name} 执行失败")
            
            return success
            
        except Exception as e:
            logger.error(f"步骤 {step.name} 执行出错: {e}")
            step.status = TaskStatus.FAILED
            step.error_message = str(e)
            return False
        
        finally:
            step.end_time = time.time()
    
    async def _execute_action_step(self, step: TaskStep) -> bool:
        """执行操作步骤"""
        action = step.action
        
        # 重试逻辑
        for attempt in range(step.retry_count):
            try:
                if attempt > 0:
                    logger.debug(f"步骤 {step.name} 第 {attempt + 1} 次重试")
                    await asyncio.sleep(step.retry_delay)
                
                # 普通操作执行
                if True:
                    # 普通操作执行
                    if action.action_type == ActionType.TAP:
                        result = await self.controller.tap_coordinate(action.position[0], action.position[1], action.description)
                    elif action.action_type == ActionType.SWIPE:
                        target_pos = action.parameters.get("target_position", (0, 0))
                        duration = action.parameters.get("duration", 1.0)
                        result = await self.controller.swipe(
                            action.position[0], action.position[1], target_pos[0], target_pos[1],
                            duration, action.description
                        )
                    elif action.action_type == ActionType.LONG_PRESS:
                        duration = action.parameters.get("duration", 2.0)
                        result = await self.controller.long_press(
                            action.position[0], action.position[1], duration, action.description
                        )
                    elif action.action_type == ActionType.HOME:
                        result = await self.controller.home(action.description)
                    elif action.action_type == ActionType.WAIT:
                        duration = action.parameters.get("duration", 1.0)
                        result = await self.controller.wait(duration, action.description)
                    else:
                        logger.error(f"不支持的操作类型: {action.action_type}")
                        return False
                
                step.execution_result = result
                
                if result.success:
                    return True
                else:
                    step.error_message = result.error_message
                    if attempt == step.retry_count - 1:
                        logger.error(f"步骤 {step.name} 重试 {step.retry_count} 次后仍然失败")
                        return False
                
            except Exception as e:
                step.error_message = str(e)
                if attempt == step.retry_count - 1:
                    logger.error(f"步骤 {step.name} 执行出错: {e}")
                    return False
        
        return False
    
    async def _execute_condition_step(self, step: TaskStep) -> bool:
        """执行条件步骤"""
        condition = step.condition
        start_time = time.time()
        
        while time.time() - start_time < step.timeout:
            try:
                # 根据条件类型检查
                if condition.type == ConditionType.ELEMENT_EXISTS:
                    element = await self.controller.find_element(condition.target)
                    if element:
                        logger.debug(f"条件满足: 元素 {condition.target} 存在")
                        return True
                
                elif condition.type == ConditionType.ELEMENT_NOT_EXISTS:
                    element = await self.controller.find_element(condition.target)
                    if not element:
                        logger.debug(f"条件满足: 元素 {condition.target} 不存在")
                        return True
                
                elif condition.type == ConditionType.SCREEN_TYPE:
                    analysis = await self.controller.analyze_screen()
                    if analysis and analysis.raw_data:
                        screen_type = analysis.raw_data.get('screen_type', 'unknown')
                        if screen_type == condition.target:
                            logger.debug(f"条件满足: 屏幕类型为 {condition.target}")
                            return True
                
                elif condition.type == ConditionType.CUSTOM:
                    if condition.custom_checker:
                        if await condition.custom_checker(self.controller):
                            logger.debug(f"条件满足: 自定义条件 {condition.description}")
                            return True
                
                # 等待下次检查
                await asyncio.sleep(condition.check_interval)
                
            except Exception as e:
                logger.error(f"检查条件时出错: {e}")
                await asyncio.sleep(condition.check_interval)
        
        # 超时
        step.error_message = f"条件检查超时: {condition.description or condition.target}"
        logger.error(step.error_message)
        return False
    
    def cancel_task(self, task_name: str) -> bool:
        """取消任务执行
        
        Args:
            task_name: 任务名称
            
        Returns:
            bool: 取消是否成功
        """
        if task_name not in self.tasks:
            logger.warning(f"任务不存在: {task_name}")
            return False
        
        task = self.tasks[task_name]
        
        if task.status != TaskStatus.RUNNING:
            logger.warning(f"任务 {task_name} 未在运行中")
            return False
        
        # 标记任务为取消状态
        task.status = TaskStatus.CANCELLED
        
        # 取消异步任务
        if task_name in self.running_tasks:
            async_task = self.running_tasks[task_name]
            async_task.cancel()
        
        logger.info(f"任务 {task_name} 已取消")
        return True
    
    def get_task_status(self, task_name: str) -> Optional[TaskStatus]:
        """获取任务状态
        
        Args:
            task_name: 任务名称
            
        Returns:
            TaskStatus: 任务状态，任务不存在时返回None
        """
        if task_name not in self.tasks:
            return None
        
        return self.tasks[task_name].status
    
    def get_task_progress(self, task_name: str) -> Optional[Dict[str, Any]]:
        """获取任务进度信息
        
        Args:
            task_name: 任务名称
            
        Returns:
            Dict: 任务进度信息，任务不存在时返回None
        """
        if task_name not in self.tasks:
            return None
        
        task = self.tasks[task_name]
        
        progress = {
            "name": task.name,
            "status": task.status.value,
            "current_step": task.current_step_index,
            "total_steps": len(task.steps),
            "progress_percentage": (task.current_step_index / len(task.steps)) * 100 if task.steps else 0,
            "start_time": task.start_time,
            "end_time": task.end_time,
            "error_message": task.error_message
        }
        
        if task.start_time:
            if task.end_time:
                progress["execution_time"] = task.end_time - task.start_time
            else:
                progress["execution_time"] = time.time() - task.start_time
        
        return progress
    
    def list_tasks(self) -> List[str]:
        """获取所有任务名称列表
        
        Returns:
            List[str]: 任务名称列表
        """
        return list(self.tasks.keys())
    
    def remove_task(self, task_name: str) -> bool:
        """删除任务
        
        Args:
            task_name: 任务名称
            
        Returns:
            bool: 删除是否成功
        """
        if task_name not in self.tasks:
            logger.warning(f"任务不存在: {task_name}")
            return False
        
        task = self.tasks[task_name]
        
        # 如果任务正在运行，先取消
        if task.status == TaskStatus.RUNNING:
            self.cancel_task(task_name)
        
        # 删除任务
        del self.tasks[task_name]
        
        logger.info(f"任务 {task_name} 已删除")
        return True
    
    def create_element_exists_condition(self, element_name: str, timeout: float = 10.0,
                                       check_interval: float = 1.0) -> TaskCondition:
        """创建元素存在条件
        
        Args:
            element_name: 元素名称
            timeout: 超时时间
            check_interval: 检查间隔
            
        Returns:
            TaskCondition: 条件对象
        """
        return TaskCondition(
            type=ConditionType.ELEMENT_EXISTS,
            target=element_name,
            timeout=timeout,
            check_interval=check_interval,
            description=f"等待元素 {element_name} 出现"
        )
    
    def create_screen_type_condition(self, screen_type: str, timeout: float = 10.0,
                                    check_interval: float = 1.0) -> TaskCondition:
        """创建屏幕类型条件
        
        Args:
            screen_type: 屏幕类型
            timeout: 超时时间
            check_interval: 检查间隔
            
        Returns:
            TaskCondition: 条件对象
        """
        return TaskCondition(
            type=ConditionType.SCREEN_TYPE,
            target=screen_type,
            timeout=timeout,
            check_interval=check_interval,
            description=f"等待屏幕类型变为 {screen_type}"
        )