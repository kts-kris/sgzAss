#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主控制器模块

整合连接、视觉识别和自动化执行服务，提供统一的iPad自动化控制接口。
实现高级业务逻辑和任务编排。
"""

import asyncio
import time
from typing import List, Optional, Dict, Any, Tuple, Union
from pathlib import Path
from loguru import logger

from ..models import (
    ExecutionMode, ActionType, Element, Action, ActionSuggestion,
    ExecutionResult, AnalysisResult, DeviceInfo, TaskConfig,
    SystemStatus, ConnectionStatus, iPadAutomationError
)
from ..services import ConnectionService, VisionService, AutomationService


class iPadController:
    """iPad自动化控制器主类"""
    
    def __init__(self, device_udid: Optional[str] = None, 
                 template_dir: str = "templates",
                 execution_mode: ExecutionMode = ExecutionMode.AUTO):
        """初始化iPad控制器
        
        Args:
            device_udid: 设备UDID，如果为None则自动检测
            template_dir: 模板目录路径
            execution_mode: 执行模式
        """
        self.device_udid = device_udid
        self.execution_mode = execution_mode
        
        # 初始化服务
        self.connection_service = ConnectionService()
        self.vision_service = VisionService(template_dir)
        self.automation_service = None  # 延迟初始化
        
        # 系统状态
        self.status = SystemStatus(
            connection_status=ConnectionStatus.DISCONNECTED,
            device_info=None,
            last_screenshot_time=None,
            last_action_time=None
        )
        
        # 任务配置
        self.task_config = TaskConfig(
            name="default_task",
            description="默认任务配置"
        )
        
        # 性能统计
        self.performance_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_response_time": 0.0,
            "last_operation_time": None
        }
    
    async def initialize(self) -> bool:
        """初始化控制器，建立设备连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("正在初始化iPad控制器...")
            
            # 连接设备
            success = await self.connect_device()
            if not success:
                logger.error("设备连接失败")
                return False
            
            # 初始化自动化服务
            if not self.device_udid:
                logger.error("设备UDID未获取")
                return False
            
            self.automation_service = AutomationService(
                device_udid=self.device_udid,
                execution_mode=self.execution_mode
            )
            
            # 连接自动化后端
            await self.automation_service.connect()
            
            logger.info("iPad控制器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            self.status.connection_status = ConnectionStatus.ERROR
            return False
    
    async def connect_device(self) -> bool:
        """连接iPad设备
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("正在连接iPad设备...")
            
            # 连接设备
            success = self.connection_service.connect()
            device_info = self.connection_service.device_info if success else None
            
            if device_info:
                self.device_udid = device_info.udid
                self.status.device_info = device_info
                self.status.connection_status = ConnectionStatus.CONNECTED
                
                logger.info(f"设备连接成功: {device_info.name} ({device_info.udid})")
                return True
            else:
                self.status.connection_status = ConnectionStatus.DISCONNECTED
                logger.error("设备连接失败")
                return False
                
        except Exception as e:
            logger.error(f"连接设备时出错: {e}")
            self.status.connection_status = ConnectionStatus.ERROR
            return False
    
    async def disconnect_device(self) -> None:
        """断开设备连接"""
        try:
            logger.info("正在断开设备连接...")
            
            # 断开自动化服务
            if self.automation_service:
                await self.automation_service.disconnect()
            
            # 断开连接服务
            self.connection_service.disconnect()
            
            self.status.connection_status = ConnectionStatus.DISCONNECTED
            self.status.device_info = None
            
            logger.info("设备连接已断开")
            
        except Exception as e:
            logger.warning(f"断开连接时出错: {e}")
    
    def connect(self) -> bool:
        """同步版本的连接方法
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 运行异步连接方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.connect_device())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"同步连接失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """同步版本的断开连接方法"""
        try:
            # 运行异步断开连接方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.disconnect_device())
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"同步断开连接失败: {e}")
    
    async def take_screenshot(self) -> Optional[Any]:
        """获取设备截图
        
        Returns:
            numpy.ndarray: 截图图像，失败时返回None
        """
        try:
            if self.status.connection_status != ConnectionStatus.CONNECTED:
                raise iPadAutomationError("设备未连接")
            
            screenshot = self.connection_service.get_screenshot()
            
            if screenshot is not None:
                self.status.last_screenshot_time = time.time()
                logger.debug("截图获取成功")
            
            return screenshot
            
        except Exception as e:
            logger.error(f"获取截图失败: {e}")
            return None
    
    async def analyze_screen(self, use_vlm: bool = False) -> Optional[AnalysisResult]:
        """分析当前屏幕内容
        
        Args:
            use_vlm: 是否使用VLM进行分析
            
        Returns:
            AnalysisResult: 分析结果，失败时返回None
        """
        try:
            # 获取截图
            screenshot = await self.take_screenshot()
            if screenshot is None:
                logger.error("无法获取截图进行分析")
                return None
            
            # 分析屏幕
            analysis_result = self.vision_service.analyze_screen(screenshot, use_vlm=use_vlm)
            
            # 从raw_data中获取screen_type
            screen_type = analysis_result.raw_data.get('screen_type', 'unknown') if analysis_result.raw_data else 'unknown'
            logger.info(f"屏幕分析完成: {screen_type}, 找到 {len(analysis_result.elements)} 个元素")
            return analysis_result
            
        except Exception as e:
            logger.error(f"屏幕分析失败: {e}")
            return None
    
    async def find_element(self, element_name: str, use_vlm: bool = False) -> Optional[Element]:
        """在当前屏幕中查找指定元素
        
        Args:
            element_name: 元素名称
            use_vlm: 是否使用VLM进行识别
            
        Returns:
            Element: 找到的元素，未找到时返回None
        """
        try:
            # 获取截图
            screenshot = await self.take_screenshot()
            if screenshot is None:
                logger.error("无法获取截图进行元素查找")
                return None
            
            # 查找元素
            match_result = self.vision_service.find_element(screenshot, element_name, use_vlm=use_vlm)
            
            if match_result:
                element = Element(
                    type=self._infer_element_type(element_name),
                    name=element_name,
                    x=match_result.x,
                    y=match_result.y,
                    width=match_result.width,
                    height=match_result.height,
                    confidence=match_result.confidence
                )
                
                logger.debug(f"找到元素: {element_name} at ({element.x}, {element.y})")
                return element
            else:
                logger.debug(f"未找到元素: {element_name}")
                return None
                
        except Exception as e:
            logger.error(f"查找元素失败: {e}")
            return None
    
    async def tap_element(self, element_name: str, use_vlm: bool = False) -> ExecutionResult:
        """点击指定元素
        
        Args:
            element_name: 元素名称
            use_vlm: 是否使用VLM进行识别
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            # 查找元素
            element = await self.find_element(element_name, use_vlm=use_vlm)
            
            if not element:
                return ExecutionResult(
                success=False,
                action=None,
                execution_time=0.0,
                error_message=f"未找到元素: {element_name}"
            )
            
            # 计算点击坐标（元素中心）
            click_x = element.x + element.width // 2
            click_y = element.y + element.height // 2
            
            # 创建点击操作
            action = self.automation_service.create_tap_action(
                click_x, click_y, f"点击元素: {element_name}"
            )
            
            # 执行操作
            result = await self.automation_service.execute_action(action)
            
            # 更新统计
            self._update_performance_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"点击元素失败: {e}")
            return ExecutionResult(
            success=False,
            action=None,
            execution_time=0.0,
            error_message=str(e)
        )
    
    async def tap_coordinate(self, x: int, y: int, description: str = "") -> ExecutionResult:
        """点击指定坐标
        
        Args:
            x, y: 点击坐标
            description: 操作描述
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            if not self.automation_service:
                raise iPadAutomationError("自动化服务未初始化")
            
            # 创建点击操作
            action = self.automation_service.create_tap_action(x, y, description)
            
            # 执行操作
            result = await self.automation_service.execute_action(action)
            
            # 更新统计
            self._update_performance_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"点击坐标失败: {e}")
            return ExecutionResult(
            success=False,
            action=None,
            execution_time=0.0,
            error_message=str(e)
        )
    
    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
                   duration: float = 1.0, description: str = "") -> ExecutionResult:
        """执行滑动操作
        
        Args:
            start_x, start_y: 起始坐标
            end_x, end_y: 结束坐标
            duration: 滑动持续时间
            description: 操作描述
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            if not self.automation_service:
                raise iPadAutomationError("自动化服务未初始化")
            
            # 创建滑动操作
            action = self.automation_service.create_swipe_action(
                start_x, start_y, end_x, end_y, duration, description
            )
            
            # 执行操作
            result = await self.automation_service.execute_action(action)
            
            # 更新统计
            self._update_performance_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"滑动操作失败: {e}")
            return ExecutionResult(
            success=False,
            action=None,
            execution_time=0.0,
            error_message=str(e)
        )
    
    async def long_press(self, x: int, y: int, duration: float = 2.0,
                        description: str = "") -> ExecutionResult:
        """执行长按操作
        
        Args:
            x, y: 长按坐标
            duration: 长按持续时间
            description: 操作描述
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            if not self.automation_service:
                raise iPadAutomationError("自动化服务未初始化")
            
            # 创建长按操作
            action = self.automation_service.create_long_press_action(x, y, duration, description)
            
            # 执行操作
            result = await self.automation_service.execute_action(action)
            
            # 更新统计
            self._update_performance_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"长按操作失败: {e}")
            return ExecutionResult(
            success=False,
            action=None,
            execution_time=0.0,
            error_message=str(e)
        )
    
    async def home(self, description: str = "") -> ExecutionResult:
        """按下Home键
        
        Args:
            description: 操作描述
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            if not self.automation_service:
                raise iPadAutomationError("自动化服务未初始化")
            
            # 创建Home键操作
            action = self.automation_service.create_home_action(description)
            
            # 执行操作
            result = await self.automation_service.execute_action(action)
            
            # 更新统计
            self._update_performance_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Home键操作失败: {e}")
            return ExecutionResult(
            success=False,
            action=None,
            execution_time=0.0,
            error_message=str(e)
        )
    
    async def wait(self, duration: float, description: str = "") -> ExecutionResult:
        """等待指定时间
        
        Args:
            duration: 等待时间（秒）
            description: 操作描述
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            if not self.automation_service:
                raise iPadAutomationError("自动化服务未初始化")
            
            # 创建等待操作
            action = self.automation_service.create_wait_action(duration, description)
            
            # 执行操作
            result = await self.automation_service.execute_action(action)
            
            # 更新统计
            self._update_performance_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"等待操作失败: {e}")
            return ExecutionResult(
            success=False,
            action=None,
            execution_time=0.0,
            error_message=str(e)
        )
    
    async def execute_task_sequence(self, actions: List[Action]) -> List[ExecutionResult]:
        """执行任务序列
        
        Args:
            actions: 操作序列
            
        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        try:
            if not self.automation_service:
                raise iPadAutomationError("自动化服务未初始化")
            
            logger.info(f"开始执行任务序列，共 {len(actions)} 个操作")
            
            # 执行操作序列
            results = await self.automation_service.execute_actions(actions)
            
            # 更新统计
            for result in results:
                self._update_performance_stats(result)
            
            # 统计结果
            successful = sum(1 for r in results if r.success)
            logger.info(f"任务序列执行完成，成功: {successful}/{len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"执行任务序列失败: {e}")
            return []
    
    def set_execution_mode(self, mode: ExecutionMode) -> None:
        """设置执行模式
        
        Args:
            mode: 执行模式
        """
        self.execution_mode = mode
        self.status.execution_mode = mode
        
        if self.automation_service:
            self.automation_service.set_execution_mode(mode)
        
        logger.info(f"执行模式已设置为: {mode.value}")
    
    def set_automation_backend(self, backend_type: str, **kwargs) -> None:
        """设置自动化后端
        
        Args:
            backend_type: 后端类型
            **kwargs: 后端特定参数
        """
        if self.automation_service:
            self.automation_service.set_backend(backend_type, **kwargs)
            self.status.automation_backend = backend_type
            logger.info(f"自动化后端已设置为: {backend_type}")
    
    def enable_vlm(self, vlm_client: Any) -> None:
        """启用VLM大模型识别
        
        Args:
            vlm_client: VLM客户端实例
        """
        self.vision_service.enable_vlm(vlm_client)
        logger.info("VLM大模型识别已启用")
    
    def disable_vlm(self) -> None:
        """禁用VLM大模型识别"""
        self.vision_service.disable_vlm()
        logger.info("VLM大模型识别已禁用")
    
    def get_system_status(self) -> SystemStatus:
        """获取系统状态
        
        Returns:
            SystemStatus: 当前系统状态
        """
        return self.status
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            Dict: 性能统计信息
        """
        stats = self.performance_stats.copy()
        
        # 添加自动化服务统计
        if self.automation_service:
            automation_stats = self.automation_service.get_stats()
            stats.update({
                "automation_stats": automation_stats
            })
        
        return stats
    
    def _infer_element_type(self, element_name: str) -> str:
        """根据元素名称推断元素类型"""
        if "button" in element_name.lower():
            return "button"
        elif "menu" in element_name.lower():
            return "ui"
        elif "land" in element_name.lower() or "resource" in element_name.lower():
            return "interactive"
        else:
            return "unknown"
    
    def _update_performance_stats(self, result: ExecutionResult) -> None:
        """更新性能统计信息"""
        self.performance_stats["total_operations"] += 1
        
        if result.success:
            self.performance_stats["successful_operations"] += 1
        else:
            self.performance_stats["failed_operations"] += 1
        
        # 更新平均响应时间
        total_ops = self.performance_stats["total_operations"]
        current_avg = self.performance_stats["average_response_time"]
        new_avg = ((current_avg * (total_ops - 1)) + result.execution_time) / total_ops
        self.performance_stats["average_response_time"] = new_avg
        
        self.performance_stats["last_operation_time"] = time.time()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect_device()