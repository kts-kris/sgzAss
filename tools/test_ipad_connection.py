#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
iPad连接测试工具

帮助用户测试和配置iPad连接，确保能够正确获取iPad屏幕截图
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from core.device_connector import DeviceConnector
from PIL import Image
import numpy as np

class iPadConnectionTester:
    """iPad连接测试器"""
    
    def __init__(self):
        self.device_connector = None
        
    def test_connection_types(self):
        """测试不同的连接类型"""
        logger.info("=== iPad连接测试工具 ===")
        logger.info("此工具将帮助您测试iPad连接并获取正确的屏幕截图")
        
        while True:
            print("\n请选择连接类型:")
            print("1. 网络连接 (推荐)")
            print("2. USB连接 (开发中)")
            print("3. 模拟模式 (用于测试)")
            print("4. 退出")
            
            choice = input("请输入选择 (1-4): ").strip()
            
            if choice == "1":
                self._test_network_connection()
            elif choice == "2":
                self._test_usb_connection()
            elif choice == "3":
                self._test_simulation_mode()
            elif choice == "4":
                break
            else:
                print("无效选择，请重新输入")
    
    def _test_network_connection(self):
        """测试网络连接"""
        logger.info("\n=== 测试网络连接 ===")
        
        # 获取iPad IP地址
        ip = input("请输入iPad的IP地址 (例如: 192.168.1.100): ").strip()
        if not ip:
            logger.error("IP地址不能为空")
            return
        
        port = input("请输入端口号 (默认: 5555): ").strip()
        if not port:
            port = "5555"
        
        try:
            port = int(port)
        except ValueError:
            logger.error("端口号必须是数字")
            return
        
        # 创建设备连接器
        device_settings = {
            "connection_type": "network",
            "device_ip": ip,
            "device_port": port,
            "screen_width": 2732,
            "screen_height": 2048
        }
        
        self.device_connector = DeviceConnector(device_settings)
        
        logger.info(f"尝试连接到 {ip}:{port}...")
        
        if self.device_connector.connect():
            logger.success("连接成功！")
            self._test_screenshot("network")
            self._save_connection_config(device_settings)
        else:
            logger.error("连接失败")
            self._show_network_troubleshooting()
    
    def _test_usb_connection(self):
        """测试USB连接"""
        logger.info("\n=== 测试USB连接 ===")
        logger.warning("USB连接功能正在开发中")
        logger.info("请确保:")
        logger.info("1. iPad已通过USB连接到电脑")
        logger.info("2. 已安装必要的驱动程序")
        logger.info("3. iPad已信任此电脑")
        
        device_settings = {
            "connection_type": "usb",
            "screen_width": 2732,
            "screen_height": 2048
        }
        
        self.device_connector = DeviceConnector(device_settings)
        
        if self.device_connector.connect():
            logger.success("USB连接成功！")
            self._test_screenshot("usb")
        else:
            logger.error("USB连接失败")
    
    def _test_simulation_mode(self):
        """测试模拟模式"""
        logger.info("\n=== 测试模拟模式 ===")
        logger.warning("模拟模式将截取电脑屏幕，不是iPad屏幕")
        logger.info("此模式仅用于测试程序功能")
        
        device_settings = {
            "connection_type": "simulation",
            "screen_width": 1366,
            "screen_height": 1024
        }
        
        self.device_connector = DeviceConnector(device_settings)
        
        if self.device_connector.connect():
            logger.success("模拟模式设置成功！")
            self._test_screenshot("simulation")
        else:
            logger.error("模拟模式设置失败")
    
    def _test_screenshot(self, connection_type):
        """测试截图功能"""
        logger.info("\n=== 测试截图功能 ===")
        
        for i in range(3):
            logger.info(f"正在获取第 {i+1} 张截图...")
            
            screenshot = self.device_connector.get_screenshot()
            
            if screenshot is not None:
                # 保存截图
                timestamp = int(time.time())
                filename = f"test_screenshot_{connection_type}_{timestamp}_{i+1}.png"
                filepath = os.path.join(Path(__file__).parent.parent, "resources", "screenshots", filename)
                
                # 转换为PIL图像并保存
                if isinstance(screenshot, np.ndarray):
                    image = Image.fromarray(screenshot)
                    image.save(filepath)
                    logger.success(f"截图已保存: {filename}")
                    logger.info(f"图像尺寸: {image.width}x{image.height}")
                else:
                    logger.error("截图数据格式错误")
            else:
                logger.error(f"获取第 {i+1} 张截图失败")
            
            if i < 2:
                time.sleep(2)
        
        # 断开连接
        if self.device_connector:
            self.device_connector.disconnect()
    
    def _save_connection_config(self, device_settings):
        """保存连接配置到.env文件"""
        logger.info("\n=== 保存连接配置 ===")
        
        save_config = input("是否保存此连接配置到.env文件? (y/n): ").strip().lower()
        
        if save_config == 'y':
            env_path = os.path.join(Path(__file__).parent.parent, ".env")
            
            # 读取现有配置
            env_lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_lines = f.readlines()
            
            # 更新配置
            new_lines = []
            updated_keys = set()
            
            for line in env_lines:
                if line.strip() and not line.strip().startswith('#'):
                    key = line.split('=')[0]
                    if key == 'CONNECTION_TYPE':
                        new_lines.append(f"CONNECTION_TYPE={device_settings['connection_type']}\n")
                        updated_keys.add('CONNECTION_TYPE')
                    elif key == 'DEVICE_IP':
                        new_lines.append(f"DEVICE_IP={device_settings.get('device_ip', '')}\n")
                        updated_keys.add('DEVICE_IP')
                    elif key == 'DEVICE_PORT':
                        new_lines.append(f"DEVICE_PORT={device_settings.get('device_port', 5555)}\n")
                        updated_keys.add('DEVICE_PORT')
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # 添加缺失的配置
            if 'CONNECTION_TYPE' not in updated_keys:
                new_lines.append(f"CONNECTION_TYPE={device_settings['connection_type']}\n")
            if 'DEVICE_IP' not in updated_keys:
                new_lines.append(f"DEVICE_IP={device_settings.get('device_ip', '')}\n")
            if 'DEVICE_PORT' not in updated_keys:
                new_lines.append(f"DEVICE_PORT={device_settings.get('device_port', 5555)}\n")
            
            # 保存配置
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            logger.success(f"配置已保存到 {env_path}")
            logger.info("请重新运行主程序以使用新配置")
    
    def _show_network_troubleshooting(self):
        """显示网络连接故障排除指南"""
        logger.info("\n=== 网络连接故障排除 ===")
        logger.info("如果连接失败，请检查以下项目:")
        logger.info("")
        logger.info("1. iPad和电脑是否在同一个WiFi网络中?")
        logger.info("2. iPad的IP地址是否正确?")
        logger.info("   - 在iPad上: 设置 > WiFi > 点击已连接的网络 > 查看IP地址")
        logger.info("3. 是否在iPad上安装了相应的服务端应用?")
        logger.info("4. 防火墙是否阻止了连接?")
        logger.info("5. 端口是否被其他程序占用?")
        logger.info("")
        logger.info("建议:")
        logger.info("- 尝试ping iPad的IP地址: ping <iPad_IP>")
        logger.info("- 检查端口是否开放: telnet <iPad_IP> <端口>")
        logger.info("- 暂时关闭防火墙进行测试")

def main():
    """主函数"""
    tester = iPadConnectionTester()
    tester.test_connection_types()
    logger.info("测试完成，感谢使用！")

if __name__ == "__main__":
    main()