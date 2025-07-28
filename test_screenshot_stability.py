#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
截图功能稳定性测试
用于诊断持续运行模式中的截图超时问题
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.connection import ConnectionService
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def test_screenshot_stability():
    """测试截图功能的稳定性"""
    print("🔧 开始截图稳定性测试")
    print("=" * 50)
    
    # 初始化配置和连接服务
    config = get_config()
    connection = ConnectionService(auto_start_tunneld=True)
    
    # 先连接设备
    print("🔌 正在连接设备...")
    if not connection.connect():
        print("❌ 设备连接失败，无法进行测试")
        return
    
    print(f"✅ 设备连接成功: {connection.device_info.name if connection.device_info else 'Unknown'}")
    print()
    
    # 测试参数
    test_count = 10
    success_count = 0
    timeout_count = 0
    error_count = 0
    
    print(f"📊 将进行 {test_count} 次截图测试")
    print(f"USB超时设置: {config.connection.usb_timeout} 秒")
    print(f"截图超时设置: {config.connection.screenshot_timeout} 秒")
    print()
    
    for i in range(1, test_count + 1):
        print(f"🔄 测试 {i}/{test_count}")
        start_time = time.time()
        
        try:
            # 尝试截图
            screenshot_array = connection.get_screenshot()
            end_time = time.time()
            duration = end_time - start_time
            
            if screenshot_array is not None and screenshot_array.size > 0:
                height, width = screenshot_array.shape[:2]
                data_size = screenshot_array.nbytes
                print(f"  ✅ 成功 - 耗时: {duration:.2f}s, 尺寸: {width}x{height}, 数据大小: {data_size} bytes")
                success_count += 1
            else:
                print(f"  ❌ 失败 - 截图数据为空")
                error_count += 1
                
        except asyncio.TimeoutError:
            end_time = time.time()
            duration = end_time - start_time
            print(f"  ⏰ 超时 - 耗时: {duration:.2f}s")
            timeout_count += 1
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"  💥 异常 - 耗时: {duration:.2f}s, 错误: {str(e)}")
            error_count += 1
        
        # 短暂等待
        if i < test_count:
            await asyncio.sleep(1)
    
    # 统计结果
    print()
    print("📈 测试结果统计:")
    print(f"  成功: {success_count}/{test_count} ({success_count/test_count*100:.1f}%)")
    print(f"  超时: {timeout_count}/{test_count} ({timeout_count/test_count*100:.1f}%)")
    print(f"  错误: {error_count}/{test_count} ({error_count/test_count*100:.1f}%)")
    
    if success_count == test_count:
        print("\n🎉 所有测试都成功！截图功能稳定")
    elif timeout_count > 0:
        print(f"\n⚠️  发现 {timeout_count} 次超时，建议增加超时时间")
    else:
        print(f"\n❌ 发现 {error_count} 次错误，需要进一步调试")

def main():
    """主函数"""
    try:
        asyncio.run(test_screenshot_stability())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {str(e)}")
        logger.error(f"Screenshot stability test error: {e}", exc_info=True)

if __name__ == "__main__":
    main()