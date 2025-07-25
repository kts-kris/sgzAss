#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的模板收集工具
用于收集三国志霸业游戏界面的关键模板
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from core.device_connector import DeviceConnector
from loguru import logger

# 需要收集的关键模板
REQUIRED_TEMPLATES = {
    'close_button': '关闭按钮 - 通常是X或关闭图标',
    'back_button': '返回按钮 - 通常是箭头或返回图标',
    'main_menu': '主菜单按钮 - 游戏主界面的菜单按钮',
    'world_map': '世界地图按钮 - 进入世界地图的按钮',
    'confirm_button': '确认按钮 - 确认操作的按钮',
    'cancel_button': '取消按钮 - 取消操作的按钮',
    'land_occupation': '占领土地按钮 - 占领土地的按钮',
    'attack_button': '攻击按钮 - 发起攻击的按钮'
}

class SimpleTemplateCollector:
    def __init__(self):
        # 使用loguru logger
        
        # 设备连接设置
        device_settings = {
            "connection_type": "simulation",
            "device_ip": "",
            "device_port": 5555,
            "screen_width": 2732,
            "screen_height": 2048,
        }
        
        # 初始化设备连接器
        self.device = DeviceConnector(device_settings)
        
        # 模板保存目录
        self.template_dir = Path(__file__).parent.parent / "resources" / "templates"
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前截图
        self.current_screenshot = None
        self.current_template = None
        self.template_index = 0
        
        # 鼠标选择相关
        self.drawing = False
        self.ix, self.iy = -1, -1
    
    def connect_device(self):
        """连接设备"""
        try:
            success = self.device.connect()
            if success:
                logger.info("设备连接成功")
                return True
            else:
                logger.error("设备连接失败")
                return False
        except Exception as e:
            logger.exception(f"连接设备时出错: {e}")
            return False
    
    def take_screenshot(self):
        """获取屏幕截图"""
        try:
            screenshot = self.device.get_screenshot()
            if screenshot is not None:
                self.current_screenshot = screenshot
                logger.info(f"获取截图成功，尺寸: {screenshot.shape[:2]}")
                return True
            else:
                logger.error("获取截图失败")
                return False
        except Exception as e:
            logger.exception(f"获取截图时出错: {e}")
            return False
    
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标回调函数"""
        if self.current_screenshot is None:
            return
        
        # 创建一个副本用于绘制
        img_copy = self.current_screenshot.copy()
        
        # 记录起始点
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
        
        # 绘制矩形
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                cv2.rectangle(img_copy, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
                cv2.imshow("Template Collector", img_copy)
        
        # 完成绘制并保存选区
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            cv2.rectangle(img_copy, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
            cv2.imshow("Template Collector", img_copy)
            
            # 计算矩形坐标
            x1, y1 = min(self.ix, x), min(self.iy, y)
            x2, y2 = max(self.ix, x), max(self.iy, y)
            
            # 检查选区大小
            width = x2 - x1
            height = y2 - y1
            
            if width > 10 and height > 10:  # 最小尺寸检查
                # 截取选区
                template = self.current_screenshot[y1:y2, x1:x2].copy()
                
                # 保存模板
                template_name = self.current_template
                template_path = self.template_dir / f"{template_name}.png"
                cv2.imwrite(str(template_path), template)
                
                logger.info(f"已保存模板: {template_name} ({width}x{height}) 到 {template_path}")
                print(f"✓ 已保存模板: {template_name} ({width}x{height})")
                
                # 移到下一个模板
                self.next_template()
            else:
                print("选区太小，请重新选择")
    
    def next_template(self):
        """移到下一个模板"""
        self.template_index += 1
        if self.template_index >= len(REQUIRED_TEMPLATES):
            print("\n🎉 所有模板收集完成！")
            cv2.destroyAllWindows()
            return False
        
        template_names = list(REQUIRED_TEMPLATES.keys())
        self.current_template = template_names[self.template_index]
        description = REQUIRED_TEMPLATES[self.current_template]
        
        print(f"\n📋 请选择模板 [{self.template_index + 1}/{len(REQUIRED_TEMPLATES)}]: {self.current_template}")
        print(f"描述: {description}")
        print("在截图中用鼠标拖拽选择对应的界面元素")
        
        return True
    
    def start_collection(self):
        """开始收集模板"""
        print("\n🚀 开始收集游戏界面模板")
        print("请确保游戏界面可见，然后按任意键继续...")
        input()
        
        # 获取截图
        if not self.take_screenshot():
            print("❌ 无法获取截图，请检查设备连接")
            return
        
        # 开始第一个模板
        template_names = list(REQUIRED_TEMPLATES.keys())
        self.current_template = template_names[0]
        description = REQUIRED_TEMPLATES[self.current_template]
        
        print(f"\n📋 请选择模板 [1/{len(REQUIRED_TEMPLATES)}]: {self.current_template}")
        print(f"描述: {description}")
        print("在截图中用鼠标拖拽选择对应的界面元素")
        print("按 'q' 键退出，按 's' 键重新截图")
        
        # 显示截图并设置鼠标回调
        cv2.namedWindow("Template Collector", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Template Collector", self.mouse_callback)
        cv2.imshow("Template Collector", self.current_screenshot)
        
        # 等待用户操作
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                print("\n📸 重新获取截图...")
                if self.take_screenshot():
                    cv2.imshow("Template Collector", self.current_screenshot)
                    print("截图已更新")
            elif self.template_index >= len(REQUIRED_TEMPLATES):
                break
        
        cv2.destroyAllWindows()
    
    def list_collected_templates(self):
        """列出已收集的模板"""
        print("\n📁 已收集的模板:")
        for template_name in REQUIRED_TEMPLATES.keys():
            template_path = self.template_dir / f"{template_name}.png"
            if template_path.exists():
                # 读取图片获取尺寸
                img = cv2.imread(str(template_path))
                if img is not None:
                    height, width = img.shape[:2]
                    print(f"✓ {template_name}.png ({width}x{height})")
                else:
                    print(f"⚠ {template_name}.png (无法读取)")
            else:
                print(f"✗ {template_name}.png (未收集)")
    
    def run(self):
        """运行模板收集工具"""
        print("="*50)
        print("🎮 三国志霸业 - 简化模板收集工具")
        print("="*50)
        
        # 连接设备
        if not self.connect_device():
            print("❌ 设备连接失败，请检查设置")
            return
        
        try:
            while True:
                print("\n📋 菜单选项:")
                print("1. 开始收集模板")
                print("2. 查看已收集的模板")
                print("3. 重新获取截图")
                print("4. 退出")
                
                choice = input("\n请选择操作 (1-4): ").strip()
                
                if choice == "1":
                    self.start_collection()
                elif choice == "2":
                    self.list_collected_templates()
                elif choice == "3":
                    if self.take_screenshot():
                        print("✓ 截图已更新")
                elif choice == "4":
                    break
                else:
                    print("❌ 无效的选择，请重试")
        
        except KeyboardInterrupt:
            print("\n\n👋 收到退出信号，正在退出...")
        finally:
            self.device.disconnect()
            print("🔌 设备已断开连接")

def main():
    collector = SimpleTemplateCollector()
    collector.run()

if __name__ == "__main__":
    main()