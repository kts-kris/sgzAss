#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
iPad客户端应用

在iPad上运行，接收来自电脑的命令并执行相应操作。
需要在iPad上安装Python和必要的依赖。
"""

import os
import io
import sys
import time
import socket
import argparse
from PIL import Image
import numpy as np

# 尝试导入iOS特定模块
try:
    import pyto_ui as ui
    import screenshot
    import touch
    IS_IOS = True
except ImportError:
    # 在非iOS环境下模拟
    IS_IOS = False
    import pyautogui


class IPadClient:
    """iPad客户端类，负责接收命令并执行操作"""
    
    def __init__(self, host='0.0.0.0', port=5555):
        """初始化iPad客户端
        
        Args:
            host: 监听地址
            port: 监听端口
        """
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.connection = None
        
        # 获取屏幕尺寸
        if IS_IOS:
            # 在iOS上获取屏幕尺寸
            self.screen_width, self.screen_height = ui.get_screen_size()
        else:
            # 在其他平台上使用pyautogui获取屏幕尺寸
            self.screen_width, self.screen_height = pyautogui.size()
        
        print(f"屏幕尺寸: {self.screen_width}x{self.screen_height}")
    
    def start(self):
        """启动客户端服务"""
        try:
            # 创建套接字
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            
            print(f"服务已启动，监听 {self.host}:{self.port}")
            self.running = True
            
            while self.running:
                # 等待连接
                print("等待连接...")
                self.connection, address = self.socket.accept()
                print(f"接受来自 {address} 的连接")
                
                # 处理连接
                self._handle_connection()
                
        except Exception as e:
            print(f"服务启动出错: {e}")
        finally:
            self._cleanup()
    
    def _handle_connection(self):
        """处理客户端连接"""
        try:
            while self.running and self.connection:
                # 接收命令
                data = self.connection.recv(1024)
                if not data:
                    print("连接已关闭")
                    break
                
                # 解析命令
                command = data.decode().strip()
                print(f"收到命令: {command}")
                
                # 处理命令
                if command == "HELLO":
                    self.connection.send(b"OK")
                elif command == "SCREENSHOT":
                    self._handle_screenshot()
                elif command.startswith("TAP "):
                    self._handle_tap(command)
                elif command.startswith("SWIPE "):
                    self._handle_swipe(command)
                elif command == "EXIT":
                    self.connection.send(b"OK")
                    self.running = False
                    break
                else:
                    self.connection.send(b"UNKNOWN COMMAND")
                    
        except Exception as e:
            print(f"处理连接时出错: {e}")
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def _handle_screenshot(self):
        """处理截图命令"""
        try:
            # 获取截图
            if IS_IOS:
                # 在iOS上使用screenshot模块获取截图
                img = screenshot.take_screenshot()
            else:
                # 在其他平台上使用pyautogui获取截图
                try:
                    from PIL import ImageGrab
                    img = ImageGrab.grab()
                except Exception as grab_error:
                    print(f"使用ImageGrab获取截图失败: {grab_error}，尝试使用pyautogui")
                    img = pyautogui.screenshot()
            
            # 确保图像是RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 将图像转换为字节流
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=95)  # 使用JPEG格式减小数据大小
            img_byte_arr = img_byte_arr.getvalue()
            
            # 发送图像大小
            size = len(img_byte_arr)
            self.connection.send(size.to_bytes(8, byteorder='big'))
            
            # 分块发送图像数据
            chunk_size = 4096
            sent = 0
            while sent < size:
                chunk = img_byte_arr[sent:sent+chunk_size]
                self.connection.send(chunk)
                sent += len(chunk)
            
            print(f"已发送截图，大小: {size} 字节，分辨率: {img.width}x{img.height}")
            
        except Exception as e:
            print(f"处理截图命令时出错: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.connection.send(b"ERROR")
            except:
                pass
    
    def _handle_tap(self, command):
        """处理点击命令
        
        Args:
            command: 点击命令，格式为 "TAP x y"
        """
        try:
            # 解析坐标
            parts = command.split()
            if len(parts) != 3:
                self.connection.send(b"INVALID COMMAND FORMAT")
                return
            
            x = int(parts[1])
            y = int(parts[2])
            
            # 执行点击
            if IS_IOS:
                # 在iOS上使用touch模块执行点击
                touch.tap(x, y)
            else:
                # 在其他平台上使用pyautogui执行点击
                pyautogui.click(x, y)
            
            print(f"已点击位置: ({x}, {y})")
            self.connection.send(b"OK")
            
        except Exception as e:
            print(f"处理点击命令时出错: {e}")
            self.connection.send(b"ERROR")
    
    def _handle_swipe(self, command):
        """处理滑动命令
        
        Args:
            command: 滑动命令，格式为 "SWIPE start_x start_y end_x end_y duration_ms"
        """
        try:
            # 解析参数
            parts = command.split()
            if len(parts) != 6:
                self.connection.send(b"INVALID COMMAND FORMAT")
                return
            
            start_x = int(parts[1])
            start_y = int(parts[2])
            end_x = int(parts[3])
            end_y = int(parts[4])
            duration_ms = int(parts[5])
            duration_sec = duration_ms / 1000.0
            
            # 执行滑动
            if IS_IOS:
                # 在iOS上使用touch模块执行滑动
                touch.swipe(start_x, start_y, end_x, end_y, duration_sec)
            else:
                # 在其他平台上使用pyautogui执行滑动
                pyautogui.moveTo(start_x, start_y)
                pyautogui.dragTo(end_x, end_y, duration=duration_sec, button='left')
            
            print(f"已滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y}), 持续时间: {duration_sec:.2f}秒")
            self.connection.send(b"OK")
            
        except Exception as e:
            print(f"处理滑动命令时出错: {e}")
            self.connection.send(b"ERROR")
    
    def _cleanup(self):
        """清理资源"""
        if self.connection:
            self.connection.close()
        
        if self.socket:
            self.socket.close()
        
        print("服务已停止")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="iPad客户端应用")
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="监听地址"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=5555,
        help="监听端口"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 创建并启动客户端
    client = IPadClient(host=args.host, port=args.port)
    client.start()


if __name__ == "__main__":
    main()