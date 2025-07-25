#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WebDriverAgent集成示例

展示如何在现有项目中集成WebDriverAgent实现真正的iPad自动化控制。
这个示例演示了如何结合使用DeviceConnector和WebDriverController。
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.device_connector import DeviceConnector
from core.webdriver_controller import WebDriverController
from loguru import logger


class EnhancedDeviceController:
    """
    增强的设备控制器
    
    结合DeviceConnector的截图功能和WebDriverController的触控功能，
    提供完整的iPad自动化解决方案。
    """
    
    def __init__(self, config: dict):
        """
        初始化增强设备控制器
        
        Args:
            config: 配置字典，包含设备连接和WebDriver配置
        """
        self.config = config
        
        # 初始化DeviceConnector（用于截图）
        self.device_connector = DeviceConnector(
            connection_type=config.get("connection_type", "usb"),
            device_ip=config.get("device_ip"),
            device_port=config.get("device_port", 8100)
        )
        
        # 初始化WebDriverController（用于触控）
        webdriver_config = {
            "udid": config.get("udid"),
            "bundle_id": config.get("bundle_id", "com.apple.springboard"),
            "server_url": config.get("server_url", "http://localhost:4723"),
            "device_name": config.get("device_name", "iPad"),
            "platform_version": config.get("platform_version", "17.0")
        }
        
        self.webdriver_controller = WebDriverController(webdriver_config)
        
        self.connected = False
    
    def connect(self) -> bool:
        """
        连接到设备
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 连接DeviceConnector（用于截图）
            if not self.device_connector.connect():
                logger.error("DeviceConnector连接失败")
                return False
            
            # 连接WebDriverController（用于触控）
            if not self.webdriver_controller.connect():
                logger.error("WebDriverController连接失败")
                self.device_connector.disconnect()
                return False
            
            self.connected = True
            logger.info("设备连接成功")
            return True
            
        except Exception as e:
            logger.exception(f"设备连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开设备连接"""
        try:
            if hasattr(self, 'webdriver_controller'):
                self.webdriver_controller.disconnect()
            if hasattr(self, 'device_connector'):
                self.device_connector.disconnect()
            self.connected = False
            logger.info("设备连接已断开")
        except Exception as e:
            logger.exception(f"断开连接时出错: {e}")
    
    def get_screenshot(self):
        """
        获取屏幕截图
        
        Returns:
            numpy.ndarray: 截图数组
        """
        if not self.connected:
            logger.error("设备未连接")
            return None
        
        return self.device_connector.get_screenshot()
    
    def tap(self, x: int, y: int) -> bool:
        """
        在指定坐标执行点击操作
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected:
            logger.error("设备未连接")
            return False
        
        return self.webdriver_controller.tap(x, y)
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500) -> bool:
        """
        执行滑动操作
        
        Args:
            start_x: 起始横坐标
            start_y: 起始纵坐标
            end_x: 结束横坐标
            end_y: 结束纵坐标
            duration: 滑动持续时间（毫秒）
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected:
            logger.error("设备未连接")
            return False
        
        return self.webdriver_controller.swipe(start_x, start_y, end_x, end_y, duration)
    
    def find_and_tap_template(self, template_path: str, threshold: float = 0.8, timeout: int = 10) -> bool:
        """
        查找模板并点击
        
        Args:
            template_path: 模板图像路径
            threshold: 匹配阈值
            timeout: 超时时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected:
            logger.error("设备未连接")
            return False
        
        # 使用WebDriverController的图像匹配功能
        return self.webdriver_controller.tap_image(template_path, threshold, timeout)
    
    def launch_app(self, bundle_id: str) -> bool:
        """
        启动应用
        
        Args:
            bundle_id: 应用Bundle ID
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected:
            logger.error("设备未连接")
            return False
        
        return self.webdriver_controller.launch_app(bundle_id)
    
    def __enter__(self):
        """上下文管理器入口"""
        if self.connect():
            return self
        else:
            raise ConnectionError("无法连接到设备")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


def demo_basic_operations():
    """
    演示基本操作
    """
    logger.info("=== 基本操作演示 ===")
    
    # 配置（请根据实际情况修改）
    config = {
        "connection_type": "usb",
        "udid": "你的设备UDID",  # 使用 idevice_id -l 获取
        "bundle_id": "com.apple.Preferences",
        "server_url": "http://localhost:4723",
        "device_name": "iPad",
        "platform_version": "17.0"
    }
    
    try:
        with EnhancedDeviceController(config) as controller:
            # 获取截图
            screenshot = controller.get_screenshot()
            if screenshot is not None:
                logger.info(f"获取截图成功，尺寸: {screenshot.shape}")
            
            # 点击屏幕中心
            if screenshot is not None:
                height, width = screenshot.shape[:2]
                center_x, center_y = width // 2, height // 2
                
                logger.info(f"点击屏幕中心: ({center_x}, {center_y})")
                controller.tap(center_x, center_y)
                time.sleep(1)
            
            # 执行滑动操作
            logger.info("执行向上滑动")
            controller.swipe(500, 800, 500, 400, 500)
            time.sleep(1)
            
            # 启动设置应用
            logger.info("启动设置应用")
            controller.launch_app("com.apple.Preferences")
            time.sleep(2)
            
    except Exception as e:
        logger.exception(f"演示失败: {e}")


