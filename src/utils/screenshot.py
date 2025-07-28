#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
截图工具模块

提供统一的截图功能接口
"""

import time
import asyncio
import glob
from pathlib import Path
from typing import Optional, Union, List
import numpy as np
from PIL import Image
from loguru import logger

from .helpers import save_screenshot, get_timestamp, ensure_dir
from ..services.connection import ConnectionService
from ..utils.config import get_config


class ScreenshotManager:
    """截图管理器"""
    
    def __init__(self, connection: Optional[ConnectionService] = None):
        """
        初始化截图管理器
        
        Args:
            connection: 设备连接对象
        """
        self.connection = connection
        self.config = get_config()
        self._last_screenshot = None
        self._last_screenshot_time = 0
        
    async def take_screenshot(self) -> Optional[np.ndarray]:
        """
        异步获取截图
        
        Returns:
            Optional[np.ndarray]: 截图数据，BGR格式
        """
        if not self.connection:
            logger.error("设备连接未初始化")
            return None
            
        try:
            # 在线程池中执行截图操作
            loop = asyncio.get_event_loop()
            screenshot = await loop.run_in_executor(
                None, self.connection.get_screenshot
            )
            
            if screenshot is not None:
                self._last_screenshot = screenshot
                self._last_screenshot_time = time.time()
                logger.debug("异步截图获取成功")
                
            return screenshot
            
        except Exception as e:
            logger.error(f"异步截图获取失败: {e}")
            return None
    
    def take_screenshot_sync(self) -> Optional[np.ndarray]:
        """
        同步获取截图
        
        Returns:
            Optional[np.ndarray]: 截图数据，BGR格式
        """
        if not self.connection:
            logger.error("设备连接未初始化")
            return None
            
        try:
            screenshot = self.connection.get_screenshot()
            
            if screenshot is not None:
                self._last_screenshot = screenshot
                self._last_screenshot_time = time.time()
                logger.debug("同步截图获取成功")
                
            return screenshot
            
        except Exception as e:
            logger.error(f"同步截图获取失败: {e}")
            return None
    
    async def save_screenshot_async(
        self, 
        screenshot: Optional[np.ndarray] = None,
        filename: Optional[str] = None,
        directory: Optional[Union[str, Path]] = None
    ) -> Optional[str]:
        """
        异步保存截图
        
        Args:
            screenshot: 截图数据，如果为None则使用最后一次截图
            filename: 文件名，如果为None则自动生成
            directory: 保存目录，如果为None则使用配置中的目录
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        if screenshot is None:
            screenshot = self._last_screenshot
            
        if screenshot is None:
            logger.error("没有可用的截图数据")
            return None
            
        try:
            # 确定保存目录
            if directory is None:
                from ..utils.config import get_config_manager
                config_manager = get_config_manager()
                save_dir = config_manager.get_screenshot_dir()
            else:
                save_dir = Path(directory)
                
            # 确保目录存在
            ensure_dir(save_dir)
            
            # 生成文件名
            if filename is None:
                timestamp = get_timestamp()
                filename = f"screenshot_{timestamp}.png"
                
            filepath = save_dir / filename
            
            # 在线程池中保存截图
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, save_screenshot, screenshot, str(filepath)
            )
            
            logger.debug(f"截图已保存: {filepath}")
            
            # 自动清理旧截图
            config = get_config()
            if config.screenshot.cleanup_on_save:
                await self.cleanup_old_screenshots_async(save_dir)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"保存截图失败: {e}")
            return None
    
    def save_screenshot_sync(
        self,
        screenshot: Optional[np.ndarray] = None,
        filename: Optional[str] = None,
        directory: Optional[Union[str, Path]] = None
    ) -> Optional[str]:
        """
        同步保存截图
        
        Args:
            screenshot: 截图数据，如果为None则使用最后一次截图
            filename: 文件名，如果为None则自动生成
            directory: 保存目录，如果为None则使用配置中的目录
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        if screenshot is None:
            screenshot = self._last_screenshot
            
        if screenshot is None:
            logger.error("没有可用的截图数据")
            return None
            
        try:
            # 确定保存目录
            if directory is None:
                from ..utils.config import get_config_manager
                config_manager = get_config_manager()
                save_dir = config_manager.get_screenshot_dir()
            else:
                save_dir = Path(directory)
                
            # 确保目录存在
            ensure_dir(save_dir)
            
            # 生成文件名
            if filename is None:
                timestamp = get_timestamp()
                filename = f"screenshot_{timestamp}.png"
                
            filepath = save_dir / filename
            
            # 保存截图
            save_screenshot(screenshot, str(filepath))
            
            logger.debug(f"截图已保存: {filepath}")
            
            # 自动清理旧截图
            config = get_config()
            if config.screenshot.cleanup_on_save:
                self.cleanup_old_screenshots(save_dir)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"保存截图失败: {e}")
            return None
    
    @property
    def last_screenshot(self) -> Optional[np.ndarray]:
        """获取最后一次截图"""
        return self._last_screenshot
    
    @property
    def last_screenshot_time(self) -> float:
        """获取最后一次截图时间"""
        return self._last_screenshot_time
    
    def cleanup_old_screenshots(self, directory: Optional[Union[str, Path]] = None) -> int:
        """清理旧截图文件
        
        Args:
            directory: 清理目录，如果为None则使用配置中的目录
            
        Returns:
            int: 清理的文件数量
        """
        try:
            # 确定清理目录
            if directory is None:
                from ..utils.config import get_config_manager
                config_manager = get_config_manager()
                cleanup_dir = config_manager.get_screenshot_dir()
            else:
                cleanup_dir = Path(directory)
            
            if not cleanup_dir.exists():
                logger.debug(f"截图目录不存在: {cleanup_dir}")
                return 0
            
            # 获取配置
            config = get_config()
            screenshot_config = config.screenshot
            
            if not screenshot_config.auto_cleanup:
                logger.debug("自动清理已禁用")
                return 0
            
            cleaned_count = 0
            
            # 按模式清理文件
            for pattern in screenshot_config.cleanup_patterns:
                files = list(cleanup_dir.glob(pattern))
                
                if len(files) <= screenshot_config.max_keep_count:
                    continue
                
                # 按修改时间排序，保留最新的文件
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                files_to_delete = files[screenshot_config.max_keep_count:]
                
                for file_path in files_to_delete:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"已删除旧截图: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"删除文件失败 {file_path}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"清理完成，删除了 {cleaned_count} 个旧截图文件")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理截图失败: {e}")
            return 0
    
    async def cleanup_old_screenshots_async(self, directory: Optional[Union[str, Path]] = None) -> int:
        """异步清理旧截图文件
        
        Args:
            directory: 清理目录，如果为None则使用配置中的目录
            
        Returns:
            int: 清理的文件数量
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.cleanup_old_screenshots, directory)
    
    def get_screenshot_files(self, directory: Optional[Union[str, Path]] = None) -> List[Path]:
        """获取截图文件列表
        
        Args:
            directory: 查找目录，如果为None则使用配置中的目录
            
        Returns:
            List[Path]: 截图文件路径列表
        """
        try:
            # 确定查找目录
            if directory is None:
                from ..utils.config import get_config_manager
                config_manager = get_config_manager()
                search_dir = config_manager.get_screenshot_dir()
            else:
                search_dir = Path(directory)
            
            if not search_dir.exists():
                return []
            
            # 获取配置
            config = get_config()
            screenshot_config = config.screenshot
            
            all_files = []
            
            # 按模式查找文件
            for pattern in screenshot_config.cleanup_patterns:
                files = list(search_dir.glob(pattern))
                all_files.extend(files)
            
            # 去重并按修改时间排序
            unique_files = list(set(all_files))
            unique_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            return unique_files
            
        except Exception as e:
            logger.error(f"获取截图文件列表失败: {e}")
            return []


