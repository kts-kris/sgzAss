#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试不同的截图方法
比较 ScreenshotService 和 DVT Screenshot 的差异
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from loguru import logger
from PIL import Image
import io

try:
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.screenshot import ScreenshotService
    from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
    from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot
    from pymobiledevice3.exceptions import (
        InvalidServiceError, 
        PasswordRequiredError, 
        NoDeviceConnectedError, 
        PairingError
    )
except ImportError as e:
    logger.error(f"导入 pymobiledevice3 失败: {e}")
    sys.exit(1)

def test_screenshot_service():
    """测试传统的 ScreenshotService"""
    logger.info("=== 测试 ScreenshotService ===")
    
    try:
        # 创建 lockdown 客户端
        lockdown_client = create_using_usbmux()
        logger.info("Lockdown 客户端创建成功")
        
        # 创建截图服务
        screenshot_service = ScreenshotService(lockdown=lockdown_client)
        logger.info("ScreenshotService 创建成功")
        
        # 获取截图
        start_time = time.time()
        screenshot_data = screenshot_service.take_screenshot()
        duration = time.time() - start_time
        
        if screenshot_data:
            logger.success(f"ScreenshotService 截图成功，耗时: {duration:.3f}秒，数据大小: {len(screenshot_data)} bytes")
            
            # 保存截图
            image = Image.open(io.BytesIO(screenshot_data))
            # 确保resources目录存在
            resources_dir = Path(__file__).parent / "resources"
            resources_dir.mkdir(exist_ok=True)
            image.save(resources_dir / "test_screenshot_service.png")
            logger.info(f"截图已保存，尺寸: {image.width}x{image.height}")
            return True
        else:
            logger.error("ScreenshotService 截图失败：数据为空")
            return False
            
    except Exception as e:
        logger.error(f"ScreenshotService 测试失败: {e}")
        logger.error(f"异常类型: {type(e).__name__}")
        import traceback
        logger.debug(f"完整异常堆栈:\n{traceback.format_exc()}")
        return False

def test_dvt_screenshot():
    """测试 DVT Screenshot 服务"""
    logger.info("=== 测试 DVT Screenshot ===")
    
    try:
        # 创建 lockdown 客户端
        lockdown_client = create_using_usbmux()
        logger.info("Lockdown 客户端创建成功")
        
        # 创建 DVT 服务
        dvt_service = DvtSecureSocketProxyService(lockdown=lockdown_client)
        logger.info("DvtSecureSocketProxyService 创建成功")
        
        # 创建截图服务
        screenshot = Screenshot(dvt=dvt_service)
        logger.info("DVT Screenshot 创建成功")
        
        # 获取截图
        start_time = time.time()
        screenshot_data = screenshot.get_screenshot()
        duration = time.time() - start_time
        
        if screenshot_data:
            logger.success(f"DVT Screenshot 截图成功，耗时: {duration:.3f}秒，数据大小: {len(screenshot_data)} bytes")
            
            # 保存截图
            image = Image.open(io.BytesIO(screenshot_data))
            # 确保resources目录存在
            resources_dir = Path(__file__).parent / "resources"
            resources_dir.mkdir(exist_ok=True)
            image.save(resources_dir / "test_dvt_screenshot.png")
            logger.info(f"截图已保存，尺寸: {image.width}x{image.height}")
            return True
        else:
            logger.error("DVT Screenshot 截图失败：数据为空")
            return False
            
    except Exception as e:
        logger.error(f"DVT Screenshot 测试失败: {e}")
        logger.error(f"异常类型: {type(e).__name__}")
        import traceback
        logger.debug(f"完整异常堆栈:\n{traceback.format_exc()}")
        return False

def main():
    """主函数"""
    logger.info("开始测试不同的截图方法")
    
    # 测试传统方法
    result1 = test_screenshot_service()
    
    print("\n" + "="*50 + "\n")
    
    # 测试 DVT 方法
    result2 = test_dvt_screenshot()
    
    print("\n" + "="*50 + "\n")
    
    # 总结
    logger.info("=== 测试结果总结 ===")
    logger.info(f"ScreenshotService: {'成功' if result1 else '失败'}")
    logger.info(f"DVT Screenshot: {'成功' if result2 else '失败'}")
    
    if result2 and not result1:
        logger.success("DVT Screenshot 方法可用，建议切换到此方法")
    elif result1 and not result2:
        logger.info("ScreenshotService 方法可用")
    elif result1 and result2:
        logger.success("两种方法都可用")
    else:
        logger.error("两种方法都失败")

if __name__ == "__main__":
    main()