def demo_template_matching():
    """
    演示模板匹配功能
    """
    logger.info("=== 模板匹配演示 ===")
    
    config = {
        "connection_type": "usb",
        "udid": "你的设备UDID",
        "bundle_id": "com.apple.springboard",
        "server_url": "http://localhost:4723",
        "device_name": "iPad",
        "platform_version": "17.0"
    }
    
    try:
        with EnhancedDeviceController(config) as controller:
            # 确保模板文件存在
            template_path = "resources/templates/settings_icon.png"
            
            if os.path.exists(template_path):
                logger.info(f"查找并点击模板: {template_path}")
                success = controller.find_and_tap_template(template_path, threshold=0.8, timeout=10)
                
                if success:
                    logger.info("模板匹配并点击成功")
                else:
                    logger.warning("模板匹配失败")
            else:
                logger.warning(f"模板文件不存在: {template_path}")
                logger.info("请先使用模板制作工具创建模板")
            
    except Exception as e:
        logger.exception(f"模板匹配演示失败: {e}")


def demo_automation_workflow():
    """
    演示自动化工作流程
    """
    logger.info("=== 自动化工作流程演示 ===")
    
    config = {
        "connection_type": "usb",
        "udid": "你的设备UDID",
        "bundle_id": "com.apple.springboard",
        "server_url": "http://localhost:4723",
        "device_name": "iPad",
        "platform_version": "17.0"
    }
    
    try:
        with EnhancedDeviceController(config) as controller:
            # 工作流程：打开设置 -> 查找Wi-Fi -> 点击Wi-Fi
            
            # 1. 启动设置应用
            logger.info("步骤1: 启动设置应用")
            controller.launch_app("com.apple.Preferences")
            time.sleep(3)
            
            # 2. 获取当前截图
            logger.info("步骤2: 获取当前截图")
            screenshot = controller.get_screenshot()
            if screenshot is not None:
                logger.info(f"截图获取成功，尺寸: {screenshot.shape}")
            
            # 3. 查找并点击Wi-Fi设置（如果有对应模板）
            wifi_template = "resources/templates/wifi_setting.png"
            if os.path.exists(wifi_template):
                logger.info("步骤3: 查找并点击Wi-Fi设置")
                success = controller.find_and_tap_template(wifi_template, threshold=0.8, timeout=5)
                if success:
                    logger.info("Wi-Fi设置点击成功")
                    time.sleep(2)
                else:
                    logger.warning("未找到Wi-Fi设置")
            else:
                logger.info("步骤3: Wi-Fi模板不存在，执行模拟点击")
                # 模拟点击Wi-Fi设置位置（根据实际情况调整坐标）
                controller.tap(200, 300)
                time.sleep(2)
            
            # 4. 返回主屏幕
            logger.info("步骤4: 返回主屏幕")
            controller.webdriver_controller.home_button()
            time.sleep(1)
            
            logger.info("自动化工作流程完成")
            
    except Exception as e:
        logger.exception(f"自动化工作流程失败: {e}")


def check_prerequisites():
    """
    检查前置条件
    """
    logger.info("=== 检查前置条件 ===")
    
    # 检查Appium是否安装
    try:
        import subprocess
        result = subprocess.run(["appium", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info(f"Appium已安装，版本: {result.stdout.strip()}")
        else:
            logger.error("Appium未安装或无法运行")
            return False
    except Exception as e:
        logger.error(f"检查Appium失败: {e}")
        logger.info("请安装Appium: npm install -g appium")
        return False
    
    # 检查WebDriverAgent驱动
    try:
        result = subprocess.run(["appium", "driver", "list", "--installed"], capture_output=True, text=True, timeout=10)
        if "xcuitest" in result.stdout:
            logger.info("XCUITest驱动已安装")
        else:
            logger.warning("XCUITest驱动未安装")
            logger.info("请安装XCUITest驱动: appium driver install xcuitest")
    except Exception as e:
        logger.warning(f"检查XCUITest驱动失败: {e}")
    
    # 检查设备连接
    try:
        result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            devices = result.stdout.strip().split('\n')
            logger.info(f"发现设备: {devices}")
            logger.info(f"请在配置中使用设备UDID: {devices[0]}")
        else:
            logger.warning("未发现连接的设备")
            logger.info("请确保设备已连接并信任此电脑")
    except Exception as e:
        logger.warning(f"检查设备连接失败: {e}")
        logger.info("请安装libimobiledevice: brew install libimobiledevice")
    
    return True


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    # 检查前置条件
    if not check_prerequisites():
        logger.error("前置条件检查失败，请先安装必要的工具")
        sys.exit(1)
    
    # 运行演示
    try:
        logger.info("开始WebDriverAgent集成演示")
        
        # 基本操作演示
        demo_basic_operations()
        
        # 模板匹配演示
        demo_template_matching()
        
        # 自动化工作流程演示
        demo_automation_workflow()
        
        logger.info("演示完成")
        
    except KeyboardInterrupt:
        logger.info("用户中断演示")
    except Exception as e:
        logger.exception(f"演示过程中出错: {e}")