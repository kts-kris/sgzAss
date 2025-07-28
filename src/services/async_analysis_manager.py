#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
异步截图分析管理器

负责协调截图获取、VLM分析和结果输出的整个异步流程。
提供实时分析、批量分析和智能调度功能。
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Coroutine
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from loguru import logger

from .ollama_vlm import OllamaVLMService
from .connection import ConnectionService
from ..models import (
    VLMResult, AnalysisResult, Element, ActionSuggestion,
    VLMError, ScreenshotError
)
from ..utils.config import ConfigManager
from ..utils.helpers import save_screenshot, format_timestamp


@dataclass
class AnalysisTask:
    """分析任务数据类"""
    task_id: str
    screenshot: np.ndarray
    timestamp: float
    analysis_type: str = "game_analysis"
    custom_prompt: Optional[str] = None
    priority: int = 1
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnalysisRecord:
    """分析记录数据类"""
    task_id: str
    timestamp: float
    screenshot_path: str
    vlm_result: VLMResult
    analysis_duration: float
    user_feedback: Optional[str] = None
    accuracy_score: Optional[float] = None


class AsyncAnalysisManager:
    """异步截图分析管理器"""
    
    def __init__(self, 
                 config_manager: ConfigManager,
                 connection_service: ConnectionService,
                 max_concurrent_tasks: int = 3,
                 analysis_history_limit: int = 100):
        """
        初始化异步分析管理器
        
        Args:
            config_manager: 配置管理器
            connection_service: 连接服务
            max_concurrent_tasks: 最大并发任务数
            analysis_history_limit: 分析历史记录限制
        """
        self.config = config_manager
        self.connection = connection_service
        self.max_concurrent_tasks = max_concurrent_tasks
        self.analysis_history_limit = analysis_history_limit
        
        # VLM服务
        self.vlm_service = None
        
        # 任务队列和管理
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.completed_tasks = {}
        self.analysis_history = []
        self.history_limit = analysis_history_limit
        
        # 控制标志
        self.is_running = False
        self.auto_analysis_enabled = False
        self.analysis_interval = 5.0  # 自动分析间隔（秒）
        
        # 线程池用于CPU密集型任务
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        
        # 结果输出回调
        self.result_callbacks = []
        
        # 统计信息
        self.stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_duration": 0.0,
            "prompt_optimizations": 0
        }
    
    async def initialize(self) -> bool:
        """
        初始化分析管理器
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 初始化VLM服务
            vlm_config = self.config.get_vlm_config()
            self.vlm_service = OllamaVLMService(
                host=vlm_config.host,
                port=vlm_config.port,
                model=vlm_config.model,
                timeout=vlm_config.timeout
            )
            
            if not await self.vlm_service.initialize():
                logger.error("VLM服务初始化失败")
                return False
            
            # 启动任务处理器
            self.is_running = True
            asyncio.create_task(self._task_processor())
            
            # 添加默认结果输出回调
            self.add_result_callback(self._default_result_callback)
            
            logger.info("异步分析管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"异步分析管理器初始化失败: {e}")
            return False
    
    async def start(self) -> bool:
        """启动异步分析管理器"""
        return await self.initialize()
    
    async def stop(self) -> None:
        """停止异步分析管理器"""
        try:
            self.is_running = False
            self.auto_analysis_enabled = False
            
            # 停止VLM服务
            if self.vlm_service:
                await self.vlm_service.stop()
            
            # 关闭线程池
            if self.thread_pool:
                self.thread_pool.shutdown(wait=True)
            
            logger.info("异步分析管理器已停止")
            
        except Exception as e:
            logger.error(f"停止异步分析管理器失败: {e}")
    
    async def start_auto_analysis(self, interval: float = 5.0) -> None:
        """
        启动自动截图分析
        
        Args:
            interval: 分析间隔（秒）
        """
        self.analysis_interval = interval
        self.auto_analysis_enabled = True
        
        # 启动自动分析任务
        asyncio.create_task(self._auto_analysis_loop())
        logger.info(f"自动截图分析已启动，间隔: {interval}秒")
    
    async def stop_auto_analysis(self) -> None:
        """停止自动截图分析"""
        self.auto_analysis_enabled = False
        logger.info("自动截图分析已停止")
    
    async def analyze_screenshot(self, 
                               screenshot: Optional[np.ndarray] = None,
                               analysis_type: str = "game_analysis",
                               custom_prompt: Optional[str] = None,
                               priority: int = 1,
                               callback: Optional[Callable] = None) -> str:
        """
        提交截图分析任务
        
        Args:
            screenshot: 截图数据，如果为None则自动获取
            analysis_type: 分析类型
            custom_prompt: 自定义提示词
            priority: 任务优先级
            callback: 完成回调函数
            
        Returns:
            str: 任务ID
        """
        try:
            # 获取截图
            if screenshot is None:
                screenshot = await self._capture_screenshot()
            
            # 创建任务
            task_id = f"analysis_{int(time.time() * 1000)}"
            task = AnalysisTask(
                task_id=task_id,
                screenshot=screenshot,
                timestamp=time.time(),
                analysis_type=analysis_type,
                custom_prompt=custom_prompt,
                priority=priority,
                callback=callback
            )
            
            # 添加到队列
            await self.task_queue.put(task)
            logger.info(f"分析任务已提交: {task_id}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"提交分析任务失败: {e}")
            raise
    
    async def get_analysis_result(self, task_id: str, timeout: float = 60.0) -> Optional[VLMResult]:
        """
        获取分析结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
            
        Returns:
            VLMResult: 分析结果，如果超时或失败则返回None
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            
            await asyncio.sleep(0.1)
        
        logger.warning(f"获取分析结果超时: {task_id}")
        return None
    
    def add_result_callback(self, callback: Callable[[str, VLMResult], None]) -> None:
        """
        添加结果回调函数
        
        Args:
            callback: 回调函数，接收(task_id, result)参数
        """
        self.result_callbacks.append(callback)
    
    async def optimize_prompts(self, user_feedback: Optional[str] = None) -> bool:
        """
        基于历史数据优化提示词
        
        Args:
            user_feedback: 用户反馈
            
        Returns:
            bool: 优化是否成功
        """
        try:
            if len(self.analysis_history) < 5:
                logger.warning("历史数据不足，无法进行提示词优化")
                return False
            
            # 准备历史数据
            history_data = []
            for record in self.analysis_history[-20:]:  # 使用最近20条记录
                history_data.append({
                    "timestamp": record.timestamp,
                    "scene": record.vlm_result.description,
                    "accuracy": record.accuracy_score or 0.8,
                    "elements_count": len(record.vlm_result.elements),
                    "suggestions_count": len(record.vlm_result.suggestions)
                })
            
            # 调用VLM服务进行提示词优化
            optimized_prompt = await self.vlm_service.generate_optimized_prompt(
                history_data, user_feedback
            )
            
            # 更新提示词模板
            self.vlm_service.prompt_templates["game_analysis"] = optimized_prompt
            
            # 更新统计
            self.stats["prompt_optimizations"] += 1
            
            logger.info("提示词优化完成")
            return True
            
        except Exception as e:
            logger.error(f"提示词优化失败: {e}")
            return False
    
    async def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        获取分析统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = self.stats.copy()
        stats.update({
            "queue_size": self.task_queue.qsize(),
            "active_tasks_count": len(self.active_tasks),
            "history_count": len(self.analysis_history),
            "auto_analysis_enabled": self.auto_analysis_enabled,
            "vlm_service_available": self.vlm_service.is_available if self.vlm_service else False
        })
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息（同步版本）
        
        Returns:
            Dict: 统计信息
        """
        stats = self.stats.copy()
        stats.update({
            "queue_size": self.task_queue.qsize(),
            "active_tasks_count": len(self.active_tasks),
            "history_count": len(self.analysis_history),
            "auto_analysis_enabled": self.auto_analysis_enabled,
            "vlm_service_available": self.vlm_service.is_available if self.vlm_service else False
        })
        # 添加测试需要的字段
        stats['total_tasks'] = stats.get('total_analyses', 0)
        return stats
    
    async def _task_processor(self) -> None:
        """任务处理器主循环"""
        logger.info("任务处理器已启动")
        
        while self.is_running:
            try:
                # 控制并发数量
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                    continue
                
                # 获取任务（带超时）
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # 启动任务处理
                asyncio.create_task(self._process_task(task))
                
            except Exception as e:
                logger.error(f"任务处理器错误: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_task(self, task: AnalysisTask) -> None:
        """处理单个分析任务"""
        start_time = time.time()
        self.active_tasks[task.task_id] = task
        
        try:
            logger.info(f"开始处理分析任务: {task.task_id}")
            
            # 保存截图
            screenshot_path = await self._save_task_screenshot(task)
            
            # 执行VLM分析
            vlm_result = await self.vlm_service.analyze_screenshot_async(
                task.screenshot,
                task.analysis_type,
                task.custom_prompt
            )
            
            # 计算分析时长
            analysis_duration = time.time() - start_time
            
            # 创建分析记录
            record = AnalysisRecord(
                task_id=task.task_id,
                timestamp=task.timestamp,
                screenshot_path=screenshot_path,
                vlm_result=vlm_result,
                analysis_duration=analysis_duration
            )
            
            # 添加到历史记录
            self._add_to_history(record)
            
            # 保存结果
            self.completed_tasks[task.task_id] = vlm_result
            
            # 更新统计
            self._update_stats(vlm_result, analysis_duration)
            
            # 调用回调函数
            await self._call_callbacks(task.task_id, vlm_result)
            
            # 执行任务特定回调
            if task.callback:
                try:
                    if asyncio.iscoroutinefunction(task.callback):
                        await task.callback(task.task_id, vlm_result)
                    else:
                        task.callback(task.task_id, vlm_result)
                except Exception as e:
                    logger.error(f"任务回调执行失败: {e}")
            
            logger.info(f"分析任务完成: {task.task_id}, 耗时: {analysis_duration:.2f}秒")
            
        except Exception as e:
            logger.error(f"分析任务失败: {task.task_id}, 错误: {e}")
            
            # 创建失败结果
            failed_result = VLMResult(
                success=False,
                description=f"分析失败: {str(e)}",
                elements=[],
                suggestions=[],
                confidence=0.0,
                model_name=self.vlm_service.model if self.vlm_service else "unknown"
            )
            
            self.completed_tasks[task.task_id] = failed_result
            self.stats["failed_analyses"] += 1
            
        finally:
            # 清理活动任务
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    async def _auto_analysis_loop(self) -> None:
        """自动分析循环"""
        logger.info("自动分析循环已启动")
        
        while self.auto_analysis_enabled:
            try:
                # 提交自动分析任务
                await self.analyze_screenshot(
                    analysis_type="game_analysis",
                    priority=0  # 低优先级
                )
                
                # 等待下次分析
                await asyncio.sleep(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"自动分析错误: {e}")
                await asyncio.sleep(5.0)  # 错误后等待更长时间
    
    async def _capture_screenshot(self) -> np.ndarray:
        """获取截图"""
        try:
            screenshot = await self.connection.get_screenshot()
            if screenshot is None:
                raise ScreenshotError("截图获取失败")
            return screenshot
        except Exception as e:
            logger.error(f"截图获取失败: {e}")
            raise ScreenshotError(f"截图获取失败: {e}")
    
    async def _save_task_screenshot(self, task: AnalysisTask) -> str:
        """保存任务截图"""
        try:
            timestamp_str = format_timestamp(task.timestamp)
            filename = f"analysis_{task.task_id}_{timestamp_str}.png"
            
            screenshot_dir = Path(self.config.get_screenshot_dir())
            screenshot_path = screenshot_dir / filename
            
            # 在线程池中保存截图
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.thread_pool,
                save_screenshot,
                task.screenshot,
                str(screenshot_path)
            )
            
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"保存截图失败: {e}")
            return ""
    
    def _add_to_history(self, record: AnalysisRecord) -> None:
        """添加到历史记录"""
        self.analysis_history.append(record)
        
        # 限制历史记录数量
        if len(self.analysis_history) > self.analysis_history_limit:
            self.analysis_history = self.analysis_history[-self.analysis_history_limit:]
    
    def _update_stats(self, result: VLMResult, duration: float) -> None:
        """更新统计信息"""
        self.stats["total_analyses"] += 1
        
        if result.success:
            self.stats["successful_analyses"] += 1
        else:
            self.stats["failed_analyses"] += 1
        
        # 更新平均时长
        total = self.stats["total_analyses"]
        current_avg = self.stats["average_duration"]
        self.stats["average_duration"] = (current_avg * (total - 1) + duration) / total
    
    async def _call_callbacks(self, task_id: str, result: VLMResult) -> None:
        """调用结果回调函数"""
        for callback in self.result_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_id, result)
                else:
                    callback(task_id, result)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}")
    
    async def _default_result_callback(self, task_id: str, result: VLMResult) -> None:
        """默认结果输出回调"""
        try:
            # 格式化输出分析结果
            print("\n" + "="*60)
            print(f"📱 截图分析结果 - 任务ID: {task_id}")
            print("="*60)
            
            if result.success:
                print(f"✅ 分析成功 (置信度: {result.confidence:.2f})")
                print(f"🎮 模型: {result.model_name}")
                print(f"📝 描述: {result.description}")
                
                if result.elements:
                    print(f"\n🎯 发现元素 ({len(result.elements)}个):")
                    for i, element in enumerate(result.elements[:5], 1):  # 只显示前5个
                        print(f"  {i}. {element.name} - {element.element_type.value} "
                              f"({element.position[0]}, {element.position[1]}) "
                              f"置信度: {element.confidence:.2f}")
                
                if result.suggestions:
                    print(f"\n💡 操作建议 ({len(result.suggestions)}个):")
                    for i, suggestion in enumerate(result.suggestions[:3], 1):  # 只显示前3个
                        print(f"  {i}. {suggestion.action_type.value}: {suggestion.description} "
                              f"(优先级: {suggestion.priority}, 置信度: {suggestion.confidence:.2f})")
            else:
                print(f"❌ 分析失败: {result.description}")
            
            print("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"默认回调输出失败: {e}")
    
    async def close(self) -> None:
        """关闭分析管理器"""
        logger.info("正在关闭异步分析管理器...")
        
        # 停止自动分析
        self.auto_analysis_enabled = False
        
        # 停止任务处理器
        self.is_running = False
        
        # 等待活动任务完成
        while self.active_tasks:
            logger.info(f"等待 {len(self.active_tasks)} 个活动任务完成...")
            await asyncio.sleep(1.0)
        
        # 关闭VLM服务
        if self.vlm_service:
            await self.vlm_service.close()
        
        # 关闭线程池
        self.thread_pool.shutdown(wait=True)
        
        logger.info("异步分析管理器已关闭")