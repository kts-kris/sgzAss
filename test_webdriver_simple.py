#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的WebDriverAgent测试脚本

这是一个最简化的测试脚本，用于验证WebDriverAgent是否正常工作。
使用前请确保已完成环境设置。
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.webdriver_controller import WebDriverController
from loguru import logger


def simple_test():
    """
    简单的WebDriverAgent功能测试
    """
    logger.info("=== WebDriverAgent简单测试 ===")
    
    # 配置（请根据实际情况修改UDID）
    config = {
        "udid": "请替换为你的设备UDID",  # 使用 idevice_id -l 获取
        "bundle_id": "com.apple.springboard",  # 主屏幕
        "server_url": "http://localhost:4723",
        "device_name": "iPad",
        "platform_version": "17.0"  # 根据你的iOS版本调整
    }
    
    # 检查配置
    if config["udid"] == "请替换为你的设备UDID":
        logger.error("请先在配置中设置正确的设备UDID")
        logger.info("获取设备UDID的方法:")
        logger.info("1. 连接iPad到Mac")
        logger.info("2. 运行命令: idevice_id -l")
        logger.info("3. 复制显示的UDID到配置中")
        return False
    
    try:
        logger.info(f"正在连接设备: {config['udid'][:8]}...")
        
        # 创建控制器并连接
        with WebDriverController(config) as controller:
            logger.info("设备连接成功！")
            
            # 测试1: 获取屏幕尺寸
            logger.info("\n--- 测试1: 获取屏幕尺寸 ---")
            size = controller.get_window_size()
            if size:
                logger.info(f"屏幕尺寸: {size[0]} x {size[1]} 像素")
            else:
                logger.error("获取屏幕尺寸失败")
                return False
            
            # 测试2: 获取截图
            logger.info("\n--- 测试2: 获取截图 ---")
            screenshot = controller.get_screenshot()
            if screenshot:
                # 保存截图
                screenshot_path = "test_screenshot.png"
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot)
                logger.info(f"截图已保存: {screenshot_path}")
            else:
                logger.error("获取截图失败")
                return False
            
            # 测试3: 点击操作
            logger.info("\n--- 测试3: 点击操作 ---")
            center_x, center_y = size[0] // 2, size[1] // 2
            logger.info(f"点击屏幕中心: ({center_x}, {center_y})")
            
            success = controller.tap(center_x, center_y)
            if success:
                logger.info("点击操作成功")
                time.sleep(1)  # 等待响应
            else:
                logger.error("点击操作失败")
                return False
            
            # 测试4: 滑动操作
            logger.info("\n--- 测试4: 滑动操作 ---")
            start_x, start_y = size[0] // 2, size[1] * 3 // 4
            end_x, end_y = size[0] // 2, size[1] // 4
            
            logger.info(f"向上滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            success = controller.swipe(start_x, start_y, end_x, end_y, 500)
            if success:
                logger.info("滑动操作成功")
                time.sleep(1)  # 等待响应
            else:
                logger.error("滑动操作失败")
                return False
            
            # 测试5: 长按操作
            logger.info("\n--- 测试5: 长按操作 ---")
            logger.info(f"长按屏幕中心: ({center_x}, {center_y})")
            
            success = controller.long_press(center_x, center_y, 1000)
            if success:
                logger.info("长按操作成功")
                time.sleep(1)  # 等待响应
            else:
                logger.error("长按操作失败")
                return False
            
            # 测试6: Home键
            logger.info("\n--- 测试6: Home键操作 ---")
            success = controller.home_button()
            if success:
                logger.info("Home键操作成功")
                time.sleep(1)  # 等待响应
            else:
                logger.warning("Home键操作失败（某些iOS版本可能不支持）")
            
            logger.info("\n🎉 所有测试完成！WebDriverAgent工作正常")
            return True
            
    except ConnectionError as e:
        logger.error(f"设备连接失败: {e}")
        logger.info("\n故障排除建议:")
        logger.info("1. 确保iPad已连接并信任此电脑")
        logger.info("2. 确保Appium服务器正在运行: appium")
        logger.info("3. 检查设备UDID是否正确: idevice_id -l")
        logger.info("4. 尝试重启Appium服务器")
        return False
        
    except Exception as e:
        logger.exception(f"测试过程中出错: {e}")
        return False


def check_prerequisites():
    """
    检查前置条件
    """
    logger.info("=== 检查前置条件 ===")
    
    import subprocess
    
    # 检查Appium
    try:
        result = subprocess.run(["appium", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info(f"✓ Appium: {result.stdout.strip()}")
        else:
            logger.error("✗ Appium未安装")
            return False
    except Exception:
        logger.error("✗ Appium未安装或无法运行")
        logger.info("安装方法: npm install -g appium")
        return False
    
    # 检查XCUITest驱动
    try:
        result = subprocess.run(["appium", "driver", "list", "--installed"], capture_output=True, text=True, timeout=10)
        if "xcuitest" in result.stdout:
            logger.info("✓ XCUITest驱动已安装")
        else:
            logger.error("✗ XCUITest驱动未安装")
            logger.info("安装方法: appium driver install xcuitest")
            return False
    except Exception:
        logger.warning("⚠ 无法检查XCUITest驱动状态")
    
    # 检查设备连接
    try:
        result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            devices = result.stdout.strip().split('\n')
            logger.info(f"✓ 发现设备: {len(devices)} 个")
            for i, device in enumerate(devices, 1):
                logger.info(f"  设备{i}: {device}")
        else:
            logger.warning("⚠ 未发现连接的设备")
            logger.info("请确保iPad已连接并信任此电脑")
    except Exception:
        logger.error("✗ libimobiledevice未安装")
        logger.info("安装方法: brew install libimobiledevice")
        return False
    
    # 检查Appium服务器
    try:
        result = subprocess.run(["curl", "-s", "http://localhost:4723/status"], capture_output=True, timeout=5)
        if result.returncode == 0:
            logger.info("✓ Appium服务器正在运行")
        else:
            logger.warning("⚠ Appium服务器未运行")
            logger.info("启动方法: appium")
    except Exception:
        logger.warning("⚠ 无法检查Appium服务器状态")
    
    return True


def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    logger.info("WebDriverAgent简单测试脚本")
    logger.info("=" * 50)
    
    # 检查前置条件
    if not check_prerequisites():
        logger.error("前置条件检查失败")
        logger.info("\n请先运行安装脚本: python scripts/setup_webdriver.py")
        sys.exit(1)
    
    # 运行测试
    try:
        success = simple_test()
        
        if success:
            logger.info("\n🎉 测试成功！")
            logger.info("现在您可以使用WebDriverAgent进行iPad自动化控制了")
            logger.info("\n下一步:")
            logger.info("1. 查看完整示例: python examples/webdriver_integration_example.py")
            logger.info("2. 阅读详细指南: WebDriverAgent快速开始指南.md")
            logger.info("3. 使用模板制作工具创建自动化脚本")
        else:
            logger.error("\n❌ 测试失败")
            logger.info("请检查错误信息并参考故障排除指南")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n用户中断测试")
    except Exception as e:
        logger.exception(f"测试过程中出现未预期的错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()