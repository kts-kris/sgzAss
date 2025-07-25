#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试 pymobiledevice3 USB 截图功能
"""

import os
import sys
import time
from PIL import Image
import io

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from loguru import logger

# 设置日志
logger.add("logs/test_pymobiledevice3.log", rotation="10 MB", retention="7 days", level="INFO")

def test_pymobiledevice3_screenshot():
    """测试 pymobiledevice3 截图功能"""
    try:
        # 导入 pymobiledevice3
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.services.screenshot import ScreenshotService
        
        logger.info("开始测试 pymobiledevice3 USB 截图功能...")
        
        # 创建 lockdown 客户端
        logger.info("正在连接USB设备...")
        lockdown_client = create_using_usbmux()
        
        # 获取设备信息
        device_name = lockdown_client.get_value('DeviceName')
        product_version = lockdown_client.get_value('ProductVersion')
        device_class = lockdown_client.get_value('DeviceClass')
        
        logger.info(f"设备信息:")
        logger.info(f"  设备名称: {device_name}")
        logger.info(f"  iOS版本: {product_version}")
        logger.info(f"  设备类型: {device_class}")
        
        # 创建截图服务
        logger.info("正在初始化截图服务...")
        screenshot_service = ScreenshotService(lockdown=lockdown_client)
        
        # 获取截图
        logger.info("正在获取截图...")
        start_time = time.time()
        screenshot_data = screenshot_service.take_screenshot()
        end_time = time.time()
        
        logger.info(f"截图获取完成，耗时: {end_time - start_time:.2f}秒")
        logger.info(f"截图数据大小: {len(screenshot_data)} 字节")
        
        # 保存截图
        image = Image.open(io.BytesIO(screenshot_data))
        
        # 创建保存目录
        screenshots_dir = os.path.join(project_root, "resources", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # 保存截图文件
        timestamp = int(time.time())
        screenshot_path = os.path.join(screenshots_dir, f"pymobiledevice3_test_{timestamp}.png")
        image.save(screenshot_path)
        
        logger.info(f"截图已保存到: {screenshot_path}")
        logger.info(f"截图尺寸: {image.width}x{image.height}")
        logger.info(f"截图格式: {image.mode}")
        
        logger.info("pymobiledevice3 USB 截图测试成功！")
        return True
        
    except ImportError as e:
        logger.error(f"pymobiledevice3 导入失败: {e}")
        logger.error("请确保已安装 pymobiledevice3: pip install pymobiledevice3")
        return False
    except Exception as e:
        logger.exception(f"pymobiledevice3 截图测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("pymobiledevice3 USB 截图功能测试")
    logger.info("=" * 50)
    
    success = test_pymobiledevice3_screenshot()
    
    if success:
        logger.info("测试完成：成功")
        return 0
    else:
        logger.error("测试完成：失败")
        return 1

if __name__ == "__main__":
    exit(main())