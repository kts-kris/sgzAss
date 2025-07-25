#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AirPlay屏幕镜像捕获工具

通过AirPlay将iPad屏幕镜像到Mac，然后捕获镜像窗口的内容
这是一个实用的解决方案，不需要在iPad上安装特殊应用
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from PIL import Image, ImageGrab
import pyautogui
import numpy as np

class AirPlayCapture:
    """AirPlay屏幕镜像捕获器"""
    
    def __init__(self):
        self.airplay_window = None
        self.capture_region = None
        
    def setup_airplay_capture(self):
        """设置AirPlay屏幕镜像捕获"""
        logger.info("=== AirPlay屏幕镜像设置指南 ===")
        logger.info("")
        logger.info("请按照以下步骤设置iPad屏幕镜像：")
        logger.info("")
        logger.info("1. 确保iPad和Mac在同一WiFi网络中")
        logger.info("2. 在iPad上打开控制中心（从右上角向下滑动）")
        logger.info("3. 点击'屏幕镜像'按钮")
        logger.info("4. 选择您的Mac设备")
        logger.info("5. 如果需要，输入AirPlay密码")
        logger.info("6. iPad屏幕应该会出现在Mac上")
        logger.info("")
        
        # 等待用户设置
        input("请完成上述步骤后按回车键继续...")
        
        # 检测AirPlay窗口
        return self._detect_airplay_window()
    
    def _detect_airplay_window(self):
        """检测AirPlay镜像窗口"""
        logger.info("正在检测AirPlay镜像窗口...")
        
        # 方法1：通过窗口标题检测
        try:
            # 使用AppleScript获取窗口信息
            script = '''
            tell application "System Events"
                set windowList to {}
                repeat with proc in (every process whose background only is false)
                    try
                        repeat with win in (every window of proc)
                            set windowInfo to {name of win, position of win, size of win, name of proc}
                            set end of windowList to windowInfo
                        end repeat
                    end try
                end repeat
                return windowList
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                windows = result.stdout.strip()
                logger.debug(f"检测到的窗口: {windows}")
                
                # 查找可能的AirPlay窗口
                airplay_keywords = ['iPad', 'iPhone', 'AirPlay', '镜像', 'Mirror']
                
                for keyword in airplay_keywords:
                    if keyword.lower() in windows.lower():
                        logger.info(f"可能找到AirPlay窗口，包含关键词: {keyword}")
                        break
            
        except Exception as e:
            logger.warning(f"自动检测窗口失败: {e}")
        
        # 方法2：手动选择区域
        return self._manual_region_selection()
    
    def _manual_region_selection(self):
        """手动选择捕获区域"""
        logger.info("")
        logger.info("=== 手动选择捕获区域 ===")
        logger.info("")
        logger.info("请按照以下步骤手动选择iPad屏幕区域：")
        logger.info("")
        logger.info("1. 确保iPad镜像窗口可见")
        logger.info("2. 记录窗口的位置和大小")
        logger.info("3. 或者使用自动区域选择工具")
        logger.info("")
        
        while True:
            print("选择方式:")
            print("1. 手动输入坐标")
            print("2. 使用鼠标选择区域")
            print("3. 全屏捕获")
            print("4. 返回")
            
            choice = input("请选择 (1-4): ").strip()
            
            if choice == "1":
                return self._input_coordinates()
            elif choice == "2":
                return self._mouse_selection()
            elif choice == "3":
                return self._fullscreen_capture()
            elif choice == "4":
                return False
            else:
                print("无效选择，请重新输入")
    
    def _input_coordinates(self):
        """手动输入坐标"""
        try:
            print("\n请输入iPad镜像窗口的坐标和尺寸:")
            x = int(input("左上角X坐标: "))
            y = int(input("左上角Y坐标: "))
            width = int(input("宽度: "))
            height = int(input("高度: "))
            
            self.capture_region = (x, y, width, height)
            logger.info(f"设置捕获区域: {self.capture_region}")
            
            # 测试捕获
            return self._test_capture()
            
        except ValueError:
            logger.error("输入的坐标格式错误")
            return False
    
    def _mouse_selection(self):
        """使用鼠标选择区域"""
        logger.info("\n=== 鼠标区域选择 ===")
        logger.info("请按照提示使用鼠标选择iPad屏幕区域")
        logger.info("")
        
        try:
            # 获取屏幕尺寸
            screen_width, screen_height = pyautogui.size()
            logger.info(f"屏幕尺寸: {screen_width}x{screen_height}")
            
            # 提示用户
            input("请将鼠标移动到iPad镜像窗口的左上角，然后按回车键...")
            x1, y1 = pyautogui.position()
            logger.info(f"左上角坐标: ({x1}, {y1})")
            
            input("请将鼠标移动到iPad镜像窗口的右下角，然后按回车键...")
            x2, y2 = pyautogui.position()
            logger.info(f"右下角坐标: ({x2}, {y2})")
            
            # 计算区域
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            self.capture_region = (x, y, width, height)
            logger.info(f"设置捕获区域: {self.capture_region}")
            
            # 测试捕获
            return self._test_capture()
            
        except Exception as e:
            logger.error(f"鼠标选择失败: {e}")
            return False
    
    def _fullscreen_capture(self):
        """全屏捕获"""
        screen_width, screen_height = pyautogui.size()
        self.capture_region = (0, 0, screen_width, screen_height)
        logger.info(f"设置全屏捕获: {self.capture_region}")
        
        return self._test_capture()
    
    def _test_capture(self):
        """测试捕获功能"""
        logger.info("\n=== 测试屏幕捕获 ===")
        
        try:
            # 进行测试捕获
            for i in range(3):
                logger.info(f"正在进行第 {i+1} 次测试捕获...")
                
                screenshot = self.capture_screen()
                
                if screenshot is not None:
                    # 保存测试截图
                    timestamp = int(time.time())
                    filename = f"airplay_test_{timestamp}_{i+1}.png"
                    filepath = os.path.join(Path(__file__).parent.parent, "resources", "screenshots", filename)
                    
                    screenshot.save(filepath)
                    logger.success(f"测试截图已保存: {filename}")
                    logger.info(f"图像尺寸: {screenshot.width}x{screenshot.height}")
                else:
                    logger.error(f"第 {i+1} 次测试捕获失败")
                
                if i < 2:
                    time.sleep(2)
            
            # 询问是否满意
            satisfied = input("\n测试捕获是否满意? (y/n): ").strip().lower()
            
            if satisfied == 'y':
                # 保存配置
                self._save_airplay_config()
                return True
            else:
                logger.info("请重新选择捕获区域")
                return False
                
        except Exception as e:
            logger.error(f"测试捕获失败: {e}")
            return False
    
    def capture_screen(self):
        """捕获屏幕"""
        if not self.capture_region:
            logger.error("捕获区域未设置")
            return None
        
        try:
            x, y, width, height = self.capture_region
            
            # 使用PIL的ImageGrab捕获指定区域
            screenshot = ImageGrab.grab(bbox=(x, y, x+width, y+height))
            
            return screenshot
            
        except Exception as e:
            logger.error(f"屏幕捕获失败: {e}")
            return None
    
    def _save_airplay_config(self):
        """保存AirPlay配置"""
        logger.info("\n=== 保存AirPlay配置 ===")
        
        # 创建自定义配置文件
        config_content = f'''
