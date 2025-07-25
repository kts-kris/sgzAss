#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的USB连接测试脚本

测试USB连接和截图功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from loguru import logger
from core.device_connector import DeviceConnector
from PIL import Image
import numpy as np

def test_usb_connection():
    """测试USB连接"""
    logger.info("=== USB连接测试 ===")
    
    # 设备配置
    device_settings = {
        "connection_type": "usb",
        "screen_width": 2732,
        "screen_height": 2048
    }
    
    # 创建设备连接器
    device_connector = DeviceConnector(device_settings)
    
    # 尝试连接
    logger.info("正在连接USB设备...")
    if device_connector.connect():
        logger.success("USB连接成功！")
        
        # 测试截图
        logger.info("正在测试截图功能...")
        screenshot = device_connector.get_screenshot()
        
        if screenshot is not None:
            logger.success(f"截图成功！图像尺寸: {screenshot.shape}")
            
            # 保存截图
            image = Image.fromarray(screenshot)
            screenshot_path = "usb_test_screenshot.png"
            image.save(screenshot_path)
            logger.info(f"截图已保存: {screenshot_path}")
            
            # 检查截图是否为空白
            if np.sum(screenshot) == 0:
                logger.warning("截图为空白图像，可能是截图服务不可用")
            else:
                logger.success("截图包含内容，USB连接工作正常")
        else:
            logger.error("截图失败")
        
        # 断开连接
        device_connector.disconnect()
        logger.info("已断开连接")
    else:
        logger.error("USB连接失败")

if __name__ == "__main__":
    test_usb_connection()