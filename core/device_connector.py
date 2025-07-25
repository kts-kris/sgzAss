#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备连接器模块

负责与iPad设备建立连接，获取屏幕截图，发送触控指令等。
支持USB连接和网络连接两种方式。
"""

import os
import io  # 添加io模块导入
import time
import socket
import subprocess
import sys
from loguru import logger
from PIL import Image, ImageGrab
import numpy as np
import pyautogui

# pymobiledevice3 相关导入
try:
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.screenshot import ScreenshotService
    from pymobiledevice3.exceptions import InvalidServiceError, PasswordRequiredError, NoDeviceConnectedError, PairingError
    PYMOBILEDEVICE3_AVAILABLE = True
except ImportError:
    PYMOBILEDEVICE3_AVAILABLE = False
    logger.warning("pymobiledevice3 未安装，USB截图功能将使用传统方式")


class TunneldManager:
    """管理 pymobiledevice3 tunneld 服务"""
    
    def __init__(self):
        self.process = None
        self.started = False
    
    def is_running(self):
        """检查 tunneld 服务是否在运行"""
        try:
            check_cmd = "ps aux | grep 'pymobiledevice3 remote tunneld' | grep -v grep"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            return bool(result.stdout.strip())
        except Exception:
            return False
    
    def start(self):
        """启动 tunneld 服务"""
        try:
            if self.is_running():
                logger.debug("tunneld 服务已在运行")
                self.started = True
                return True
            
            logger.debug("正在启动 pymobiledevice3 tunneld 服务...")
            
            # 启动新的 tunneld 进程
            cmd = [sys.executable, "-m", "pymobiledevice3", "remote", "tunneld"]
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待服务启动
            time.sleep(2)
            
            if self.process.poll() is None:
                logger.debug("tunneld 服务启动成功")
                self.started = True
                return True
            else:
                logger.warning("tunneld 服务启动失败")
                return False
                
        except Exception as e:
            logger.warning(f"启动 tunneld 服务失败: {e}")
            return False
    
    def stop(self):
        """停止 tunneld 服务"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
                logger.debug("tunneld 服务已停止")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.debug("强制终止 tunneld 服务")
            except Exception as e:
                logger.warning(f"停止 tunneld 服务失败: {e}")
        
        self.started = False
        self.process = None