# AirPlay屏幕镜像配置
# 此配置由AirPlay捕获工具生成

# 设备连接设置
DEVICE_SETTINGS = {{
    "connection_type": "airplay",
    "capture_region": {self.capture_region},
    "screen_width": {self.capture_region[2]},
    "screen_height": {self.capture_region[3]}
}}

# 游戏设置
GAME_SETTINGS = {{
    "match_threshold": 0.8,
    "action_delay_min": 0.5,
    "action_delay_max": 1.5,
    "screenshot_interval": 1.0
}}
'''
        
        config_path = os.path.join(Path(__file__).parent.parent, "config.custom.py")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # 更新.env文件
        env_path = os.path.join(Path(__file__).parent.parent, ".env")
        
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
        
        # 更新CONNECTION_TYPE
        new_lines = []
        connection_type_updated = False
        
        for line in env_lines:
            if line.strip().startswith('CONNECTION_TYPE='):
                new_lines.append('CONNECTION_TYPE=airplay\n')
                connection_type_updated = True
            else:
                new_lines.append(line)
        
        if not connection_type_updated:
            new_lines.append('CONNECTION_TYPE=airplay\n')
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        logger.success(f"配置已保存到:")
        logger.info(f"  - {config_path}")
        logger.info(f"  - {env_path}")
        logger.info("")
        logger.info("现在可以运行主程序测试AirPlay捕获功能")

def main():
    """主函数"""
    capture = AirPlayCapture()
    
    if capture.setup_airplay_capture():
        logger.success("AirPlay屏幕镜像设置完成！")
        logger.info("")
        logger.info("下一步:")
        logger.info("1. 运行主程序: python main.py --debug --duration 30")
        logger.info("2. 检查截图是否正确显示iPad内容")
        logger.info("3. 如果需要，可以重新运行此工具调整捕获区域")
    else:
        logger.error("AirPlay屏幕镜像设置失败")
        logger.info("")
        logger.info("建议:")
        logger.info("1. 确保iPad屏幕镜像正常工作")
        logger.info("2. 检查镜像窗口是否可见")
        logger.info("3. 尝试重新运行此工具")

if __name__ == "__main__":
    main()