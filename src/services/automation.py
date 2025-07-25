#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
iOS自动化执行服务模块

提供优雅高效的iOS设备控制接口，支持多种执行模式。
支持WebDriverAgent、pymobiledevice3等多种控制方式。
"""

import time
import asyncio
from typing import List, Optional, Dict, Any, Tuple, Union
from abc import ABC, abstractmethod
from loguru import logger

from ..models import (
    Action, ActionType, ActionSuggestion, ExecutionResult, ExecutionMode,
    Element, DeviceInfo, ActionError, WebDriverError
)


class AutomationBackend(ABC):
    """自动化后端抽象基类"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接设备"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def tap(self, x: int, y: int) -> bool:
        """点击指定坐标"""
        pass
    
    @abstractmethod
    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0) -> bool:
        """滑动操作"""
        pass
    
    @abstractmethod
    async def long_press(self, x: int, y: int, duration: float = 2.0) -> bool:
        """长按操作"""
        pass
    
    @abstractmethod
    async def home(self) -> bool:
        """按Home键"""
        pass
    
    @abstractmethod
    async def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        pass


class WebDriverBackend(AutomationBackend):
    """WebDriverAgent后端实现"""
    
    def __init__(self, device_udid: str, wda_port: int = 8100):
        self.device_udid = device_udid
        self.wda_port = wda_port
        self.client = None
        self.session = None
    
    async def connect(self) -> bool:
        """连接WebDriverAgent"""
        try:
            # 动态导入wda，避免在没有安装时报错
            import wda
            
            # 连接设备
            self.client = wda.Client(f"http://localhost:{self.wda_port}")
            
            # 创建会话
            self.session = self.client.session()
            
            # 测试连接
            screen_size = await self.get_screen_size()
            logger.info(f"WebDriverAgent连接成功，屏幕尺寸: {screen_size}")
            return True
            
        except Exception as e:
            logger.error(f"WebDriverAgent连接失败: {e}")
            raise WebDriverError(f"连接失败: {e}")
    
    async def disconnect(self) -> None:
        """断开WebDriverAgent连接"""
        try:
            if self.session:
                self.session.close()
            self.session = None
            self.client = None
            logger.info("WebDriverAgent连接已断开")
        except Exception as e:
            logger.warning(f"断开WebDriverAgent连接时出错: {e}")
    
    async def tap(self, x: int, y: int) -> bool:
        """点击指定坐标"""
        try:
            if not self.session:
                raise WebDriverError("WebDriverAgent未连接")
            
            self.session.tap(x, y)
            logger.debug(f"点击坐标: ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"点击操作失败: {e}")
            return False
    
    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0) -> bool:
        """滑动操作"""
        try:
            if not self.session:
                raise WebDriverError("WebDriverAgent未连接")
            
            self.session.swipe(start_x, start_y, end_x, end_y, duration)
            logger.debug(f"滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y}), 持续时间: {duration}s")
            return True
            
        except Exception as e:
            logger.error(f"滑动操作失败: {e}")
            return False
    
    async def long_press(self, x: int, y: int, duration: float = 2.0) -> bool:
        """长按操作"""
        try:
            if not self.session:
                raise WebDriverError("WebDriverAgent未连接")
            
            # WebDriverAgent的长按实现
            self.session.tap_hold(x, y, duration)
            logger.debug(f"长按坐标: ({x}, {y}), 持续时间: {duration}s")
            return True
            
        except Exception as e:
            logger.error(f"长按操作失败: {e}")
            return False
    
    async def home(self) -> bool:
        """按Home键"""
        try:
            if not self.session:
                raise WebDriverError("WebDriverAgent未连接")
            
            self.session.home()
            logger.debug("按下Home键")
            return True
            
        except Exception as e:
            logger.error(f"Home键操作失败: {e}")
            return False
    
    async def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        try:
            if not self.session:
                raise WebDriverError("WebDriverAgent未连接")
            
            window_size = self.session.window_size()
            return (window_size.width, window_size.height)
            
        except Exception as e:
            logger.error(f"获取屏幕尺寸失败: {e}")
            raise WebDriverError(f"获取屏幕尺寸失败: {e}")