# 便捷函数
async def take_screenshot_async(connection: ConnectionService) -> Optional[np.ndarray]:
    """
    便捷的异步截图函数
    
    Args:
        connection: 设备连接对象
        
    Returns:
        Optional[np.ndarray]: 截图数据
    """
    manager = ScreenshotManager(connection)
    return await manager.take_screenshot()


def take_screenshot_sync(connection: ConnectionService) -> Optional[np.ndarray]:
    """
    便捷的同步截图函数
    
    Args:
        connection: 设备连接对象
        
    Returns:
        Optional[np.ndarray]: 截图数据
    """
    manager = ScreenshotManager(connection)
    return manager.take_screenshot_sync()


async def save_screenshot_async(
    screenshot: np.ndarray,
    filename: Optional[str] = None,
    directory: Optional[Union[str, Path]] = None
) -> Optional[str]:
    """
    便捷的异步保存截图函数
    
    Args:
        screenshot: 截图数据
        filename: 文件名
        directory: 保存目录
        
    Returns:
        Optional[str]: 保存的文件路径
    """
    manager = ScreenshotManager()
    return await manager.save_screenshot_async(screenshot, filename, directory)


def save_screenshot_sync(
    screenshot: np.ndarray,
    filename: Optional[str] = None,
    directory: Optional[Union[str, Path]] = None
) -> Optional[str]:
    """
    便捷的同步保存截图函数
    
    Args:
        screenshot: 截图数据
        filename: 文件名
        directory: 保存目录
        
    Returns:
        Optional[str]: 保存的文件路径
    """
    manager = ScreenshotManager()
    return manager.save_screenshot_sync(screenshot, filename, directory)