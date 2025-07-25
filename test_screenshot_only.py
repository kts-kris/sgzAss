#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
专门测试截图功能的脚本
排除其他干扰因素，专注于验证截图能力
"""

import os
import sys
import time
import subprocess
import signal
import tempfile
from PIL import Image
import io

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from loguru import logger

# 设置日志
logger.add("logs/test_screenshot_only.log", rotation="10 MB", retention="7 days", level="DEBUG")

class TunneldManager:
    """管理 pymobiledevice3 tunneld 服务"""
    
    def __init__(self):
        self.process = None
        self.started = False
    
    def start(self):
        """启动 tunneld 服务"""
        try:
            logger.info("正在启动 pymobiledevice3 tunneld 服务...")
            
            # 检查是否已有 tunneld 进程在运行
            check_cmd = "ps aux | grep 'pymobiledevice3 remote tunneld' | grep -v grep"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout.strip():
                logger.info("tunneld 服务已在运行")
                self.started = True
                return True
            
            # 启动新的 tunneld 进程
            cmd = [sys.executable, "-m", "pymobiledevice3", "remote", "tunneld"]
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待服务启动
            time.sleep(3)
            
            if self.process.poll() is None:
                logger.info("tunneld 服务启动成功")
                self.started = True
                return True
            else:
                logger.error("tunneld 服务启动失败")
                return False
                
        except Exception as e:
            logger.exception(f"启动 tunneld 服务失败: {e}")
            return False
    
    def stop(self):
        """停止 tunneld 服务"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("tunneld 服务已停止")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("强制终止 tunneld 服务")
            except Exception as e:
                logger.exception(f"停止 tunneld 服务失败: {e}")
        
        self.started = False
        self.process = None

