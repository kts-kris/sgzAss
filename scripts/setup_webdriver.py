#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WebDriverAgent环境设置脚本

自动化安装和配置WebDriverAgent所需的环境和依赖。
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path
from loguru import logger


class WebDriverSetup:
    """WebDriverAgent环境设置类"""
    
    def __init__(self):
        self.system = platform.system()
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / "config" / "webdriver_config.json"
        
    def check_system_requirements(self) -> bool:
        """
        检查系统要求
        
        Returns:
            bool: 系统是否满足要求
        """
        logger.info("=== 检查系统要求 ===")
        
        if self.system != "Darwin":
            logger.error("WebDriverAgent仅支持macOS系统")
            return False
        
        logger.info(f"操作系统: {self.system} ✓")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            logger.error(f"需要Python 3.8+，当前版本: {python_version.major}.{python_version.minor}")
            return False
        
        logger.info(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro} ✓")
        
        return True
    
    def check_xcode(self) -> bool:
        """
        检查Xcode安装
        
        Returns:
            bool: Xcode是否已安装
        """
        logger.info("=== 检查Xcode ===")
        
        try:
            # 检查xcode-select
            result = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                xcode_path = result.stdout.strip()
                logger.info(f"Xcode路径: {xcode_path} ✓")
                
                # 检查Xcode版本
                result = subprocess.run(["xcodebuild", "-version"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.strip().split('\n')[0]
                    logger.info(f"Xcode版本: {version_info} ✓")
                    return True
                else:
                    logger.warning("无法获取Xcode版本信息")
                    return False
            else:
                logger.error("Xcode Command Line Tools未安装")
                logger.info("请运行: xcode-select --install")
                return False
                
        except Exception as e:
            logger.error(f"检查Xcode失败: {e}")
            return False
    
    def install_homebrew(self) -> bool:
        """
        安装Homebrew（如果未安装）
        
        Returns:
            bool: 安装是否成功
        """
        logger.info("=== 检查Homebrew ===")
        
        try:
            # 检查brew是否已安装
            result = subprocess.run(["brew", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_info = result.stdout.strip().split('\n')[0]
                logger.info(f"Homebrew已安装: {version_info} ✓")
                return True
            
        except FileNotFoundError:
            logger.info("Homebrew未安装，正在安装...")
            
            try:
                # 安装Homebrew
                install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                result = subprocess.run(install_cmd, shell=True, timeout=600)
                
                if result.returncode == 0:
                    logger.info("Homebrew安装成功 ✓")
                    return True
                else:
                    logger.error("Homebrew安装失败")
                    return False
                    
            except Exception as e:
                logger.error(f"安装Homebrew失败: {e}")
                return False
        
        except Exception as e:
            logger.error(f"检查Homebrew失败: {e}")
            return False
    
    def install_node_npm(self) -> bool:
        """
        安装Node.js和npm
        
        Returns:
            bool: 安装是否成功
        """
        logger.info("=== 检查Node.js和npm ===")
        
        try:
            # 检查Node.js
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                logger.info(f"Node.js已安装: {node_version} ✓")
            else:
                raise FileNotFoundError("Node.js未安装")
            
            # 检查npm
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                npm_version = result.stdout.strip()
                logger.info(f"npm已安装: {npm_version} ✓")
                return True
            else:
                raise FileNotFoundError("npm未安装")
                
        except FileNotFoundError:
            logger.info("Node.js/npm未安装，正在通过Homebrew安装...")
            
            try:
                result = subprocess.run(["brew", "install", "node"], timeout=300)
                if result.returncode == 0:
                    logger.info("Node.js和npm安装成功 ✓")
                    return True
                else:
                    logger.error("Node.js和npm安装失败")
                    return False
                    
            except Exception as e:
                logger.error(f"安装Node.js和npm失败: {e}")
                return False
        
        except Exception as e:
            logger.error(f"检查Node.js和npm失败: {e}")
            return False
    
    def install_appium(self) -> bool:
        """
        安装Appium
        
        Returns:
            bool: 安装是否成功
        """
        logger.info("=== 检查Appium ===")
        
        try:
            # 检查Appium是否已安装
            result = subprocess.run(["appium", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                appium_version = result.stdout.strip()
                logger.info(f"Appium已安装: {appium_version} ✓")
                return True
                
        except FileNotFoundError:
            logger.info("Appium未安装，正在安装...")
            
            try:
                # 安装Appium
                result = subprocess.run(["npm", "install", "-g", "appium"], timeout=300)
                if result.returncode == 0:
                    logger.info("Appium安装成功 ✓")
                    return True
                else:
                    logger.error("Appium安装失败")
                    return False
                    
            except Exception as e:
                logger.error(f"安装Appium失败: {e}")
                return False
        
        except Exception as e:
            logger.error(f"检查Appium失败: {e}")
            return False
    
    def install_xcuitest_driver(self) -> bool:
        """
        安装XCUITest驱动
        
        Returns:
            bool: 安装是否成功
        """
        logger.info("=== 检查XCUITest驱动 ===")
        
        try:
            # 检查已安装的驱动
            result = subprocess.run(["appium", "driver", "list", "--installed"], capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and "xcuitest" in result.stdout:
                logger.info("XCUITest驱动已安装 ✓")
                return True
            
            logger.info("XCUITest驱动未安装，正在安装...")
            
            # 安装XCUITest驱动
            result = subprocess.run(["appium", "driver", "install", "xcuitest"], timeout=300)
            if result.returncode == 0:
                logger.info("XCUITest驱动安装成功 ✓")
                return True
            else:
                logger.error("XCUITest驱动安装失败")
                return False
                
        except Exception as e:
            logger.error(f"安装XCUITest驱动失败: {e}")
            return False
    
    def install_libimobiledevice(self) -> bool:
        """
        安装libimobiledevice工具
        
        Returns:
            bool: 安装是否成功
        """
        logger.info("=== 检查libimobiledevice ===")
        
        try:
            # 检查idevice_id是否可用
            result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("libimobiledevice已安装 ✓")
                return True
                
        except FileNotFoundError:
            logger.info("libimobiledevice未安装，正在安装...")
            
            try:
                # 安装libimobiledevice
                result = subprocess.run(["brew", "install", "libimobiledevice"], timeout=300)
                if result.returncode == 0:
                    logger.info("libimobiledevice安装成功 ✓")
                    return True
                else:
                    logger.error("libimobiledevice安装失败")
                    return False
                    
            except Exception as e:
                logger.error(f"安装libimobiledevice失败: {e}")
                return False
        
        except Exception as e:
            logger.error(f"检查libimobiledevice失败: {e}")
            return False
    
    def install_python_dependencies(self) -> bool:
        """
        安装Python依赖
        
        Returns:
            bool: 安装是否成功
        """
        logger.info("=== 安装Python依赖 ===")
        
        try:
            # 检查requirements.txt
            requirements_file = self.project_root / "requirements.txt"
            if not requirements_file.exists():
                logger.warning("requirements.txt不存在，跳过Python依赖安装")
                return True
            
            # 安装依赖
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], timeout=300)
            if result.returncode == 0:
                logger.info("Python依赖安装成功 ✓")
                return True
            else:
                logger.error("Python依赖安装失败")
                return False
                
        except Exception as e:
            logger.error(f"安装Python依赖失败: {e}")
            return False
    
    def detect_devices(self) -> list:
        """
        检测连接的设备
        
        Returns:
            list: 设备UDID列表
        """
        logger.info("=== 检测设备 ===")
        
        try:
            result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                devices = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                logger.info(f"发现设备: {devices}")
                return devices
            else:
                logger.warning("未发现连接的设备")
                return []
                
        except Exception as e:
            logger.error(f"检测设备失败: {e}")
            return []
    
    def create_config(self, devices: list) -> bool:
        """
        创建配置文件
        
        Args:
            devices: 设备UDID列表
            
        Returns:
            bool: 创建是否成功
        """
        logger.info("=== 创建配置文件 ===")
        
        try:
            # 确保config目录存在
            config_dir = self.project_root / "config"
            config_dir.mkdir(exist_ok=True)
            
            # 创建配置
            config = {
                "webdriver": {
                    "server_url": "http://localhost:4723",
                    "device_name": "iPad",
                    "platform_version": "17.0",
                    "bundle_id": "com.apple.springboard",
                    "automation_name": "XCUITest",
                    "new_command_timeout": 300,
                    "wda_launch_timeout": 60000,
                    "wda_connection_timeout": 60000,
                    "use_new_wda": False,
                    "no_reset": True,
                    "full_reset": False
                },
                "device": {
                    "connection_type": "usb",
                    "device_ip": None,
                    "device_port": 8100
                },
                "devices": []
            }
            
            # 添加检测到的设备
            for udid in devices:
                device_config = {
                    "udid": udid,
                    "name": f"Device_{udid[:8]}",
                    "enabled": True
                }
                config["devices"].append(device_config)
            
            # 如果有设备，设置第一个为默认设备
            if devices:
                config["webdriver"]["udid"] = devices[0]
            
            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置文件已创建: {self.config_file} ✓")
            return True
            
        except Exception as e:
            logger.error(f"创建配置文件失败: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            bool: 测试是否成功
        """
        logger.info("=== 测试连接 ===")
        
        try:
            # 启动Appium服务器（后台）
            logger.info("启动Appium服务器...")
            appium_process = subprocess.Popen(
                ["appium", "--log-level", "error"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 等待服务器启动
            import time
            time.sleep(5)
            
            try:
                # 检查服务器状态
                result = subprocess.run(
                    ["curl", "-s", "http://localhost:4723/status"],
                    capture_output=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info("Appium服务器运行正常 ✓")
                    
                    # 如果有配置文件，尝试连接设备
                    if self.config_file.exists():
                        logger.info("配置文件存在，连接测试完成 ✓")
                    
                    return True
                else:
                    logger.error("Appium服务器无响应")
                    return False
                    
            finally:
                # 停止Appium服务器
                appium_process.terminate()
                appium_process.wait(timeout=10)
                
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            return False
    
    def run_setup(self) -> bool:
        """
        运行完整设置流程
        
        Returns:
            bool: 设置是否成功
        """
        logger.info("开始WebDriverAgent环境设置")
        
        # 检查系统要求
        if not self.check_system_requirements():
            return False
        
        # 检查Xcode
        if not self.check_xcode():
            logger.error("请先安装Xcode和Command Line Tools")
            return False
        
        # 安装Homebrew
        if not self.install_homebrew():
            return False
        
        # 安装Node.js和npm
        if not self.install_node_npm():
            return False
        
        # 安装Appium
        if not self.install_appium():
            return False
        
        # 安装XCUITest驱动
        if not self.install_xcuitest_driver():
            return False
        
        # 安装libimobiledevice
        if not self.install_libimobiledevice():
            return False
        
        # 安装Python依赖
        if not self.install_python_dependencies():
            return False
        
        # 检测设备
        devices = self.detect_devices()
        
        # 创建配置文件
        if not self.create_config(devices):
            return False
        
        # 测试连接
        if not self.test_connection():
            logger.warning("连接测试失败，但环境设置已完成")
        
        logger.info("WebDriverAgent环境设置完成 ✓")
        return True


def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    try:
        setup = WebDriverSetup()
        success = setup.run_setup()
        
        if success:
            logger.info("\n=== 设置完成 ===")
            logger.info("现在您可以使用WebDriverAgent进行iPad自动化控制了！")
            logger.info("\n下一步:")
            logger.info("1. 连接您的iPad设备")
            logger.info("2. 在iPad上信任此电脑")
            logger.info("3. 运行示例: python examples/webdriver_integration_example.py")
            logger.info(f"4. 配置文件位置: {setup.config_file}")
        else:
            logger.error("设置失败，请检查错误信息并重试")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断设置")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"设置过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()