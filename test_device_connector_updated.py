#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的设备连接器截图功能
"""

import sys
import os
import logging
from PIL import Image

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.device_connector import DeviceConnector

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_device_connector_screenshot():
    """测试设备连接器截图功能"""
    print("=== 测试设备连接器截图功能 ===")
    
    try:
        # 创建设备连接器实例
        device_settings = {
            "connection_type": "usb",
            "device_ip": "",
            "device_port": 5555,
            "screen_width": 2732,
            "screen_height": 2048
        }
        connector = DeviceConnector(device_settings)
        print("✓ 设备连接器创建成功")
        
        # 连接设备
        print("正在连接设备...")
        if connector.connect():
            print("✓ 设备连接成功")
        else:
            print("⚠ 设备连接失败，但继续测试截图功能")
        
        # 尝试获取截图
        print("\n正在获取截图...")
        screenshot = connector.get_screenshot()
        
        if screenshot is not None and hasattr(screenshot, 'shape'):
            # 检查截图是否为有效图像
            try:
                # screenshot是numpy数组，直接获取尺寸信息
                height, width = screenshot.shape[:2]
                channels = screenshot.shape[2] if len(screenshot.shape) > 2 else 1
                
                print(f"✓ 截图获取成功!")
                print(f"  - 数据类型: numpy数组")
                print(f"  - 图像尺寸: {width}x{height}")
                print(f"  - 通道数: {channels}")
                print(f"  - 数据形状: {screenshot.shape}")
                
                # 检查数组大小
                array_size = screenshot.size * screenshot.itemsize
                print(f"  - 数组大小: {array_size} 字节")
                
                # 保存截图到文件以验证
                img = Image.fromarray(screenshot)
                test_file = "test_screenshot_result.png"
                img.save(test_file)
                file_size = os.path.getsize(test_file)
                print(f"  - 保存文件: {test_file} ({file_size} 字节)")
                
                if width > 100 and height > 100 and file_size > 10000:  # 基本尺寸和大小检查
                    print("✓ 截图内容验证通过")
                    return True
                else:
                    print("✗ 截图尺寸或大小异常")
                    return False
                    
            except Exception as e:
                print(f"✗ 截图文件无效: {e}")
                return False
        else:
            print("✗ 截图获取失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    """主函数"""
    setup_logging()
    
    print("开始测试更新后的设备连接器截图功能...\n")
    
    success = test_device_connector_screenshot()
    
    print("\n=== 测试结果 ===")
    if success:
        print("✓ 设备连接器截图功能测试通过")
        print("建议: 可以继续测试主程序功能")
    else:
        print("✗ 设备连接器截图功能测试失败")
        print("建议: 检查设备连接和权限设置")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())