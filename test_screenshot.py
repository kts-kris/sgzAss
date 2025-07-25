#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试截图功能

这个脚本用于测试设备连接和截图功能，帮助定位问题。
"""

import os
import sys
import time
import cv2
import numpy as np
from pathlib import Path

# 确保可以导入自定义模块
sys.path.append(str(Path(__file__).parent.absolute()))

# 导入项目模块
from config import DEVICE_SETTINGS, SCREENSHOT_DIR
from core.device_connector import DeviceConnector


def main():
    """主函数"""
    print("开始测试截图功能...")
    print(f"设备连接类型: {DEVICE_SETTINGS['connection_type']}")
    
    # 确保截图目录存在
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # 连接设备
    print("正在连接设备...")
    device = DeviceConnector(DEVICE_SETTINGS)
    if not device.connect():
        print("设备连接失败，请检查设备连接设置")
        return 1
    print("设备连接成功")
    
    try:
        # 获取截图
        print("正在获取截图...")
        screenshot = device.get_screenshot()
        
        if screenshot is None:
            print("获取截图失败")
            return 1
        
        # 保存截图
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"test_screenshot_{timestamp}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        cv2.imwrite(filepath, screenshot)
        print(f"截图已保存: {filepath}")
        
        # 显示截图尺寸
        height, width = screenshot.shape[:2]
        print(f"截图尺寸: {width}x{height}")
        
        # 断开设备连接
        device.disconnect()
        print("设备已断开连接")
        
        return 0
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        device.disconnect()
        return 1


if __name__ == "__main__":
    sys.exit(main())