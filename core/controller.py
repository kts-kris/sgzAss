#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
游戏控制器模块

负责协调设备连接器和视觉系统，实现游戏操作的高级控制。
提供了一系列游戏操作的封装方法，如点击元素、滑动屏幕、执行特定游戏操作等。
"""

import os
import time
import random
import numpy as np
from loguru import logger
from config import SCREENSHOT_DIR


class GameController:
    """游戏控制器类，负责协调设备连接器和视觉系统，实现游戏操作"""
    
    def __init__(self, device, vision, game_settings, dry_run=False):
        """初始化游戏控制器
        
        Args:
            device: 设备连接器实例
            vision: 视觉系统实例
            game_settings: 游戏设置
            dry_run: 是否为演示模式（不执行实际操作）
        """
        self.device = device
        self.vision = vision
        self.settings = game_settings
        self.dry_run = dry_run
        
        # 操作延迟范围
        self.action_delay_min = game_settings.get("action_delay_min", 0.5)
        self.action_delay_max = game_settings.get("action_delay_max", 1.5)
        
        # 截图间隔
        self.screenshot_interval = game_settings.get("screenshot_interval", 1.0)
        
        # 重试设置
        self.max_retries = game_settings.get("max_retries", 3)
        self.retry_delay = game_settings.get("retry_delay", 2.0)
        
        # 安全设置
        self.enable_safe_mode = game_settings.get("enable_safe_mode", True)
        self.max_continuous_actions = game_settings.get("max_continuous_actions", 50)
        self.pause_duration = game_settings.get("pause_duration", 30)
        
        # 状态变量
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.continuous_action_count = 0
        self.last_screen_analysis = None
    
    def get_screenshot(self, force=False):
        """获取屏幕截图
        
        Args:
            force: 是否强制获取新截图，忽略截图间隔
            
        Returns:
            numpy.ndarray: 屏幕截图图像数据
        """
        current_time = time.time()
        
        # 如果距离上次截图时间不足截图间隔，且不是强制获取，则返回上次的截图
        if not force and self.last_screenshot is not None and \
           current_time - self.last_screenshot_time < self.screenshot_interval:
            return self.last_screenshot
        
        # 获取新截图
        screenshot = self.device.get_screenshot()
        
        if screenshot is None:
            logger.error("获取截图失败")
            return None
        
        # 更新状态
        self.last_screenshot = screenshot
        self.last_screenshot_time = current_time
        
        # 保存截图（用于调试）
        if self.enable_safe_mode:
            self._save_debug_screenshot(screenshot)
        
        return screenshot
    
    def _save_debug_screenshot(self, image):
        """保存调试用截图
        
        Args:
            image: 要保存的图像
        """
        try:
            # 确保目录存在
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            
            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            
            # 保存图像
            import cv2
            cv2.imwrite(filepath, image)
            logger.debug(f"已保存调试截图: {filepath}")
            
        except Exception as e:
            logger.exception(f"保存调试截图失败: {e}")
    
    def analyze_screen(self, force=False):
        """分析当前屏幕
        
        Args:
            force: 是否强制获取新截图
            
        Returns:
            dict: 屏幕分析结果
        """
        # 获取截图
        screenshot = self.get_screenshot(force=force)
        if screenshot is None:
            return None
        
        # 分析屏幕
        analysis = self.vision.analyze_screen(screenshot)
        self.last_screen_analysis = analysis
        
        return analysis
    
    def find_element(self, element_type, force=False):
        """查找指定类型的元素
        
        Args:
            element_type: 元素类型
            force: 是否强制获取新截图
            
        Returns:
            dict: 元素信息，如果未找到则返回None
        """
        # 分析屏幕
        analysis = self.analyze_screen(force=force)
        if not analysis:
            return None
        
        # 查找指定类型的元素
        for element in analysis["elements"]:
            if element["type"] == element_type:
                return element
        
        return None
    
    def find_all_elements(self, element_type, force=False):
        """查找所有指定类型的元素
        
        Args:
            element_type: 元素类型
            force: 是否强制获取新截图
            
        Returns:
            list: 元素列表
        """
        # 分析屏幕
        analysis = self.analyze_screen(force=force)
        if not analysis:
            return []
        
        # 查找所有指定类型的元素
        elements = []
        for element in analysis["elements"]:
            if element["type"] == element_type:
                elements.append(element)
        
        return elements
    
    def tap_element(self, element_or_type, retry=True):
        """点击指定元素
        
        Args:
            element_or_type: 元素对象或元素类型
            retry: 是否在失败时重试
            
        Returns:
            bool: 操作是否成功
        """
        # 安全检查
        if self._should_pause():
            return False
        
        # 如果传入的是元素类型，先查找元素
        if isinstance(element_or_type, str):
            element = self.find_element(element_or_type, force=True)
            if not element:
                logger.warning(f"未找到元素: {element_or_type}")
                return False
        else:
            element = element_or_type
        
        # 获取元素位置
        x, y, width, height = element["position"]
        
        # 计算点击位置（元素中心点附近的随机位置）
        center_x = x + width // 2
        center_y = y + height // 2
        
        # 添加随机偏移，模拟人类操作
        offset_x = random.randint(-width // 4, width // 4)
        offset_y = random.randint(-height // 4, height // 4)
        
        tap_x = center_x + offset_x
        tap_y = center_y + offset_y
        
        # 执行点击
        logger.debug(f"点击元素 {element['type']} 位置: ({tap_x}, {tap_y})")
        
        if self.dry_run:
            logger.info(f"[演示模式] 点击元素 {element['type']} 位置: ({tap_x}, {tap_y})")
            success = True
        else:
            success = self.device.tap(tap_x, tap_y)
        
        # 增加操作计数
        self.continuous_action_count += 1
        
        # 随机延迟，模拟人类操作
        self._random_delay()
        
        # 如果失败且需要重试，则重试操作
        if not success and retry:
            return self._retry_operation(lambda: self.tap_element(element_or_type, retry=False))
        
        return success
    
    def tap_position(self, x, y, retry=True):
        """点击指定位置
        
        Args:
            x: 横坐标
            y: 纵坐标
            retry: 是否在失败时重试
            
        Returns:
            bool: 操作是否成功
        """
        # 安全检查
        if self._should_pause():
            return False
        
        # 执行点击
        logger.debug(f"点击位置: ({x}, {y})")
        
        if self.dry_run:
            logger.info(f"[演示模式] 点击位置: ({x}, {y})")
            success = True
        else:
            success = self.device.tap(x, y)
        
        # 增加操作计数
        self.continuous_action_count += 1
        
        # 随机延迟，模拟人类操作
        self._random_delay()
        
        # 如果失败且需要重试，则重试操作
        if not success and retry:
            return self._retry_operation(lambda: self.tap_position(x, y, retry=False))
        
        return success
    
    def swipe(self, start_x, start_y, end_x, end_y, duration=None, retry=True):
        """滑动屏幕
        
        Args:
            start_x: 起始横坐标
            start_y: 起始纵坐标
            end_x: 结束横坐标
            end_y: 结束纵坐标
            duration: 滑动持续时间（秒），如果为None则使用随机时间
            retry: 是否在失败时重试
            
        Returns:
            bool: 操作是否成功
        """
        # 安全检查
        if self._should_pause():
            return False
        
        # 如果未指定持续时间，使用随机时间
        if duration is None:
            duration = random.uniform(0.3, 0.8)
        
        # 执行滑动
        logger.debug(f"滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y}), 持续时间: {duration:.2f}秒")
        
        if self.dry_run:
            logger.info(f"[演示模式] 滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y}), 持续时间: {duration:.2f}秒")
            success = True
        else:
            success = self.device.swipe(start_x, start_y, end_x, end_y, duration)
        
        # 增加操作计数
        self.continuous_action_count += 1
        
        # 随机延迟，模拟人类操作
        self._random_delay()
        
        # 如果失败且需要重试，则重试操作
        if not success and retry:
            return self._retry_operation(lambda: self.swipe(start_x, start_y, end_x, end_y, duration, retry=False))
        
        return success
    
    def wait_for_element(self, element_type, timeout=10, check_interval=1.0):
        """等待指定元素出现
        
        Args:
            element_type: 元素类型
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            
        Returns:
            dict: 元素信息，如果超时则返回None
        """
        logger.debug(f"等待元素出现: {element_type}, 超时时间: {timeout}秒")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 查找元素
            element = self.find_element(element_type, force=True)
            if element:
                logger.debug(f"元素已出现: {element_type}")
                return element
            
            # 等待一段时间再检查
            time.sleep(check_interval)
        
        logger.warning(f"等待元素超时: {element_type}")
        return None
    
    def _random_delay(self):
        """随机延迟，模拟人类操作"""
        delay = random.uniform(self.action_delay_min, self.action_delay_max)
        time.sleep(delay)
    
    def _retry_operation(self, operation_func):
        """重试操作
        
        Args:
            operation_func: 操作函数
            
        Returns:
            bool: 操作是否最终成功
        """
        for i in range(self.max_retries):
            logger.debug(f"重试操作 {i+1}/{self.max_retries}")
            time.sleep(self.retry_delay)
            
            if operation_func():
                return True
        
        logger.warning(f"操作重试 {self.max_retries} 次后仍然失败")
        return False
    
    def _should_pause(self):
        """检查是否应该暂停操作
        
        Returns:
            bool: 是否应该暂停
        """
        if not self.enable_safe_mode:
            return False
        
        # 检查连续操作次数
        if self.continuous_action_count >= self.max_continuous_actions:
            logger.info(f"已连续执行 {self.continuous_action_count} 次操作，暂停 {self.pause_duration} 秒")
            time.sleep(self.pause_duration)
            self.continuous_action_count = 0
            return False
        
        return False
    
    # 以下是游戏特定操作的封装
    
    def navigate_to_world_map(self):
        """导航到世界地图
        
        Returns:
            bool: 操作是否成功
        """
        # 分析当前屏幕
        analysis = self.analyze_screen(force=True)
        if not analysis:
            return False
        
        # 如果已经在世界地图，直接返回成功
        if analysis["screen_type"] == "world_map":
            logger.debug("已经在世界地图")
            return True
        
        # 如果在主界面，点击世界地图按钮
        if analysis["screen_type"] == "main_menu":
            world_map_button = self.find_element("world_map")
            if world_map_button:
                success = self.tap_element(world_map_button)
                if success:
                    # 等待世界地图加载
                    return self.wait_for_element("world_map") is not None
        
        # 如果在其他界面，尝试返回
        back_button = self.find_element("back_button")
        if back_button:
            self.tap_element(back_button)
            time.sleep(1)
            return self.navigate_to_world_map()
        
        # 尝试点击关闭按钮
        close_button = self.find_element("close_button")
        if close_button:
            self.tap_element(close_button)
            time.sleep(1)
            return self.navigate_to_world_map()
        
        logger.warning("无法导航到世界地图")
        return False
    
    def find_and_occupy_land(self, prefer_resources=True, max_distance=500):
        """查找并占领土地
        
        Args:
            prefer_resources: 是否优先占领资源点
            max_distance: 最大搜索距离（像素）
            
        Returns:
            bool: 操作是否成功
        """
        # 导航到世界地图
        if not self.navigate_to_world_map():
            return False
        
        # 查找可占领的土地
        targets = []
        
        # 如果优先占领资源点，先查找资源点
        if prefer_resources:
            resources = self.find_all_elements("resource_point", force=True)
            targets.extend(resources)
        
        # 查找空闲土地
        empty_lands = self.find_all_elements("empty_land", force=True)
        targets.extend(empty_lands)
        
        if not targets:
            logger.info("未找到可占领的土地或资源点")
            
            # 随机滑动屏幕，寻找新的区域
            screen_width = self.device.screen_width
            screen_height = self.device.screen_height
            
            # 随机选择滑动方向
            directions = ["up", "down", "left", "right"]
            direction = random.choice(directions)
            
            # 根据方向设置滑动参数
            if direction == "up":
                start_x = screen_width // 2
                start_y = screen_height * 3 // 4
                end_x = screen_width // 2
                end_y = screen_height // 4
            elif direction == "down":
                start_x = screen_width // 2
                start_y = screen_height // 4
                end_x = screen_width // 2
                end_y = screen_height * 3 // 4
            elif direction == "left":
                start_x = screen_width * 3 // 4
                start_y = screen_height // 2
                end_x = screen_width // 4
                end_y = screen_height // 2
            else:  # right
                start_x = screen_width // 4
                start_y = screen_height // 2
                end_x = screen_width * 3 // 4
                end_y = screen_height // 2
            
            logger.info(f"滑动屏幕寻找新区域，方向: {direction}")
            self.swipe(start_x, start_y, end_x, end_y)
            
            # 等待屏幕稳定
            time.sleep(1)
            
            # 递归调用自身，继续查找
            return self.find_and_occupy_land(prefer_resources, max_distance)
        
        # 选择一个目标
        target = targets[0]
        target_type = target["type"]
        x, y, width, height = target["position"]
        
        # 点击目标
        logger.info(f"点击{target_type}")
        if not self.tap_element(target):
            return False
        
        # 等待选择部队界面出现
        army_select = self.wait_for_element("army_select")
        if not army_select:
            logger.warning("未出现选择部队界面")
            return False
        
        # 点击选择部队
        if not self.tap_element(army_select):
            return False
        
        # 等待占领按钮出现
        occupy_button = self.wait_for_element("army_occupy")
        if not occupy_button:
            logger.warning("未出现占领按钮")
            return False
        
        # 点击占领按钮
        if not self.tap_element(occupy_button):
            return False
        
        # 等待确认按钮出现
        confirm_button = self.wait_for_element("confirm_button")
        if not confirm_button:
            logger.warning("未出现确认按钮")
            return False
        
        # 点击确认按钮
        if not self.tap_element(confirm_button):
            return False
        
        logger.info(f"成功占领{target_type}")
        return True
    
    def move_idle_army(self, strategy="nearest"):
        """移动空闲部队
        
        Args:
            strategy: 移动策略，可选值：nearest, resources, enemy
            
        Returns:
            bool: 操作是否成功
        """
        # 导航到世界地图
        if not self.navigate_to_world_map():
            return False
        
        # 查找空闲部队
        idle_armies = self.find_all_elements("army_idle", force=True)
        if not idle_armies:
            logger.info("未找到空闲部队")
            return False
        
        # 选择一个空闲部队
        army = idle_armies[0]
        
        # 点击部队
        logger.info("点击空闲部队")
        if not self.tap_element(army):
            return False
        
        # 根据策略选择目标
        if strategy == "resources":
            # 查找资源点
            targets = self.find_all_elements("resource_point", force=True)
            target_type = "资源点"
        elif strategy == "enemy":
            # 查找敌方土地
            targets = self.find_all_elements("enemy_land", force=True)
            target_type = "敌方土地"
        else:  # nearest
            # 查找空闲土地
            targets = self.find_all_elements("empty_land", force=True)
            target_type = "空闲土地"
        
        if not targets:
            logger.info(f"未找到{target_type}")
            
            # 取消选择部队
            cancel_button = self.find_element("cancel_button")
            if cancel_button:
                self.tap_element(cancel_button)
            
            return False
        
        # 选择一个目标
        target = targets[0]
        
        # 点击目标
        logger.info(f"点击{target_type}")
        if not self.tap_element(target):
            return False
        
        # 等待行军按钮出现
        march_button = self.wait_for_element("army_march")
        if not march_button:
            logger.warning("未出现行军按钮")
            return False
        
        # 点击行军按钮
        if not self.tap_element(march_button):
            return False
        
        # 等待确认按钮出现
        confirm_button = self.wait_for_element("confirm_button")
        if not confirm_button:
            logger.warning("未出现确认按钮")
            return False
        
        # 点击确认按钮
        if not self.tap_element(confirm_button):
            return False
        
        logger.info(f"成功派遣部队前往{target_type}")
        return True
    
    def collect_resources(self):
        """收集资源
        
        Returns:
            bool: 操作是否成功
        """
        # 导航到主界面
        if not self.navigate_to_main_menu():
            return False
        
        # 查找资源收集按钮
        collect_button = self.find_element("collect_resources_button", force=True)
        if not collect_button:
            logger.info("未找到资源收集按钮")
            return False
        
        # 点击收集按钮
        logger.info("点击资源收集按钮")
        if not self.tap_element(collect_button):
            return False
        
        # 等待确认按钮出现
        confirm_button = self.wait_for_element("confirm_button")
        if not confirm_button:
            logger.warning("未出现确认按钮")
            return False
        
        # 点击确认按钮
        if not self.tap_element(confirm_button):
            return False
        
        logger.info("成功收集资源")
        return True
    
    def navigate_to_main_menu(self):
        """导航到主界面
        
        Returns:
            bool: 操作是否成功
        """
        # 分析当前屏幕
        analysis = self.analyze_screen(force=True)
        if not analysis:
            return False
        
        # 如果已经在主界面，直接返回成功
        if analysis["screen_type"] == "main_menu":
            logger.debug("已经在主界面")
            return True
        
        # 如果在世界地图，点击返回按钮
        if analysis["screen_type"] == "world_map":
            back_button = self.find_element("back_button")
            if back_button:
                success = self.tap_element(back_button)
                if success:
                    # 等待主界面加载
                    return self.wait_for_element("main_menu") is not None
        
        # 如果在其他界面，尝试返回
        back_button = self.find_element("back_button")
        if back_button:
            self.tap_element(back_button)
            time.sleep(1)
            return self.navigate_to_main_menu()
        
        # 尝试点击关闭按钮
        close_button = self.find_element("close_button")
        if close_button:
            self.tap_element(close_button)
            time.sleep(1)
            return self.navigate_to_main_menu()
        
        logger.warning("无法导航到主界面")
        return False