#!/usr/bin/env python3
"""
测试通过 tunneld 进行截图的脚本
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import LoggerManager

# 初始化日志
logger_manager = LoggerManager()
logger = logger_manager.get_logger(__name__)

def test_tunneld_screenshot():
    """测试通过 tunneld 进行截图"""
    try:
        from pymobiledevice3.exceptions import InvalidServiceError
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
        from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot
        
        logger.info("开始测试 tunneld 截图...")
        
        # 方法1: 尝试直接使用 USB 连接
        logger.info("方法1: 尝试直接 USB 连接")
        try:
            lockdown = create_using_usbmux()
            dvt_service = DvtSecureSocketProxyService(lockdown=lockdown)
            screenshot_service = Screenshot(dvt=dvt_service)
            
            screenshot_data = screenshot_service.get_screenshot()
            logger.info(f"方法1成功: 获取到 {len(screenshot_data)} 字节的截图数据")
            return True
            
        except InvalidServiceError as e:
            logger.warning(f"方法1失败: {e}")
            logger.info("尝试通过 tunneld 重新连接...")
            
        # 方法2: 模拟 CLI 的重试逻辑
        logger.info("方法2: 模拟 CLI 重试逻辑")
        try:
            # 尝试使用 tunneld 地址连接
            from pymobiledevice3.lockdown import create_using_tcp
            
            # 默认 tunneld 地址
            tunneld_address = ('127.0.0.1', 49151)
            
            logger.info(f"尝试连接到 tunneld: {tunneld_address}")
            lockdown = create_using_tcp(tunneld_address[0], tunneld_address[1])
            
            dvt_service = DvtSecureSocketProxyService(lockdown=lockdown)
            screenshot_service = Screenshot(dvt=dvt_service)
            
            screenshot_data = screenshot_service.get_screenshot()
            logger.info(f"方法2成功: 获取到 {len(screenshot_data)} 字节的截图数据")
            return True
            
        except Exception as e:
            logger.error(f"方法2失败: {e}")
            import traceback
            logger.debug(f"异常堆栈:\n{traceback.format_exc()}")
            
        return False
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.debug(f"异常堆栈:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_tunneld_screenshot()
    if success:
        logger.info("测试成功!")
        sys.exit(0)
    else:
        logger.error("测试失败!")
        sys.exit(1)