class PyMobileDeviceBackend(AutomationBackend):
    """pymobiledevice3后端实现（预留接口）"""
    
    def __init__(self, device_udid: str):
        self.device_udid = device_udid
        self.device = None
    
    async def connect(self) -> bool:
        """连接pymobiledevice3"""
        try:
            # TODO: 实现pymobiledevice3连接逻辑
            logger.warning("pymobiledevice3后端尚未实现")
            return False
        except Exception as e:
            logger.error(f"pymobiledevice3连接失败: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    async def tap(self, x: int, y: int) -> bool:
        """点击操作"""
        # TODO: 实现pymobiledevice3点击逻辑
        logger.warning("pymobiledevice3点击操作尚未实现")
        return False
    
    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0) -> bool:
        """滑动操作"""
        # TODO: 实现pymobiledevice3滑动逻辑
        logger.warning("pymobiledevice3滑动操作尚未实现")
        return False
    
    async def long_press(self, x: int, y: int, duration: float = 2.0) -> bool:
        """长按操作"""
        # TODO: 实现pymobiledevice3长按逻辑
        logger.warning("pymobiledevice3长按操作尚未实现")
        return False
    
    async def home(self) -> bool:
        """按Home键"""
        # TODO: 实现pymobiledevice3 Home键逻辑
        logger.warning("pymobiledevice3 Home键操作尚未实现")
        return False
    
    async def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        # TODO: 实现pymobiledevice3屏幕尺寸获取逻辑
        logger.warning("pymobiledevice3屏幕尺寸获取尚未实现")
        return (0, 0)