def test_pymobiledevice3_with_tunneld():
    """测试 pymobiledevice3 通过 tunneld 截图"""
    tunneld = TunneldManager()
    
    try:
        logger.info("=== 测试 pymobiledevice3 通过 tunneld 截图 ===")
        
        # 启动 tunneld 服务
        if not tunneld.start():
            return False, None
        
        # 等待服务稳定
        time.sleep(2)
        
        # 使用命令行方式截图
        timestamp = int(time.time())
        screenshot_path = f"pymobiledevice3_tunneld_{timestamp}.png"
        
        logger.info("正在通过 tunneld 获取截图...")
        start_time = time.time()
        
        cmd = [sys.executable, "-m", "pymobiledevice3", "developer", "dvt", "screenshot", screenshot_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        end_time = time.time()
        
        if result.returncode == 0 and os.path.exists(screenshot_path):
            # 检查截图文件
            image = Image.open(screenshot_path)
            
            logger.info(f"截图获取成功，耗时: {end_time - start_time:.2f}秒")
            logger.info(f"截图已保存到: {screenshot_path}")
            logger.info(f"截图尺寸: {image.width}x{image.height}")
            logger.info(f"截图格式: {image.mode}")
            
            return True, screenshot_path
        else:
            logger.error(f"pymobiledevice3 tunneld 截图失败: {result.stderr}")
            return False, None
            
    except Exception as e:
        logger.exception(f"pymobiledevice3 tunneld 截图失败: {e}")
        return False, None
    finally:
        # 清理 tunneld 服务
        tunneld.stop()

def test_pymobiledevice3_direct():
    """测试 pymobiledevice3 直接截图"""
    try:
        logger.info("=== 测试 pymobiledevice3 直接截图 ===")
        
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.services.screenshot import ScreenshotService
        
        # 连接设备
        logger.info("正在连接设备...")
        lockdown_client = create_using_usbmux()
        
        # 获取设备信息
        device_name = lockdown_client.get_value('DeviceName')
        product_version = lockdown_client.get_value('ProductVersion')
        device_class = lockdown_client.get_value('DeviceClass')
        
        logger.info(f"设备信息: {device_name} (iOS {product_version}, {device_class})")
        
        # 创建截图服务
        logger.info("正在创建截图服务...")
        screenshot_service = ScreenshotService(lockdown=lockdown_client)
        
        # 获取截图
        logger.info("正在获取截图...")
        start_time = time.time()
        screenshot_data = screenshot_service.take_screenshot()
        end_time = time.time()
        
        logger.info(f"截图获取成功，耗时: {end_time - start_time:.2f}秒")
        logger.info(f"截图数据大小: {len(screenshot_data)} 字节")
        
        # 保存截图
        image = Image.open(io.BytesIO(screenshot_data))
        timestamp = int(time.time())
        screenshot_path = f"pymobiledevice3_direct_{timestamp}.png"
        image.save(screenshot_path)
        
        logger.info(f"截图已保存到: {screenshot_path}")
        logger.info(f"截图尺寸: {image.width}x{image.height}")
        logger.info(f"截图格式: {image.mode}")
        
        return True, screenshot_path
        
    except Exception as e:
        logger.exception(f"pymobiledevice3 直接截图失败: {e}")
        return False, None

def test_idevicescreenshot():
    """测试传统 idevicescreenshot 方法"""
    try:
        logger.info("=== 测试传统 idevicescreenshot 方法 ===")
        
        # 检查设备连接
        logger.info("检查设备连接...")
        result = subprocess.run(['ideviceinfo'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            logger.error("未检测到USB连接的iOS设备")
            return False, None
        
        # 获取设备信息
        device_info = result.stdout
        if 'DeviceName:' in device_info:
            device_name = [line.split(':', 1)[1].strip() for line in device_info.split('\n') if line.startswith('DeviceName:')][0]
            logger.info(f"检测到设备: {device_name}")
        
        # 创建临时文件
        temp_file = tempfile.mktemp(suffix='.png')
        
        # 获取截图
        logger.info("正在获取截图...")
        start_time = time.time()
        result = subprocess.run(['idevicescreenshot', temp_file], 
                              capture_output=True, text=True, timeout=15)
        end_time = time.time()
        
        if result.returncode != 0:
            logger.error(f"idevicescreenshot 失败: {result.stderr}")
            return False, None
        
        logger.info(f"截图获取成功，耗时: {end_time - start_time:.2f}秒")
        
        # 检查文件是否存在
        if not os.path.exists(temp_file):
            logger.error("截图文件未生成")
            return False, None
        
        # 读取并保存截图
        image = Image.open(temp_file)
        timestamp = int(time.time())
        screenshot_path = f"idevicescreenshot_{timestamp}.png"
        image.save(screenshot_path)
        
        # 删除临时文件
        os.remove(temp_file)
        
        logger.info(f"截图已保存到: {screenshot_path}")
        logger.info(f"截图尺寸: {image.width}x{image.height}")
        logger.info(f"截图格式: {image.mode}")
        
        return True, screenshot_path
        
    except Exception as e:
        logger.exception(f"idevicescreenshot 失败: {e}")
        return False, None

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("专门测试截图功能")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 3
    successful_methods = []
    
    # 测试 pymobiledevice3 通过 tunneld
    success, path = test_pymobiledevice3_with_tunneld()
    if success:
        success_count += 1
        successful_methods.append("pymobiledevice3 + tunneld")
        logger.info(f"✅ pymobiledevice3 + tunneld 截图成功: {path}")
    else:
        logger.error("❌ pymobiledevice3 + tunneld 截图失败")
    
    logger.info("-" * 40)
    
    # 测试 pymobiledevice3 直接方式
    success, path = test_pymobiledevice3_direct()
    if success:
        success_count += 1
        successful_methods.append("pymobiledevice3 直接")
        logger.info(f"✅ pymobiledevice3 直接截图成功: {path}")
    else:
        logger.error("❌ pymobiledevice3 直接截图失败")
    
    logger.info("-" * 40)
    
    # 测试传统方法
    success, path = test_idevicescreenshot()
    if success:
        success_count += 1
        successful_methods.append("idevicescreenshot")
        logger.info(f"✅ idevicescreenshot 截图成功: {path}")
    else:
        logger.error("❌ idevicescreenshot 截图失败")
    
    logger.info("=" * 60)
    logger.info(f"测试完成: {success_count}/{total_tests} 个方法成功")
    
    if success_count > 0:
        logger.info(f"可用的截图方法: {', '.join(successful_methods)}")
        logger.info("建议优先使用 pymobiledevice3 + tunneld 方法")
        return 0
    else:
        logger.error("所有截图方法都失败了")
        return 1

if __name__ == "__main__":
    exit(main())