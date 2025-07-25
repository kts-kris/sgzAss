#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AirPlay捕获配置工具

通过AirPlay将iPad屏幕镜像到Mac，然后捕获镜像窗口的内容。
这个工具帮助用户配置正确的捕获区域。
"""

import os
import sys
import time
import numpy as np
from PIL import Image, ImageGrab
import pyautogui
from loguru import logger

# 禁用pyautogui的安全检查
pyautogui.FAILSAFE = False

class AirPlayCapture:
    """AirPlay捕获配置类"""
    
    def __init__(self):
        self.capture_region = None
        self.config_dir = os.path.join(os.path.dirname(__file__), 'config')
        
    def show_airplay_guide(self):
        """显示AirPlay设置指南"""
        print("\n=== AirPlay设置指南 ===")
        print("1. 确保iPad和Mac连接到同一WiFi网络")
        print("2. 在iPad上打开控制中心（从右上角向下滑动）")
        print("3. 点击'屏幕镜像'按钮")
        print("4. 选择你的Mac设备")
        print("5. 等待iPad屏幕出现在Mac上")
        print("6. 调整镜像窗口大小和位置")
        print("\n请完成上述步骤后按回车键继续...")
        input()
        
    def auto_detect_airplay_window(self):
        """自动检测AirPlay窗口"""
        print("\n正在尝试自动检测AirPlay窗口...")
        
        # 常见的AirPlay窗口标题
        airplay_titles = [
            "iPad",
            "iPhone", 
            "AirPlay",
            "屏幕镜像",
            "Screen Mirroring"
        ]
        
        try:
            # 这里可以添加窗口检测逻辑
            # 由于macOS的窗口检测比较复杂，我们提供手动选择方式
            print("自动检测功能开发中，请使用手动选择方式")
            return None
        except Exception as e:
            logger.error(f"自动检测失败: {e}")
            return None
    
    def manual_select_region(self):
        """手动选择捕获区域"""
        print("\n=== 手动选择捕获区域 ===")
        print("请选择配置方式:")
        print("1. 输入坐标")
        print("2. 鼠标选择区域")
        print("3. 全屏捕获")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            return self._input_coordinates()
        elif choice == "2":
            return self._mouse_select_region()
        elif choice == "3":
            return self._fullscreen_capture()
        else:
            print("无效选择")
            return None
    
    def _input_coordinates(self):
        """输入坐标方式"""
        try:
            print("\n请输入AirPlay窗口的坐标和尺寸:")
            x = int(input("左上角X坐标: "))
            y = int(input("左上角Y坐标: "))
            width = int(input("宽度: "))
            height = int(input("高度: "))
            
            return (x, y, width, height)
        except ValueError:
            print("输入格式错误，请输入数字")
            return None
    
    def _mouse_select_region(self):
        """鼠标选择区域"""
        print("\n=== 鼠标选择区域 ===")
        print("请按照以下步骤操作:")
        print("1. 将鼠标移动到AirPlay窗口的左上角")
        print("2. 按回车键记录第一个点")
        
        input("准备好后按回车键...")
        
        # 获取第一个点
        pos1 = pyautogui.position()
        print(f"第一个点: ({pos1.x}, {pos1.y})")
        
        print("\n3. 将鼠标移动到AirPlay窗口的右下角")
        print("4. 按回车键记录第二个点")
        
        input("准备好后按回车键...")
        
        # 获取第二个点
        pos2 = pyautogui.position()
        print(f"第二个点: ({pos2.x}, {pos2.y})")
        
        # 计算区域
        x = min(pos1.x, pos2.x)
        y = min(pos1.y, pos2.y)
        width = abs(pos2.x - pos1.x)
        height = abs(pos2.y - pos1.y)
        
        return (x, y, width, height)
    
    def _fullscreen_capture(self):
        """全屏捕获"""
        screen_width, screen_height = pyautogui.size()
        return (0, 0, screen_width, screen_height)
    
    def test_capture(self, region):
        """测试捕获效果"""
        if not region:
            return False
            
        x, y, width, height = region
        print(f"\n测试捕获区域: ({x}, {y}, {width}, {height})")
        
        try:
            # 捕获测试截图
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # 保存测试图片
            test_path = os.path.join(os.path.dirname(__file__), 'test_capture.png')
            screenshot.save(test_path)
            
            print(f"测试截图已保存到: {test_path}")
            print("请检查截图是否正确捕获了iPad屏幕")
            
            confirm = input("截图效果是否满意? (y/n): ").strip().lower()
            return confirm == 'y'
            
        except Exception as e:
            logger.error(f"测试捕获失败: {e}")
            return False
    
    def save_config(self, region):
        """保存配置到文件"""
        if not region:
            return False
            
        try:
            # 确保config目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 创建自定义配置文件
            config_content = f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-

\"\"\"
AirPlay捕获配置
自动生成的配置文件
\"\"\"

# AirPlay捕获区域 (x, y, width, height)
AIRPLAY_CAPTURE_REGION = {region}
"""
            
            config_path = os.path.join(self.config_dir, 'custom.py')
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print(f"配置已保存到: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def update_env_file(self):
        """更新.env文件"""
        try:
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            
            # 读取现有配置
            env_content = []
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_content = f.readlines()
            
            # 更新CONNECTION_TYPE
            updated = False
            for i, line in enumerate(env_content):
                if line.startswith('CONNECTION_TYPE='):
                    env_content[i] = 'CONNECTION_TYPE=airplay\n'
                    updated = True
                    break
            
            if not updated:
                env_content.append('CONNECTION_TYPE=airplay\n')
            
            # 写回文件
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(env_content)
            
            print(f".env文件已更新，CONNECTION_TYPE设置为airplay")
            return True
            
        except Exception as e:
            logger.error(f"更新.env文件失败: {e}")
            return False
    
    def run(self):
        """运行配置流程"""
        print("=== AirPlay捕获配置工具 ===")
        print("这个工具将帮助你配置iPad屏幕捕获")
        
        # 显示AirPlay设置指南
        self.show_airplay_guide()
        
        # 尝试自动检测
        region = self.auto_detect_airplay_window()
        
        # 如果自动检测失败，使用手动选择
        if not region:
            region = self.manual_select_region()
        
        if not region:
            print("配置失败，退出")
            return False
        
        # 测试捕获效果
        if not self.test_capture(region):
            print("测试失败或用户不满意，请重新配置")
            return False
        
        # 保存配置
        if self.save_config(region):
            self.update_env_file()
            print("\n=== 配置完成 ===")
            print("现在可以运行主程序来测试iPad屏幕捕获功能")
            print("运行命令: python main.py")
            return True
        else:
            print("保存配置失败")
            return False

def main():
    """主函数"""
    try:
        capture = AirPlayCapture()
        capture.run()
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        logger.exception(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()