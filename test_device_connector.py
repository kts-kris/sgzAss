#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试修改后的 device_connector.py 功能
"""

import os
import sys
import time
from PIL import Image
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from loguru import logger
from core.device_connector import DeviceConnector

# 设置日志
logger.add("logs/test_device_connector.log", rotation="10 MB", retention="7 days", level="INFO")

def test_device_connector():
    """测试设备连接器功能"""
    try:
        logger.info("开始测试设备连接器功能...")
        
        # 设备配置
        device_settings = {
            "connection_type": "usb",
            "device_ip": "",
            "device_port": 5555,
            "screen_width": 2732,
            "screen_height": 2048
        }
        
        # 创建设备连接器
        logger.info("创建设备连接器...")
        connector = DeviceConnector(device_settings)
        
        # 连接设备
        logger.info("正在连接设备...")
        if not connector.connect():
            logger.error("设备连接失败")
            return False
        
        logger.info("设备连接成功")
        
        # 获取截图
        logger.info("正在获取截图...")
        start_time = time.time()
        screenshot = connector.get_screenshot()
        end_time = time.time()
        
        if screenshot is None:
            logger.error("截图获取失败")
            return False
        
        logger.info(f"截图获取成功，耗时: {end_time - start_time:.2f}秒")
        logger.info(f"截图尺寸: {screenshot.shape}")
        logger.info(f"截图数据类型: {screenshot.dtype}")
        
        # 保存截图
        screenshots_dir = os.path.join(project_root, "resources", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        timestamp = int(time.time())
        screenshot_path = os.path.join(screenshots_dir, f"device_connector_test_{timestamp}.png")
        
        # 将numpy数组转换为PIL图像并保存
        image = Image.fromarray(screenshot)
        image.save(screenshot_path)
        
        logger.info(f"截图已保存到: {screenshot_path}")
        
        # 断开连接
        logger.info("断开设备连接...")
        connector.disconnect()
        
        logger.info("设备连接器测试成功！")
        return True
        
    except Exception as e:
        logger.exception(f"设备连接器测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("设备连接器功能测试")
    logger.info("=" * 50)
    
    success = test_device_connector()
    
    if success:
        logger.info("测试完成：成功")
        return 0
    else:
        logger.error("测试完成：失败")
        return 1

if __name__ == "__main__":
    exit(main())