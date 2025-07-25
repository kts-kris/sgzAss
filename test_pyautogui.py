#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试 pyautogui 截图功能

这个脚本用于测试 pyautogui 的截图功能，帮助定位问题。
"""

import os
import sys
import time
import cv2
import numpy as np
import pyautogui
from PIL import Image
import io

def main():
    """主函数"""
    print("开始测试 pyautogui 截图功能...")
    
    try:
        # 方法1：直接使用 pyautogui.screenshot()
        print("\n方法1: 使用 pyautogui.screenshot()")
        try:
            screenshot1 = pyautogui.screenshot()
            print(f"截图1尺寸: {screenshot1.width}x{screenshot1.height}")
            
            # 保存截图
            screenshot1.save("test_screenshot1.png")
            print("截图1已保存为: test_screenshot1.png")
        except Exception as e:
            print(f"方法1失败: {e}")
        
        # 方法2：指定区域截图
        print("\n方法2: 指定区域截图")
        try:
            # 截取屏幕左上角的 500x500 区域
            screenshot2 = pyautogui.screenshot(region=(0, 0, 500, 500))
            print(f"截图2尺寸: {screenshot2.width}x{screenshot2.height}")
            
            # 保存截图
            screenshot2.save("test_screenshot2.png")
            print("截图2已保存为: test_screenshot2.png")
        except Exception as e:
            print(f"方法2失败: {e}")
        
        # 方法3：使用PIL的ImageGrab
        print("\n方法3: 使用PIL的ImageGrab")
        try:
            from PIL import ImageGrab
            screenshot3 = ImageGrab.grab()
            print(f"截图3尺寸: {screenshot3.width}x{screenshot3.height}")
            
            # 保存截图
            screenshot3.save("test_screenshot3.png")
            print("截图3已保存为: test_screenshot3.png")
        except Exception as e:
            print(f"方法3失败: {e}")
        
        # 方法4：使用PIL的ImageGrab指定区域
        print("\n方法4: 使用PIL的ImageGrab指定区域")
        try:
            from PIL import ImageGrab
            screenshot4 = ImageGrab.grab(bbox=(0, 0, 500, 500))
            print(f"截图4尺寸: {screenshot4.width}x{screenshot4.height}")
            
            # 保存截图
            screenshot4.save("test_screenshot4.png")
            print("截图4已保存为: test_screenshot4.png")
        except Exception as e:
            print(f"方法4失败: {e}")
        
        return 0
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())