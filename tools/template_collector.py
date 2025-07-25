#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模板采集工具

用于从游戏截图中采集模板图像，以供视觉识别系统使用。
"""

import os
import sys
import time
import argparse
import cv2
import numpy as np
from pathlib import Path

# 确保可以导入项目模块
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from config import TEMPLATE_DIR, SCREENSHOT_DIR, GAME_TEMPLATES
from utils.logger import setup_logger
from core.device_connector import DeviceConnector
from core.vision import VisionSystem


class TemplateCollector:
    """模板采集工具类，用于从游戏截图中采集模板图像"""
    
    def __init__(self, device_settings, log_settings):
        """初始化模板采集工具
        
        Args:
            device_settings: 设备连接设置
            log_settings: 日志设置
        """
        # 设置日志
        self.logger = setup_logger(log_settings, debug=True)
        
        # 确保目录存在
        os.makedirs(TEMPLATE_DIR, exist_ok=True)
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        
        # 连接设备
        self.logger.info(f"正在连接设备，连接方式: {device_settings['connection_type']}")
        self.device = DeviceConnector(device_settings)
        if not self.device.connect():
            self.logger.error("设备连接失败，请检查设备连接设置")
            sys.exit(1)
        self.logger.info("设备连接成功")
        
        # 当前截图
        self.current_screenshot = None
        self.screenshot_path = None
    
    def take_screenshot(self):
        """获取屏幕截图
        
        Returns:
            bool: 是否成功获取截图
        """
        self.logger.info("正在获取屏幕截图...")
        screenshot = self.device.get_screenshot()
        
        if screenshot is None:
            self.logger.error("获取截图失败")
            return False
        
        self.current_screenshot = screenshot
        
        # 保存截图
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.screenshot_path = os.path.join(SCREENSHOT_DIR, f"screenshot_{timestamp}.png")
        cv2.imwrite(self.screenshot_path, screenshot)
        
        self.logger.info(f"截图已保存: {self.screenshot_path}")
        return True
    
    def show_screenshot(self):
        """显示当前截图"""
        if self.current_screenshot is None:
            self.logger.error("没有可显示的截图")
            return
        
        # 创建一个可调整大小的窗口
        cv2.namedWindow("Screenshot", cv2.WINDOW_NORMAL)
        
        # 调整窗口大小
        height, width = self.current_screenshot.shape[:2]
        screen_height, screen_width = 1080, 1920  # 假设屏幕分辨率
        
        if height > screen_height or width > screen_width:
            scale = min(screen_width / width, screen_height / height) * 0.8
            new_width = int(width * scale)
            new_height = int(height * scale)
            cv2.resizeWindow("Screenshot", new_width, new_height)
        
        # 显示图像
        cv2.imshow("Screenshot", self.current_screenshot)
        
        # 设置鼠标回调函数
        cv2.setMouseCallback("Screenshot", self._mouse_callback)
        
        self.logger.info("按 'q' 键关闭窗口，按 's' 键保存选区为模板")
        
        # 等待按键
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        
        cv2.destroyAllWindows()
    
    def _mouse_callback(self, event, x, y, flags, param):
        """鼠标事件回调函数
        
        Args:
            event: 鼠标事件类型
            x, y: 鼠标坐标
            flags: 事件标志
            param: 额外参数
        """
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
                cv2.imshow("Screenshot", img_copy)
        
        # 完成绘制并保存选区
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            cv2.rectangle(img_copy, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
            cv2.imshow("Screenshot", img_copy)
            
            # 计算矩形坐标（确保左上角和右下角的顺序正确）
            x1, y1 = min(self.ix, x), min(self.iy, y)
            x2, y2 = max(self.ix, x), max(self.iy, y)
            
            # 显示选区信息
            width = x2 - x1
            height = y2 - y1
            self.logger.info(f"已选择区域: ({x1}, {y1}, {width}, {height})")
            
            # 提示用户输入模板名称
            template_name = input("请输入模板名称（按回车确认，直接回车取消）: ").strip()
            if not template_name:
                self.logger.info("已取消保存模板")
                return
            
            # 截取选区并保存为模板
            self._save_template(template_name, x1, y1, width, height)
    
    def _save_template(self, template_name, x, y, width, height):
        """保存选区为模板
        
        Args:
            template_name: 模板名称
            x, y: 选区左上角坐标
            width, height: 选区宽度和高度
        """
        try:
            # 检查坐标是否有效
            if width <= 0 or height <= 0:
                self.logger.error(f"无效的模板区域: ({x}, {y}, {width}, {height})")
                return
            
            # 截取选区
            template = self.current_screenshot[y:y+height, x:x+width].copy()
            
            # 生成文件名
            if template_name not in GAME_TEMPLATES:
                self.logger.warning(f"模板名称 {template_name} 不在预定义列表中")
                template_file = f"{template_name}.png"
            else:
                template_file = GAME_TEMPLATES[template_name]
            
            # 保存模板
            template_path = os.path.join(TEMPLATE_DIR, template_file)
            cv2.imwrite(template_path, template)
            
            self.logger.info(f"已保存模板: {template_name} ({width}x{height}) 到 {template_path}")
            
        except Exception as e:
            self.logger.exception(f"保存模板时出错: {e}")
    
    def run(self):
        """运行模板采集工具"""
        try:
            while True:
                print("\n模板采集工具菜单:")
                print("1. 获取屏幕截图")
                print("2. 显示当前截图并选择模板区域")
                print("3. 查看已保存的模板")
                print("4. 退出")
                
                choice = input("请选择操作 (1-4): ").strip()
                
                if choice == "1":
                    self.take_screenshot()
                elif choice == "2":
                    if self.current_screenshot is None:
                        self.logger.error("请先获取屏幕截图")
                    else:
                        self.show_screenshot()
                elif choice == "3":
                    self._list_templates()
                elif choice == "4":
                    break
                else:
                    print("无效的选择，请重试")
            
        except KeyboardInterrupt:
            self.logger.info("接收到终止信号，正在退出...")
        finally:
            # 断开设备连接
            self.device.disconnect()
            self.logger.info("设备已断开连接")
    
    def _list_templates(self):
        """列出已保存的模板"""
        templates = os.listdir(TEMPLATE_DIR)
        templates = [t for t in templates if t.endswith(".png")]
        
        if not templates:
            print("没有已保存的模板")
            return
        
        print("\n已保存的模板:")
        for i, template in enumerate(templates, 1):
            template_path = os.path.join(TEMPLATE_DIR, template)
            img = cv2.imread(template_path)
            if img is not None:
                height, width = img.shape[:2]
                print(f"{i}. {template} ({width}x{height})")
            else:
                print(f"{i}. {template} (无法读取)")
        
        # 询问是否查看模板
        choice = input("\n输入模板编号查看，或按回车返回: ").strip()
        if choice and choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(templates):
                template = templates[index]
                template_path = os.path.join(TEMPLATE_DIR, template)
                img = cv2.imread(template_path)
                
                if img is not None:
                    # 显示模板
                    cv2.namedWindow(template, cv2.WINDOW_NORMAL)
                    cv2.imshow(template, img)
                    print(f"按任意键关闭窗口")
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                else:
                    print(f"无法读取模板: {template}")
            else:
                print("无效的编号")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="模板采集工具")
    parser.add_argument(
        "--connection-type", 
        type=str, 
        choices=["usb", "network", "simulation"],
        default="simulation",
        help="设备连接方式"
    )
    parser.add_argument(
        "--device-ip", 
        type=str, 
        default="",
        help="设备IP地址（仅在network模式下使用）"
    )
    parser.add_argument(
        "--device-port", 
        type=int, 
        default=5555,
        help="设备端口（仅在network模式下使用）"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设备连接设置
    device_settings = {
        "connection_type": args.connection_type,
        "device_ip": args.device_ip,
        "device_port": args.device_port,
        "screen_width": 2732,  # iPad Pro默认宽度
        "screen_height": 2048,  # iPad Pro默认高度
    }
    
    # 日志设置
    log_settings = {
        "log_level": "DEBUG",
        "log_file": os.path.join(Path(__file__).parent.parent, "logs", "template_collector.log"),
        "rotation": "500 MB",
    }
    
    # 创建并运行模板采集工具
    collector = TemplateCollector(device_settings, log_settings)
    collector.run()


if __name__ == "__main__":
    main()