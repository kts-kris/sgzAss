#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WebDriverAgent控制器模块

基于Appium和WebDriverAgent实现真正的iPad触控自动化操作。
这是对DeviceConnector的扩展，提供更强大的自动化控制能力。
"""

import time
import subprocess
from loguru import logger
from typing import Optional, Tuple, List

try:
    from appium import webdriver
    from appium.options.ios import XCUITestOptions
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False
    logger.warning("Appium未安装，WebDriverAgent功能将不可用")


class WebDriverController:
    """WebDriverAgent控制器类"""
    
    def __init__(self, config: dict):
        """
        初始化WebDriverAgent控制器
        
        Args:
            config: 配置字典，包含以下键值：
                - udid: 设备UDID
                - bundle_id: 目标应用Bundle ID
                - server_url: Appium服务器地址
                - device_name: 设备名称
                - platform_version: iOS版本
        """
        if not APPIUM_AVAILABLE:
            raise ImportError("Appium未安装，请先安装: pip install Appium-Python-Client")
        
        self.config = config
        self.driver: Optional[webdriver.Remote] = None
        self.connected = False
        
        # 默认配置
        self.server_url = config.get("server_url", "http://localhost:4723")
        self.udid = config.get("udid")
        self.bundle_id = config.get("bundle_id", "com.apple.springboard")
        self.device_name = config.get("device_name", "iPad")
        self.platform_version = config.get("platform_version", "17.0")
        
        # 超时设置
        self.implicit_wait = config.get("implicit_wait", 10)
        self.explicit_wait = config.get("explicit_wait", 30)
    
    def start_appium_server(self) -> bool:
        """
        启动Appium服务器
        
        Returns:
            bool: 启动是否成功
        """
        try:
            # 检查Appium是否已运行
            result = subprocess.run(
                ["curl", "-s", f"{self.server_url}/status"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("Appium服务器已在运行")
                return True
            
            # 启动Appium服务器
            logger.info("正在启动Appium服务器...")
            subprocess.Popen(["appium"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 等待服务器启动
            for _ in range(30):  # 最多等待30秒
                time.sleep(1)
                try:
                    result = subprocess.run(
                        ["curl", "-s", f"{self.server_url}/status"],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        logger.info("Appium服务器启动成功")
                        return True
                except:
                    continue
            
            logger.error("Appium服务器启动超时")
            return False
            
        except Exception as e:
            logger.exception(f"启动Appium服务器失败: {e}")
            return False
    
    def connect(self) -> bool:
        """
        连接到iPad设备
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if not self.udid:
                logger.error("设备UDID未配置")
                return False
            
            # 确保Appium服务器运行
            if not self.start_appium_server():
                return False
            
            # 配置连接选项
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = self.device_name
            options.platform_version = self.platform_version
            options.udid = self.udid
            options.bundle_id = self.bundle_id
            options.automation_name = "XCUITest"
            
            # 性能优化选项
            options.new_command_timeout = 300
            options.no_reset = True
            options.full_reset = False
            options.skip_log_capture = True
            
            # WebDriverAgent相关选项
            options.use_new_wda = False
            options.wda_launch_timeout = 60000
            options.wda_connection_timeout = 60000
            
            logger.info(f"正在连接设备 {self.udid}...")
            
            # 创建WebDriver实例
            self.driver = webdriver.Remote(
                command_executor=self.server_url,
                options=options
            )
            
            # 设置超时
            self.driver.implicitly_wait(self.implicit_wait)
            
            # 验证连接
            window_size = self.driver.get_window_size()
            logger.info(f"设备连接成功，屏幕尺寸: {window_size['width']}x{window_size['height']}")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.exception(f"连接设备失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开设备连接"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.connected = False
            logger.info("设备连接已断开")
        except Exception as e:
            logger.exception(f"断开连接时出错: {e}")
    
    def tap(self, x: int, y: int) -> bool:
        """
        在指定坐标执行点击操作
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return False
        
        try:
            self.driver.tap([(x, y)])
            logger.debug(f"点击坐标 ({x}, {y}) 成功")
            return True
        except Exception as e:
            logger.exception(f"点击操作失败: {e}")
            return False
    
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
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return False
        
        try:
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            logger.debug(f"滑动操作成功: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            return True
        except Exception as e:
            logger.exception(f"滑动操作失败: {e}")
            return False
    
    def long_press(self, x: int, y: int, duration: int = 1000) -> bool:
        """
        执行长按操作
        
        Args:
            x: 横坐标
            y: 纵坐标
            duration: 长按持续时间（毫秒）
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return False
        
        try:
            from appium.webdriver.common.touch_action import TouchAction
            
            action = TouchAction(self.driver)
            action.long_press(x=x, y=y, duration=duration).release().perform()
            logger.debug(f"长按操作成功: ({x}, {y}), 持续时间: {duration}ms")
            return True
        except Exception as e:
            logger.exception(f"长按操作失败: {e}")
            return False
    
    def multi_touch(self, touches: List[Tuple[int, int]], duration: int = 500) -> bool:
        """
        执行多点触控操作
        
        Args:
            touches: 触控点列表，每个元素为(x, y)坐标
            duration: 触控持续时间（毫秒）
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return False
        
        try:
            from appium.webdriver.common.multi_action import MultiAction
            from appium.webdriver.common.touch_action import TouchAction
            
            multi_action = MultiAction(self.driver)
            
            for x, y in touches:
                action = TouchAction(self.driver)
                action.press(x=x, y=y).wait(duration).release()
                multi_action.add(action)
            
            multi_action.perform()
            logger.debug(f"多点触控操作成功: {touches}")
            return True
        except Exception as e:
            logger.exception(f"多点触控操作失败: {e}")
            return False
    
    def find_element_by_image(self, template_path: str, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        通过图像模板查找元素
        
        Args:
            template_path: 模板图像路径
            threshold: 匹配阈值
            
        Returns:
            Optional[Tuple[int, int]]: 找到的元素中心坐标，未找到返回None
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return None
        
        try:
            # 获取当前屏幕截图
            screenshot = self.driver.get_screenshot_as_png()
            
            # 使用OpenCV进行模板匹配
            import cv2
            import numpy as np
            from PIL import Image
            import io
            
            # 转换截图为OpenCV格式
            screenshot_image = Image.open(io.BytesIO(screenshot))
            screenshot_cv = cv2.cvtColor(np.array(screenshot_image), cv2.COLOR_RGB2BGR)
            
            # 读取模板图像
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"无法读取模板图像: {template_path}")
                return None
            
            # 执行模板匹配
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 计算匹配区域的中心点
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                logger.debug(f"找到匹配元素: ({center_x}, {center_y}), 匹配度: {max_val:.3f}")
                return (center_x, center_y)
            else:
                logger.debug(f"未找到匹配元素，最高匹配度: {max_val:.3f}")
                return None
                
        except Exception as e:
            logger.exception(f"图像匹配失败: {e}")
            return None
    
    def wait_for_element_by_image(self, template_path: str, timeout: int = 30, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        等待图像元素出现
        
        Args:
            template_path: 模板图像路径
            timeout: 超时时间（秒）
            threshold: 匹配阈值
            
        Returns:
            Optional[Tuple[int, int]]: 找到的元素中心坐标，超时返回None
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.find_element_by_image(template_path, threshold)
            if result:
                return result
            time.sleep(0.5)
        
        logger.warning(f"等待图像元素超时: {template_path}")
        return None
    
    def tap_image(self, template_path: str, threshold: float = 0.8, timeout: int = 10) -> bool:
        """
        查找并点击图像元素
        
        Args:
            template_path: 模板图像路径
            threshold: 匹配阈值
            timeout: 超时时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        position = self.wait_for_element_by_image(template_path, timeout, threshold)
        if position:
            return self.tap(position[0], position[1])
        else:
            logger.error(f"未找到图像元素，无法点击: {template_path}")
            return False
    
    def get_screenshot(self) -> Optional[bytes]:
        """
        获取屏幕截图
        
        Returns:
            Optional[bytes]: 截图数据（PNG格式），失败返回None
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return None
        
        try:
            screenshot = self.driver.get_screenshot_as_png()
            logger.debug("获取截图成功")
            return screenshot
        except Exception as e:
            logger.exception(f"获取截图失败: {e}")
            return None
    
    def get_window_size(self) -> Optional[Tuple[int, int]]:
        """
        获取屏幕尺寸
        
        Returns:
            Optional[Tuple[int, int]]: (宽度, 高度)，失败返回None
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return None
        
        try:
            size = self.driver.get_window_size()
            return (size['width'], size['height'])
        except Exception as e:
            logger.exception(f"获取屏幕尺寸失败: {e}")
            return None
    
    def launch_app(self, bundle_id: str) -> bool:
        """
        启动应用
        
        Args:
            bundle_id: 应用Bundle ID
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return False
        
        try:
            self.driver.activate_app(bundle_id)
            logger.info(f"启动应用成功: {bundle_id}")
            return True
        except Exception as e:
            logger.exception(f"启动应用失败: {e}")
            return False
    
    def close_app(self, bundle_id: str) -> bool:
        """
        关闭应用
        
        Args:
            bundle_id: 应用Bundle ID
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return False
        
        try:
            self.driver.terminate_app(bundle_id)
            logger.info(f"关闭应用成功: {bundle_id}")
            return True
        except Exception as e:
            logger.exception(f"关闭应用失败: {e}")
            return False
    
    def home_button(self) -> bool:
        """
        按下Home键
        
        Returns:
            bool: 操作是否成功
        """
        if not self.connected or not self.driver:
            logger.error("设备未连接")
            return False
        
        try:
            self.driver.press_keycode(3)  # Home键
            logger.debug("按下Home键成功")
            return True
        except Exception as e:
            logger.exception(f"按下Home键失败: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        if self.connect():
            return self
        else:
            raise ConnectionError("无法连接到设备")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


# 使用示例
if __name__ == "__main__":
    # 配置
    config = {
        "udid": "你的设备UDID",
        "bundle_id": "com.apple.Preferences",
        "server_url": "http://localhost:4723",
        "device_name": "iPad",
        "platform_version": "17.0"
    }
    
    # 使用上下文管理器
    try:
        with WebDriverController(config) as controller:
            # 获取屏幕尺寸
            size = controller.get_window_size()
            print(f"屏幕尺寸: {size}")
            
            # 执行点击
            controller.tap(500, 300)
            
            # 执行滑动
            controller.swipe(100, 100, 200, 200, 500)
            
            # 查找并点击图像
            controller.tap_image("resources/templates/settings_icon.png")
            
    except Exception as e:
        logger.exception(f"操作失败: {e}")