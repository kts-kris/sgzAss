#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
《三国志战略版》游戏助手控制器

整合截图、VLM分析、异步处理等功能，为用户提供智能游戏建议。
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger
import cv2

from ..models import AnalysisResult, ActionSuggestion, Element
from ..models import ConfigurationError, VisionError, ActionError
from ..services.vision import VisionService
from ..services.automation import AutomationBackend
from ..services.ollama_vlm import OllamaVLMService
from ..services.async_analysis_manager import AsyncAnalysisManager
from ..services.template_matcher import TemplateMatcher
from ..utils.config import get_config, get_config_manager
from ..utils.screenshot import ScreenshotManager


class GameAssistant:
    """《三国志战略版》游戏助手主控制器"""
    
    def __init__(self, automation_backend: Optional[AutomationBackend] = None):
        """初始化游戏助手
        
        Args:
            automation_backend: 自动化后端实例
        """
        self.config = get_config()
        self.config_manager = get_config_manager()
        self.automation_backend = automation_backend
        
        # 初始化服务
        self.vision_service = VisionService()
        self.ollama_service = None
        self.async_manager = None
        self.screenshot_manager = None
        self.template_matcher = None
        
        # 添加ollama_vlm属性引用
        self.ollama_vlm = None
        
        # 状态管理
        self.is_running = False
        self.last_analysis_time = 0
        self.analysis_count = 0
        
        # 初始化组件
        self._initialize_services()
    
    def _initialize_services(self):
        """初始化各种服务"""
        try:
            # 初始化Ollama VLM服务
            if (self.config.vision.vlm_enabled and 
                self.config.vision.vlm_provider == 'ollama'):
                # 使用配置文件中的模型参数
                ollama_config = self.config.vision.ollama_config
                self.ollama_service = OllamaVLMService(
                    host=ollama_config.host,
                    port=ollama_config.port,
                    model=ollama_config.model,
                    timeout=ollama_config.timeout,
                    image_max_size=ollama_config.image_max_size,
                    image_quality=ollama_config.image_quality
                )
                # 异步初始化VLM服务
                asyncio.create_task(self._initialize_vlm_service())
                self.vision_service.enable_vlm(self.ollama_service)
                logger.info(f"Ollama VLM服务已启用，模型: {ollama_config.model}")
            
            # 初始化连接服务（所有服务共享同一个实例）
            from ..services.connection import ConnectionService
            self.connection_service = ConnectionService()
            # 尝试连接设备
            try:
                if self.connection_service.connect():
                    logger.info("设备连接成功")
                else:
                    logger.warning("设备连接失败，截图功能可能不可用")
            except Exception as e:
                logger.warning(f"设备连接异常: {e}，截图功能可能不可用")
            
            # 初始化截图管理器
            self.screenshot_manager = ScreenshotManager(self.connection_service)
            logger.info("截图管理器已初始化")
            
            # 初始化异步分析管理器
            if self.config.async_analysis.enabled:
                self.async_manager = AsyncAnalysisManager(
                    config_manager=self.config_manager,
                    connection_service=self.connection_service  # 使用同一个连接服务实例
                )
                logger.info("异步分析管理器已启用")
            
            # 初始化模板匹配器
            if self.config.vision.template_matching.get("enabled", False):
                self.template_matcher = TemplateMatcher(
                    template_dir=self.config.vision.template_matching.get("template_dir", "templates")
                )
                logger.info("模板匹配器已启用")
            
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            raise ConfigurationError(f"服务初始化失败: {e}")
    
    async def _initialize_vlm_service(self):
        """异步初始化VLM服务"""
        try:
            if self.ollama_service:
                success = await self.ollama_service.initialize()
                if success:
                    logger.info("VLM服务异步初始化成功")
                else:
                    logger.warning("VLM服务异步初始化失败，将使用模板匹配")
        except Exception as e:
            logger.warning(f"VLM服务异步初始化异常: {e}，将使用模板匹配")
    
    async def start(self):
        """启动游戏助手（别名方法）"""
        await self.start_assistant()
    
    async def stop(self):
        """停止游戏助手（别名方法）"""
        await self.stop_assistant()
    
    async def start_assistant(self):
        """启动游戏助手"""
        if self.is_running:
            logger.warning("游戏助手已在运行中")
            return
        
        self.is_running = True
        logger.info("🎮 《三国志战略版》游戏助手已启动")
        
        try:
            # 启动Ollama VLM服务
            if self.ollama_service:
                await self.ollama_service.start()
                self.ollama_vlm = self.ollama_service
                logger.info("Ollama VLM服务已启动")
            elif not hasattr(self, 'ollama_vlm') or self.ollama_vlm is None:
                # 如果没有ollama_service，创建一个默认的
                from src.services.ollama_vlm import OllamaVLMService
                from src.utils.config import get_config
                config = get_config()
                ollama_config = config.vision.ollama_config
                self.ollama_vlm = OllamaVLMService(
                    host=ollama_config.host,
                    port=ollama_config.port,
                    model=ollama_config.model,
                    timeout=ollama_config.timeout,
                    image_max_size=ollama_config.image_max_size,
                    image_quality=ollama_config.image_quality
                )
                await self.ollama_vlm.start()
                logger.info("默认Ollama VLM服务已启动")
            
            # 启动异步分析管理器
            if self.async_manager:
                await self.async_manager.start()
            
            # 如果启用了自动分析，开始自动分析循环
            if (self.config.async_analysis.enabled and 
                self.config.async_analysis.auto_analysis_enabled):
                asyncio.create_task(self._auto_analysis_loop())
            
            logger.info("✅ 游戏助手启动完成，等待用户操作")
            
        except Exception as e:
            logger.error(f"启动游戏助手失败: {e}")
            self.is_running = False
            raise
    
    async def stop_assistant(self):
        """停止游戏助手"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("🛑 正在停止游戏助手...")
        
        try:
            # 停止异步分析管理器
            if self.async_manager:
                await self.async_manager.stop()
            
            # 停止Ollama VLM服务
            if self.ollama_service:
                await self.ollama_service.stop()
                logger.info("Ollama VLM服务已停止")
            elif self.ollama_vlm:
                await self.ollama_vlm.stop()
                logger.info("Ollama VLM服务已停止")
            
            # 断开设备连接
            if hasattr(self, 'connection_service') and self.connection_service:
                self.connection_service.disconnect()
                logger.info("设备连接已断开")
            
            logger.info("✅ 游戏助手已停止")
            
        except Exception as e:
            logger.error(f"停止游戏助手时出错: {e}")
    
    async def analyze_current_screen(self, save_screenshot: bool = True) -> Optional[AnalysisResult]:
        """分析当前屏幕
        
        Args:
            save_screenshot: 是否保存截图
            
        Returns:
            AnalysisResult: 分析结果
        """
        if not self.screenshot_manager:
            logger.error("截图管理器未初始化")
            return None
        
        try:
            # 获取截图
            screenshot = await self.screenshot_manager.take_screenshot()
            if screenshot is None:
                logger.error("获取截图失败")
                return None
            
            # 保存分析截图（如果启用且未启用自动保存）
            if save_screenshot and self.config.save_analysis_screenshots and not self.config.auto_save_screenshots:
                # 使用 ScreenshotManager 的保存功能，避免重复保存
                timestamp = int(time.time())
                filename = f"analysis_screenshot_{timestamp}.png"
                saved_path = await self.screenshot_manager.save_screenshot_async(
                    screenshot=screenshot,
                    filename=filename
                )
                if saved_path:
                    logger.debug(f"分析截图已保存: {saved_path}")
                else:
                    logger.warning("分析截图保存失败")
            elif save_screenshot and self.config.auto_save_screenshots:
                logger.debug("截图已通过自动保存功能保存，跳过重复保存")
            elif save_screenshot and not self.config.save_analysis_screenshots:
                logger.debug("分析截图保存已禁用，跳过保存")
            
            # 使用VLM分析屏幕
            if self.config.vision.vlm_enabled:
                # 确保VLM服务已启动且可用
                if (self.ollama_service and 
                    hasattr(self.ollama_service, 'is_available') and 
                    self.ollama_service.is_available):
                    
                    # 优先使用异步分析管理器（避免重复VLM调用）
                    if self.async_manager:
                        try:
                            # 提交到异步管理器进行VLM分析
                            task_id = await self.async_manager.analyze_screenshot(
                                screenshot=screenshot,
                                analysis_type="screen_analysis",
                                priority=1
                            )
                            
                            # 等待分析结果
                            vlm_result = await self.async_manager.get_analysis_result(task_id, timeout=30.0)
                            
                            if vlm_result and vlm_result.success:
                                # 将VLM结果转换为AnalysisResult格式
                                result = AnalysisResult(
                                    success=True,
                                    confidence=vlm_result.confidence,
                                    elements=vlm_result.elements,
                                    suggestions=vlm_result.suggestions,
                                    analysis_time=0.0,
                                    raw_data={
                                        "screen_type": vlm_result.screen_type,
                                        "method": "vlm_async",
                                        "task_id": task_id
                                    }
                                )
                            else:
                                logger.warning("异步VLM分析失败，回退到模板匹配")
                                result = await self.vision_service.analyze_screen(screenshot, use_vlm=False)
                                
                        except Exception as e:
                            logger.warning(f"异步分析失败: {e}，回退到直接VLM分析")
                            result = await self.vision_service.analyze_screen(screenshot, use_vlm=True)
                    else:
                        # 没有异步管理器时直接使用VisionService
                        result = await self.vision_service.analyze_screen(screenshot, use_vlm=True)
                else:
                    logger.warning("VLM服务不可用，使用模板匹配分析")
                    result = await self.vision_service.analyze_screen(screenshot, use_vlm=False)
                
                self.analysis_count += 1
                self.last_analysis_time = time.time()
                
                return result
            else:
                logger.warning("VLM未启用，无法进行智能分析")
                return None
                
        except Exception as e:
            logger.error(f"分析当前屏幕失败: {e}")
            return None
    
    async def find_game_element(self, element_name: str) -> Optional[Element]:
        """查找游戏元素
        
        Args:
            element_name: 元素名称
            
        Returns:
            Element: 找到的元素
        """
        if not self.screenshot_manager:
            logger.error("截图管理器未初始化")
            return None
        
        try:
            # 获取当前截图
            screenshot = await self.screenshot_manager.take_screenshot()
            if screenshot is None:
                return None
            
            # 查找元素
            match_result = self.vision_service.find_element(
                screenshot, element_name, use_vlm=True
            )
            
            if match_result:
                return Element(
                    type="interactive",
                    name=element_name,
                    x=match_result.x,
                    y=match_result.y,
                    width=match_result.width,
                    height=match_result.height,
                    confidence=match_result.confidence
                )
            
            return None
            
        except Exception as e:
            logger.error(f"查找游戏元素失败: {e}")
            return None
    
    async def get_game_suggestions(self) -> List[ActionSuggestion]:
        """获取游戏操作建议
        
        Returns:
            List[ActionSuggestion]: 操作建议列表
        """
        try:
            # 分析当前屏幕
            analysis_result = await self.analyze_current_screen()
            
            if analysis_result and analysis_result.success:
                return analysis_result.suggestions
            else:
                logger.warning("无法获取游戏建议：屏幕分析失败")
                return []
                
        except Exception as e:
            logger.error(f"获取游戏建议失败: {e}")
            return []
    
    async def execute_suggestion(self, suggestion: ActionSuggestion) -> bool:
        """执行操作建议
        
        Args:
            suggestion: 操作建议
            
        Returns:
            bool: 执行是否成功
        """
        if not self.automation_backend:
            logger.error("自动化后端未初始化")
            return False
        
        if not suggestion.target:
            logger.error("操作建议缺少目标元素")
            return False
        
        try:
            # 获取目标位置
            x, y = suggestion.target.center
            
            # 根据建议类型执行操作
            if suggestion.action_type == "click":
                await self.automation_backend.click(x, y)
            elif suggestion.action_type == "swipe":
                # 假设建议中包含滑动的终点坐标
                end_x = suggestion.parameters.get("end_x", x + 100)
                end_y = suggestion.parameters.get("end_y", y)
                await self.automation_backend.swipe(
                    x, y, end_x, end_y
                )
            elif suggestion.action_type == "long_press":
                duration = suggestion.parameters.get("duration", 1.0)
                await self.automation_backend.long_press(
                    x, y, duration
                )
            else:
                logger.warning(f"不支持的操作类型: {suggestion.action_type}")
                return False
            
            logger.info(f"✅ 已执行操作建议: {suggestion.description}")
            return True
            
        except Exception as e:
            logger.error(f"执行操作建议失败: {e}")
            return False
    
    async def _auto_analysis_loop(self):
        """自动分析循环"""
        logger.info("🔄 自动分析循环已启动")
        
        while self.is_running:
            try:
                if self.config.async_analysis.auto_analysis_enabled:
                    # 提交自动分析任务
                    if self.screenshot_manager and self.async_manager:
                        screenshot = await self.screenshot_manager.take_screenshot()
                        if screenshot is not None:
                            await self.async_manager.analyze_screenshot(
                                screenshot=screenshot,
                                analysis_type="auto_analysis",
                                priority=self.config.async_analysis.auto_analysis_priority
                            )
                
                # 等待下次分析
                await asyncio.sleep(self.config.async_analysis.auto_analysis_interval)
                
            except Exception as e:
                logger.error(f"自动分析循环出错: {e}")
                await asyncio.sleep(5)  # 出错时等待5秒再继续
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """获取分析统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "total_analyses": self.analysis_count,
            "last_analysis_time": self.last_analysis_time,
            "is_running": self.is_running,
            "services_status": {
                "vision_service": self.vision_service is not None,
                "ollama_service": self.ollama_service is not None,
                "async_manager": self.async_manager is not None,
                "screenshot_manager": self.screenshot_manager is not None
            }
        }
        
        # 添加异步管理器统计信息
        if self.async_manager:
            async_stats = self.async_manager.get_statistics()
            stats["async_analysis"] = async_stats
        
        return stats
    
    async def optimize_prompts(self) -> bool:
        """优化提示词
        
        Returns:
            bool: 优化是否成功
        """
        if not self.async_manager:
            logger.warning("异步管理器未启用，无法优化提示词")
            return False
        
        try:
            success = await self.async_manager.optimize_prompts()
            if success:
                logger.info("✅ 提示词优化完成")
            else:
                logger.warning("⚠️ 提示词优化失败")
            return success
            
        except Exception as e:
            logger.error(f"优化提示词时出错: {e}")
            return False
    
    def __del__(self):
        """析构函数"""
        if self.is_running:
            logger.warning("游戏助手未正常停止，正在清理资源...")