class AutomationService:
    """自动化执行服务类"""
    
    def __init__(self, device_udid: str, execution_mode: ExecutionMode = ExecutionMode.AUTO):
        """初始化自动化服务
        
        Args:
            device_udid: 设备UDID
            execution_mode: 执行模式
        """
        self.device_udid = device_udid
        self.execution_mode = execution_mode
        self.backend: Optional[AutomationBackend] = None
        self.backend_type = "webdriver"  # 默认使用WebDriverAgent
        
        # 操作历史记录
        self.action_history: List[Action] = []
        
        # 性能统计
        self.stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "average_execution_time": 0.0
        }
    
    def set_backend(self, backend_type: str, **kwargs) -> None:
        """设置自动化后端
        
        Args:
            backend_type: 后端类型 ('webdriver', 'pymobiledevice')
            **kwargs: 后端特定参数
        """
        self.backend_type = backend_type
        
        if backend_type == "webdriver":
            wda_port = kwargs.get("wda_port", 8100)
            self.backend = WebDriverBackend(self.device_udid, wda_port)
        elif backend_type == "pymobiledevice":
            self.backend = PyMobileDeviceBackend(self.device_udid)
        else:
            raise AutomationError(f"不支持的后端类型: {backend_type}")
        
        logger.info(f"已设置自动化后端: {backend_type}")
    
    async def connect(self) -> bool:
        """连接设备"""
        if not self.backend:
            self.set_backend(self.backend_type)
        
        try:
            success = await self.backend.connect()
            if success:
                logger.info(f"设备连接成功: {self.device_udid}")
            return success
        except Exception as e:
            logger.error(f"设备连接失败: {e}")
            raise AutomationError(f"设备连接失败: {e}")
    
    async def disconnect(self) -> None:
        """断开设备连接"""
        if self.backend:
            await self.backend.disconnect()
            logger.info(f"设备连接已断开: {self.device_udid}")
    
    async def execute_action(self, action: Action) -> ExecutionResult:
        """执行单个操作
        
        Args:
            action: 要执行的操作
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        
        try:
            # 记录操作
            self.action_history.append(action)
            self.stats["total_actions"] += 1
            
            # 根据执行模式处理
            if self.execution_mode == ExecutionMode.SUGGEST_ONLY:
                # 仅建议模式，不实际执行
                suggestion = self._generate_suggestion(action)
                logger.info(f"操作建议: {suggestion.description}")
                
                result = ExecutionResult(
                success=True,
                action=action,
                execution_time=time.time() - start_time
            )
            else:
                # 实际执行模式
                success = await self._execute_action_impl(action)
                
                if success:
                    self.stats["successful_actions"] += 1
                else:
                    self.stats["failed_actions"] += 1
                
                result = ExecutionResult(
                success=success,
                action=action,
                execution_time=time.time() - start_time
            )
            
            # 更新平均执行时间
            self._update_average_execution_time(result.execution_time)
            
            return result
            
        except Exception as e:
            logger.error(f"执行操作失败: {e}")
            self.stats["failed_actions"] += 1
            
            return ExecutionResult(
            success=False,
            action=action,
            execution_time=time.time() - start_time,
            error_message=str(e)
        )
    
    async def execute_actions(self, actions: List[Action]) -> List[ExecutionResult]:
        """批量执行操作
        
        Args:
            actions: 操作列表
            
        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        results = []
        
        for i, action in enumerate(actions):
            logger.info(f"执行操作 {i+1}/{len(actions)}: {action.type.value}")
            
            result = await self.execute_action(action)
            results.append(result)
            
            # 如果操作失败且设置了停止标志，则停止执行
            if not result.success and action.stop_on_failure:
                logger.warning(f"操作失败，停止执行后续操作: {result.error}")
                break
            
            # 操作间延迟
            if action.delay_after > 0:
                await asyncio.sleep(action.delay_after)
        
        logger.info(f"批量操作完成，成功: {sum(1 for r in results if r.success)}/{len(results)}")
        return results
    
    async def _execute_action_impl(self, action: Action) -> bool:
        """实际执行操作的内部实现"""
        if not self.backend:
            raise AutomationError("自动化后端未初始化")
        
        try:
            if action.action_type == ActionType.TAP:
                return await self.backend.tap(action.position[0], action.position[1])
            
            elif action.action_type == ActionType.SWIPE:
                target_pos = action.parameters.get("target_position", (0, 0))
                duration = action.parameters.get("duration", 1.0)
                return await self.backend.swipe(
                    action.position[0], action.position[1],
                    target_pos[0], target_pos[1],
                    duration
                )
            
            elif action.action_type == ActionType.LONG_PRESS:
                duration = action.parameters.get("duration", 2.0)
                return await self.backend.long_press(action.position[0], action.position[1], duration)
            
            elif action.action_type == ActionType.HOME:
                return await self.backend.home()
            
            elif action.action_type == ActionType.WAIT:
                duration = action.parameters.get("duration", 1.0)
                await asyncio.sleep(duration)
                return True
            
            else:
                logger.warning(f"不支持的操作类型: {action.action_type}")
                return False
                
        except Exception as e:
            logger.error(f"执行操作时出错: {e}")
            return False
    
    def _generate_suggestion(self, action: Action) -> ActionSuggestion:
        """生成操作建议"""
        descriptions = {
            ActionType.TAP: f"点击坐标 ({action.position[0]}, {action.position[1]})" if action.position else "点击操作",
            ActionType.SWIPE: f"从 ({action.position[0]}, {action.position[1]}) 滑动到 ({action.parameters.get('target_position', (0, 0))[0]}, {action.parameters.get('target_position', (0, 0))[1]})" if action.position and action.parameters.get('target_position') else "滑动操作",
            ActionType.LONG_PRESS: f"长按坐标 ({action.position[0]}, {action.position[1]}) {action.parameters.get('duration', 2.0)}秒" if action.position else f"长按操作 {action.parameters.get('duration', 2.0)}秒",
            ActionType.HOME: "按下Home键",
            ActionType.WAIT: f"等待 {action.parameters.get('duration', 1.0)} 秒"
        }
        
        description = descriptions.get(action.action_type, f"执行 {action.action_type.value} 操作")
        
        return ActionSuggestion(
            action_type=action.action_type,
            description=description,
            coordinates=action.position if action.position else None,
            confidence=1.0,
            reason=action.description or "用户指定操作"
        )
    
    def _update_average_execution_time(self, execution_time: float) -> None:
        """更新平均执行时间"""
        total_actions = self.stats["total_actions"]
        current_avg = self.stats["average_execution_time"]
        
        # 计算新的平均值
        new_avg = ((current_avg * (total_actions - 1)) + execution_time) / total_actions
        self.stats["average_execution_time"] = new_avg
    
    def set_execution_mode(self, mode: ExecutionMode) -> None:
        """设置执行模式
        
        Args:
            mode: 执行模式
        """
        self.execution_mode = mode
        logger.info(f"执行模式已设置为: {mode.value}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            Dict: 统计信息
        """
        return self.stats.copy()
    
    def get_action_history(self, limit: Optional[int] = None) -> List[Action]:
        """获取操作历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            List[Action]: 操作历史记录
        """
        if limit:
            return self.action_history[-limit:]
        return self.action_history.copy()
    
    def clear_history(self) -> None:
        """清空操作历史记录"""
        self.action_history.clear()
        logger.info("操作历史记录已清空")
    
    async def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸
        
        Returns:
            Tuple[int, int]: (宽度, 高度)
        """
        if not self.backend:
            raise AutomationError("自动化后端未初始化")
        
        return await self.backend.get_screen_size()
    
    def create_tap_action(self, x: int, y: int, description: str = "") -> Action:
        """创建点击操作
        
        Args:
            x, y: 点击坐标
            description: 操作描述
            
        Returns:
            Action: 点击操作对象
        """
        return Action(
            action_type=ActionType.TAP,
            position=(x, y),
            description=description or f"点击 ({x}, {y})"
        )
    
    def create_swipe_action(self, start_x: int, start_y: int, end_x: int, end_y: int,
                           duration: float = 1.0, description: str = "") -> Action:
        """创建滑动操作
        
        Args:
            start_x, start_y: 起始坐标
            end_x, end_y: 结束坐标
            duration: 滑动持续时间
            description: 操作描述
            
        Returns:
            Action: 滑动操作对象
        """
        return Action(
            action_type=ActionType.SWIPE,
            position=(start_x, start_y),
            parameters={"target_position": (end_x, end_y), "duration": duration},
            description=description or f"滑动 ({start_x}, {start_y}) -> ({end_x}, {end_y})"
        )
    
    def create_long_press_action(self, x: int, y: int, duration: float = 2.0,
                                description: str = "") -> Action:
        """创建长按操作
        
        Args:
            x, y: 长按坐标
            duration: 长按持续时间
            description: 操作描述
            
        Returns:
            Action: 长按操作对象
        """
        return Action(
            action_type=ActionType.LONG_PRESS,
            position=(x, y),
            parameters={"duration": duration},
            description=description or f"长按 ({x}, {y}) {duration}秒"
        )
    
    def create_home_action(self, description: str = "") -> Action:
        """创建Home键操作
        
        Args:
            description: 操作描述
            
        Returns:
            Action: Home键操作对象
        """
        return Action(
            action_type=ActionType.HOME,
            description=description or "按下Home键"
        )
    
    def create_wait_action(self, duration: float, description: str = "") -> Action:
        """创建等待操作
        
        Args:
            duration: 等待时间（秒）
            description: 操作描述
            
        Returns:
            Action: 等待操作对象
        """
        return Action(
            action_type=ActionType.WAIT,
            parameters={"duration": duration},
            description=description or f"等待 {duration} 秒"
        )