class DeviceConnector:
    """设备连接器类，负责与iPad设备的通信"""
    
    def __init__(self, device_settings):
        """初始化设备连接器
        
        Args:
            device_settings: 设备连接配置
        """
        self.settings = device_settings
        self.connection_type = device_settings["connection_type"]
        self.device_ip = device_settings.get("device_ip", "")
        self.device_port = device_settings.get("device_port", 5555)
        self.screen_width = device_settings.get("screen_width", 2732)  # iPad Pro默认宽度
        self.screen_height = device_settings.get("screen_height", 2048)  # iPad Pro默认高度
        self.connected = False
        self.connection = None
        
        # pymobiledevice3 相关属性
        self.lockdown_client = None
        self.screenshot_service = None
        self.tunneld_manager = TunneldManager()
        
        # 用于模拟连接的屏幕区域（仅在模拟模式下使用）
        self.simulation_region = None
    
    def connect(self):
        """连接到设备
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if self.connection_type == "usb":
                return self._connect_usb()
            elif self.connection_type == "network":
                return self._connect_network()
            elif self.connection_type == "simulation":
                return self._setup_simulation()
            elif self.connection_type == "airplay":
                return self._setup_airplay()
            else:
                logger.error(f"不支持的连接类型: {self.connection_type}")
                return False
        except Exception as e:
            logger.exception(f"连接设备时出错: {e}")
            return False
    
    def _connect_usb(self):
        """通过USB连接到设备
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if PYMOBILEDEVICE3_AVAILABLE:
                # 使用 pymobiledevice3 连接设备
                logger.info("使用 pymobiledevice3 连接USB设备...")
                
                try:
                    # 创建 lockdown 客户端
                    self.lockdown_client = create_using_usbmux()
                    
                    # 获取设备信息
                    device_name = self.lockdown_client.get_value('DeviceName')
                    product_version = self.lockdown_client.get_value('ProductVersion')
                    device_class = self.lockdown_client.get_value('DeviceClass')
                    logger.info(f"检测到USB连接的设备: {device_name} (iOS {product_version}, {device_class})")
                    
                    # 尝试创建截图服务
                    try:
                        self.screenshot_service = ScreenshotService(lockdown=self.lockdown_client)
                        logger.info("截图服务初始化成功")
                    except Exception as e:
                        logger.warning(f"截图服务初始化失败: {e}")
                        if "InvalidService" in str(e):
                            logger.warning("截图服务不可用，可能需要设备配对、开发者模式或信任此电脑")
                        elif "PasswordRequired" in str(e):
                            logger.warning("设备需要解锁或信任此电脑")
                        self.screenshot_service = None
                    
                    self.connected = True
                    logger.info("pymobiledevice3 USB连接成功")
                    return True
                    
                except Exception as e:
                    logger.warning(f"pymobiledevice3 连接失败: {e}")
                    if "NoDeviceConnectedError" in str(e):
                        logger.warning("未检测到USB连接的iOS设备")
                    elif "PairingError" in str(e):
                        logger.warning("设备配对失败，请确保设备已信任此电脑")
                    # 回退到传统方式
                    logger.info("回退到传统连接方式...")
                
            else:
                # 回退到传统方式
                logger.info("使用传统方式连接USB设备...")
                
                # 检查是否有iOS设备连接
                result = subprocess.run(['ideviceinfo'], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    logger.error("未检测到USB连接的iOS设备")
                    return False
                
                # 获取设备信息
                device_info = result.stdout
                if 'DeviceName:' in device_info:
                    device_name = [line.split(':', 1)[1].strip() for line in device_info.split('\n') if line.startswith('DeviceName:')][0]
                    logger.info(f"检测到USB连接的设备: {device_name}")
                
                # 检查开发者磁盘镜像状态
                mount_result = subprocess.run(['ideviceimagemounter', '-l'], capture_output=True, text=True, timeout=5)
                if mount_result.returncode == 0 and 'Status: Complete' in mount_result.stdout:
                    logger.info("开发者磁盘镜像已挂载")
                else:
                    logger.warning("开发者磁盘镜像未挂载，某些功能可能不可用")
                
                self.connected = True
                logger.info("传统USB连接成功")
                return True
            
            # 如果配置了网络IP，尝试建立网络连接作为备用
            if self.device_ip:
                logger.info(f"尝试建立网络连接作为备用方案: {self.device_ip}:{self.device_port}")
                try:
                    # 尝试建立TCP连接
                    backup_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    backup_connection.settimeout(5)
                    backup_connection.connect((self.device_ip, self.device_port))
                    
                    # 发送测试消息
                    backup_connection.send(b"HELLO")
                    response = backup_connection.recv(1024)
                    
                    if response == b"OK":
                        logger.info(f"网络连接备用方案建立成功: {self.device_ip}:{self.device_port}")
                        self.connection = backup_connection
                    else:
                        logger.warning(f"网络连接备用方案响应异常: {response}")
                        backup_connection.close()
                        
                except Exception as e:
                    logger.warning(f"网络连接备用方案建立失败，将仅使用USB连接: {e}")
                    if 'backup_connection' in locals():
                        backup_connection.close()
            
        except subprocess.TimeoutExpired:
            logger.error("USB连接超时")
            return False
        except Exception as e:
            logger.exception(f"USB连接失败: {e}")
            return False
    
    def _connect_network(self):
        """通过网络连接到设备
        
        Returns:
            bool: 连接是否成功
        """
        if not self.device_ip:
            logger.error("未设置设备IP地址")
            return False
        
        try:
            # 尝试建立TCP连接
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(5)  # 设置连接超时
            self.connection.connect((self.device_ip, self.device_port))
            
            # 发送测试消息
            self.connection.send(b"HELLO")
            response = self.connection.recv(1024)
            
            if response == b"OK":
                logger.info(f"成功连接到设备 {self.device_ip}:{self.device_port}")
                self.connected = True
                return True
            else:
                logger.error(f"设备响应异常: {response}")
                self.connection.close()
                return False
                
        except Exception as e:
            logger.exception(f"网络连接失败: {e}")
            if self.connection:
                self.connection.close()
            return False
    
    def _setup_simulation(self):
        """设置模拟模式
        
        在模拟模式下，使用本地屏幕的一部分区域模拟iPad屏幕
        
        Returns:
            bool: 设置是否成功
        """
        try:
            # 获取屏幕尺寸
            screen_width, screen_height = pyautogui.size()
            
            # 计算模拟区域（居中显示）
            x = max(0, (screen_width - self.screen_width) // 2)
            y = max(0, (screen_height - self.screen_height) // 2)
            
            # 如果屏幕太小，则缩放模拟区域
            if self.screen_width > screen_width or self.screen_height > screen_height:
                scale = min(screen_width / self.screen_width, screen_height / self.screen_height) * 0.9
                new_width = int(self.screen_width * scale)
                new_height = int(self.screen_height * scale)
                
                x = (screen_width - new_width) // 2
                y = (screen_height - new_height) // 2
                
                self.simulation_region = (x, y, new_width, new_height)
                logger.info(f"模拟区域已缩放: {self.simulation_region}")
            else:
                self.simulation_region = (x, y, self.screen_width, self.screen_height)
                logger.info(f"模拟区域: {self.simulation_region}")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.exception(f"设置模拟模式失败: {e}")
            return False
    
    def disconnect(self):
        """断开与设备的连接"""
        if not self.connected:
            return
        
        try:
            if self.connection_type == "network" and self.connection:
                self.connection.close()
            
            # 清理 pymobiledevice3 连接
            if self.screenshot_service:
                self.screenshot_service = None
            if self.lockdown_client:
                self.lockdown_client = None
            
            self.connected = False
            logger.info("已断开设备连接")
            
        except Exception as e:
            logger.exception(f"断开连接时出错: {e}")
    
    def get_screenshot(self):
        """获取设备屏幕截图
        
        Returns:
            numpy.ndarray: 屏幕截图图像数据，如果失败则返回None
        """
        if not self.connected:
            logger.error("设备未连接，无法获取截图")
            return None
        
        try:
            if self.connection_type == "usb":
                return self._get_screenshot_usb()
            elif self.connection_type == "network":
                return self._get_screenshot_network()
            elif self.connection_type == "simulation":
                return self._get_screenshot_simulation()
            elif self.connection_type == "airplay":
                return self._get_screenshot_airplay()
            else:
                logger.error(f"不支持的连接类型: {self.connection_type}")
                return None
        except Exception as e:
            logger.exception(f"获取截图时出错: {e}")
            return None
    
    def _get_screenshot_usb(self):
        """通过USB获取屏幕截图
        
        Returns:
            numpy.ndarray: 屏幕截图图像数据
        """
        try:
            if PYMOBILEDEVICE3_AVAILABLE and self.screenshot_service:
                # 使用 pymobiledevice3 获取截图
                logger.debug("使用 pymobiledevice3 获取USB截图...")
                
                try:
                    # 获取截图数据
                    screenshot_data = self.screenshot_service.take_screenshot()
                    
                    # 将字节数据转换为PIL图像
                    image = Image.open(io.BytesIO(screenshot_data))
                    
                    # 确保图像是RGB格式
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # 转换为numpy数组
                    img_array = np.array(image)
                    
                    logger.debug(f"pymobiledevice3 USB截图成功，尺寸: {image.width}x{image.height}")
                    return img_array
                    
                except Exception as e:
                    logger.warning(f"pymobiledevice3 截图失败: {e}")
                    if "InvalidService" in str(e):
                        logger.warning("截图服务不可用，可能需要设备配对或开发者模式")
                    elif "PasswordRequired" in str(e):
                        logger.warning("设备需要解锁或信任此电脑")
                    # 回退到传统方式
                    logger.info("回退到传统截图方式...")
                
            else:
                # 回退到传统方式
                logger.debug("使用传统方式获取USB截图...")
                
                # 创建临时文件名
                import tempfile
                temp_file = tempfile.mktemp(suffix='.png')
                
                # 首先尝试使用 pymobiledevice3 + tunneld 方法
                tunneld_success = False
                try:
                    # 确保 tunneld 服务运行
                    if not self.tunneld_manager.is_running():
                        logger.debug("启动 tunneld 服务以支持截图")
                        self.tunneld_manager.start()
                        time.sleep(1)  # 等待服务稳定
                    
                    # 使用 pymobiledevice3 tunneld 方法获取截图
                    result = subprocess.run([sys.executable, '-m', 'pymobiledevice3', 'developer', 'dvt', 'screenshot', temp_file], 
                                          capture_output=True, text=True, timeout=15)
                    
                    if result.returncode == 0 and os.path.exists(temp_file):
                        logger.debug("pymobiledevice3 tunneld 截图成功")
                        tunneld_success = True
                    else:
                        logger.warning(f"pymobiledevice3 tunneld 截图失败: {result.stderr}")
                        
                except Exception as e:
                    logger.warning(f"pymobiledevice3 tunneld 方法失败: {e}")
                
                # 如果 tunneld 方法失败，回退到传统方法
                if not tunneld_success:
                    logger.debug("回退到传统 idevicescreenshot 方法")
                    result = subprocess.run(['idevicescreenshot', temp_file], 
                                          capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    logger.warning(f"获取USB截图失败: {result.stderr}")
                    # 如果截图服务不可用，返回空白图像
                    if "screenshotr service" in result.stderr:
                        logger.warning("截图服务不可用，可能需要挂载开发者磁盘镜像")
                        logger.info("iOS 26.0版本过新，USB截图服务不可用，建议使用网络连接模式")
                    
                    # 如果USB截图失败，尝试使用网络连接
                    if hasattr(self, 'device_ip') and self.device_ip and hasattr(self, 'connection') and self.connection:
                        logger.info("尝试使用网络连接获取截图...")
                        return self._get_screenshot_network()
                    else:
                        logger.error("网络连接不可用，无法获取截图")
                        logger.warning("返回空白图像，建议使用AirPlay模式或确保网络连接正常")
                        img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
                        return img
                
                # 读取截图文件
                if os.path.exists(temp_file):
                    image = Image.open(temp_file)
                    
                    # 确保图像是RGB格式
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # 转换为numpy数组
                    img_array = np.array(image)
                    
                    # 删除临时文件
                    os.remove(temp_file)
                    
                    logger.debug(f"传统USB截图成功，尺寸: {image.width}x{image.height}")
                    return img_array
                else:
                    logger.error("截图文件未生成")
                    img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
                    return img
                
        except subprocess.TimeoutExpired:
            logger.error("USB截图超时")
            # 尝试网络连接作为备用方案
            if hasattr(self, 'device_ip') and self.device_ip and hasattr(self, 'connection') and self.connection:
                logger.info("尝试使用网络连接作为备用方案...")
                return self._get_screenshot_network()
            else:
                img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
                return img
        except Exception as e:
            logger.exception(f"USB截图失败: {e}")
            # 尝试网络连接作为备用方案
            if hasattr(self, 'device_ip') and self.device_ip and hasattr(self, 'connection') and self.connection:
                logger.info("尝试使用网络连接作为备用方案...")
                return self._get_screenshot_network()
            else:
                img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
                return img
    
    def _get_screenshot_network(self):
        """通过网络获取屏幕截图
        
        Returns:
            numpy.ndarray: 屏幕截图图像数据
        """
        try:
            # 发送截图请求
            self.connection.send(b"SCREENSHOT")
            
            # 接收图像数据大小
            size_data = self.connection.recv(8)
            image_size = int.from_bytes(size_data, byteorder='big')
            
            logger.debug(f"准备接收图像数据，大小: {image_size} 字节")
            
            # 接收图像数据
            received_data = b""
            bytes_received = 0
            start_time = time.time()
            
            while bytes_received < image_size:
                chunk = self.connection.recv(min(4096, image_size - bytes_received))
                if not chunk:
                    logger.warning("接收数据中断")
                    break
                received_data += chunk
                bytes_received += len(chunk)
                
                # 每秒打印一次进度
                if time.time() - start_time > 1:
                    logger.debug(f"接收进度: {bytes_received}/{image_size} 字节 ({bytes_received/image_size*100:.1f}%)")
                    start_time = time.time()
            
            if bytes_received < image_size:
                logger.warning(f"接收数据不完整: {bytes_received}/{image_size} 字节")
            
            # 将数据转换为图像
            try:
                # 创建内存中的图像对象
                image_data = io.BytesIO(received_data)
                image = Image.open(image_data)
                
                # 确保图像是RGB格式
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # 转换为numpy数组
                img_array = np.array(image)
                
                logger.debug(f"成功获取网络截图，尺寸: {image.width}x{image.height}")
                return img_array
                
            except Exception as e:
                logger.exception(f"图像数据解析失败: {e}")
                
                # 保存原始数据以便调试
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, f"network_image_debug_{int(time.time())}.bin")
                
                with open(debug_file, "wb") as f:
                    f.write(received_data)
                logger.info(f"已保存原始图像数据到 {debug_file} 以便调试")
                
                return None
            
        except Exception as e:
            logger.exception(f"通过网络获取截图失败: {e}")
            return None
    
    def _get_screenshot_simulation(self):
        """在模拟模式下获取屏幕截图
        
        Returns:
            numpy.ndarray: 屏幕截图图像数据
        """
        try:
            if not self.simulation_region:
                logger.error("模拟区域未设置")
                return None
            
            # 获取指定区域的屏幕截图
            x, y, width, height = self.simulation_region
            
            # 使用PIL的ImageGrab替代pyautogui.screenshot
            from PIL import ImageGrab
            screenshot = ImageGrab.grab(bbox=(x, y, x+width, y+height))
            
            # 转换为numpy数组
            img_array = np.array(screenshot)
            
            # 确保图像是RGB格式
            if len(img_array.shape) == 2:  # 灰度图像
                img_array = np.stack((img_array,) * 3, axis=-1)
            elif img_array.shape[2] == 4:  # RGBA图像
                img_array = img_array[:, :, :3]
                
            logger.debug(f"成功获取模拟截图，尺寸: {img_array.shape[1]}x{img_array.shape[0]}")
            return img_array
            
        except Exception as e:
            logger.exception(f"获取模拟截图失败: {e}")
            return None
    
    def tap(self, x, y):
        """在屏幕上点击指定位置
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected:
            logger.error("设备未连接，无法执行点击操作")
            return False
        
        try:
            if self.connection_type == "usb":
                return self._tap_usb(x, y)
            elif self.connection_type == "network":
                return self._tap_network(x, y)
            elif self.connection_type == "simulation":
                return self._tap_simulation(x, y)
            elif self.connection_type == "airplay":
                return self._tap_airplay(x, y)
            else:
                logger.error(f"不支持的连接类型: {self.connection_type}")
                return False
        except Exception as e:
            logger.exception(f"点击操作失败: {e}")
            return False
    
    def _tap_usb(self, x, y):
        """通过USB执行点击操作
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 检查是否有可用的触控工具
            # 注意：libimobiledevice本身不支持触控操作
            # 需要使用其他工具如WebDriverAgent或ios-deploy
            logger.warning(f"USB触控操作需要额外工具支持，当前模拟点击位置: ({x}, {y})")
            logger.info("建议使用网络连接模式或安装WebDriverAgent以支持触控操作")
            return True
        except Exception as e:
            logger.exception(f"USB点击操作失败: {e}")
            return False
    
    def _tap_network(self, x, y):
        """通过网络执行点击操作
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 发送点击命令
            command = f"TAP {x} {y}".encode()
            self.connection.send(command)
            
            # 接收响应
            response = self.connection.recv(1024)
            
            if response == b"OK":
                logger.debug(f"点击位置 ({x}, {y}) 成功")
                return True
            else:
                logger.error(f"点击操作响应异常: {response}")
                return False
                
        except Exception as e:
            logger.exception(f"通过网络执行点击操作失败: {e}")
            return False
    
    def _tap_simulation(self, x, y):
        """在模拟模式下执行点击操作
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.simulation_region:
                logger.error("模拟区域未设置")
                return False
            
            # 计算在模拟区域中的实际坐标
            sim_x, sim_y, sim_width, sim_height = self.simulation_region
            
            # 计算缩放比例
            scale_x = sim_width / self.screen_width
            scale_y = sim_height / self.screen_height
            
            # 计算实际点击位置
            real_x = sim_x + int(x * scale_x)
            real_y = sim_y + int(y * scale_y)
            
            # 执行点击
            pyautogui.click(real_x, real_y)
            logger.debug(f"模拟点击位置: ({real_x}, {real_y})")
            
            return True
            
        except Exception as e:
            logger.exception(f"模拟点击操作失败: {e}")
            return False
    
    def swipe(self, start_x, start_y, end_x, end_y, duration=0.5):
        """在屏幕上执行滑动操作
        
        Args:
            start_x: 起始横坐标
            start_y: 起始纵坐标
            end_x: 结束横坐标
            end_y: 结束纵坐标
            duration: 滑动持续时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        if not self.connected:
            logger.error("设备未连接，无法执行滑动操作")
            return False
        
        try:
            if self.connection_type == "usb":
                return self._swipe_usb(start_x, start_y, end_x, end_y, duration)
            elif self.connection_type == "network":
                return self._swipe_network(start_x, start_y, end_x, end_y, duration)
            elif self.connection_type == "simulation":
                return self._swipe_simulation(start_x, start_y, end_x, end_y, duration)
            elif self.connection_type == "airplay":
                return self._swipe_airplay(start_x, start_y, end_x, end_y, duration)
            else:
                logger.error(f"不支持的连接类型: {self.connection_type}")
                return False
        except Exception as e:
            logger.exception(f"滑动操作失败: {e}")
            return False
    
    def _swipe_usb(self, start_x, start_y, end_x, end_y, duration):
        """通过USB执行滑动操作
        
        Args:
            start_x: 起始横坐标
            start_y: 起始纵坐标
            end_x: 结束横坐标
            end_y: 结束纵坐标
            duration: 滑动持续时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        # 这里需要根据实际情况实现USB滑动逻辑
        logger.warning(f"USB滑动功能尚未实现，模拟滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        return True
    
    def _swipe_network(self, start_x, start_y, end_x, end_y, duration):
        """通过网络执行滑动操作
        
        Args:
            start_x: 起始横坐标
            start_y: 起始纵坐标
            end_x: 结束横坐标
            end_y: 结束纵坐标
            duration: 滑动持续时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 发送滑动命令
            command = f"SWIPE {start_x} {start_y} {end_x} {end_y} {int(duration * 1000)}".encode()
            self.connection.send(command)
            
            # 接收响应
            response = self.connection.recv(1024)
            
            if response == b"OK":
                logger.debug(f"滑动操作成功: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
                return True
            else:
                logger.error(f"滑动操作响应异常: {response}")
                return False
                
        except Exception as e:
            logger.exception(f"通过网络执行滑动操作失败: {e}")
            return False
    
    def _swipe_simulation(self, start_x, start_y, end_x, end_y, duration):
        """在模拟模式下执行滑动操作
        
        Args:
            start_x: 起始横坐标
            start_y: 起始纵坐标
            end_x: 结束横坐标
            end_y: 结束纵坐标
            duration: 滑动持续时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.simulation_region:
                logger.error("模拟区域未设置")
                return False
            
            # 计算在模拟区域中的实际坐标
            sim_x, sim_y, sim_width, sim_height = self.simulation_region
            
            # 计算缩放比例
            scale_x = sim_width / self.screen_width
            scale_y = sim_height / self.screen_height
            
            # 计算实际滑动位置
            real_start_x = sim_x + int(start_x * scale_x)
            real_start_y = sim_y + int(start_y * scale_y)
            real_end_x = sim_x + int(end_x * scale_x)
            real_end_y = sim_y + int(end_y * scale_y)
            
            # 执行滑动
            pyautogui.moveTo(real_start_x, real_start_y)
            pyautogui.dragTo(real_end_x, real_end_y, duration=duration, button='left')
            
            logger.debug(f"模拟滑动: ({real_start_x}, {real_start_y}) -> ({real_end_x}, {real_end_y})")
            return True
            
        except Exception as e:
            logger.exception(f"模拟滑动操作失败: {e}")
            return False
    
    def _setup_airplay(self):
        """设置AirPlay模式
        
        在AirPlay模式下，从配置文件加载捕获区域设置
        
        Returns:
            bool: 设置是否成功
        """
        try:
            # 尝试导入自定义配置
            try:
                import sys
                import os
                # 添加项目根目录到Python路径
                project_root = os.path.dirname(os.path.dirname(__file__))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                
                import config.custom as custom_config
                if hasattr(custom_config, 'AIRPLAY_CAPTURE_REGION'):
                    self.airplay_region = custom_config.AIRPLAY_CAPTURE_REGION
                    logger.info(f"从配置文件加载AirPlay捕获区域: {self.airplay_region}")
                else:
                    logger.error("配置文件中未找到AIRPLAY_CAPTURE_REGION设置")
                    return False
            except ImportError as e:
                logger.error(f"未找到config.custom配置文件: {e}，请先运行airplay_capture.py进行配置")
                return False
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.exception(f"设置AirPlay模式失败: {e}")
            return False
    
    def _get_screenshot_airplay(self):
        """通过AirPlay获取屏幕截图
        
        Returns:
            numpy.ndarray: 屏幕截图图像数据
        """
        try:
            if not hasattr(self, 'airplay_region') or not self.airplay_region:
                logger.error("AirPlay捕获区域未设置")
                return None
            
            x, y, width, height = self.airplay_region
            
            # 使用PIL截取指定区域
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # 转换为RGB格式的numpy数组
            img_array = np.array(screenshot.convert('RGB'))
            
            logger.debug(f"AirPlay截图成功，区域: {self.airplay_region}，尺寸: {img_array.shape}")
            return img_array
            
        except Exception as e:
            logger.exception(f"AirPlay截图失败: {e}")
            return None
    
    def _tap_airplay(self, x, y):
        """在AirPlay模式下执行点击操作
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not hasattr(self, 'airplay_region') or not self.airplay_region:
                logger.error("AirPlay捕获区域未设置")
                return False
            
            # 计算在AirPlay区域中的实际坐标
            region_x, region_y, region_width, region_height = self.airplay_region
            
            # 计算缩放比例
            scale_x = region_width / self.screen_width
            scale_y = region_height / self.screen_height
            
            # 计算实际点击位置
            real_x = region_x + int(x * scale_x)
            real_y = region_y + int(y * scale_y)
            
            # 执行点击
            pyautogui.click(real_x, real_y)
            logger.debug(f"AirPlay点击位置: ({real_x}, {real_y})")
            
            return True
            
        except Exception as e:
            logger.exception(f"AirPlay点击操作失败: {e}")
            return False
    
    def _swipe_airplay(self, start_x, start_y, end_x, end_y, duration):
        """在AirPlay模式下执行滑动操作
        
        Args:
            start_x: 起始横坐标
            start_y: 起始纵坐标
            end_x: 结束横坐标
            end_y: 结束纵坐标
            duration: 滑动持续时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not hasattr(self, 'airplay_region') or not self.airplay_region:
                logger.error("AirPlay捕获区域未设置")
                return False
            
            # 计算在AirPlay区域中的实际坐标
            region_x, region_y, region_width, region_height = self.airplay_region
            
            # 计算缩放比例
            scale_x = region_width / self.screen_width
            scale_y = region_height / self.screen_height
            
            # 计算实际滑动位置
            real_start_x = region_x + int(start_x * scale_x)
            real_start_y = region_y + int(start_y * scale_y)
            real_end_x = region_x + int(end_x * scale_x)
            real_end_y = region_y + int(end_y * scale_y)
            
            # 执行滑动
            pyautogui.moveTo(real_start_x, real_start_y)
            pyautogui.dragTo(real_end_x, real_end_y, duration=duration, button='left')
            
            logger.debug(f"AirPlay滑动: ({real_start_x}, {real_start_y}) -> ({real_end_x}, {real_end_y})")
            return True
            
        except Exception as e:
            logger.exception(f"AirPlay滑动操作失败: {e}")
            return False