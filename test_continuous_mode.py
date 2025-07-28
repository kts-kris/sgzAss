#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试持续运行模式的自动化脚本

这个脚本将自动启动游戏助手的持续运行模式，
并监控其运行状态，用于验证超时问题是否已解决。
"""

import asyncio
import sys
import time
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.cli.game_cli import GameCLI
from src.utils.config import get_config


async def test_continuous_mode():
    """测试持续运行模式"""
    print("🧪 开始测试持续运行模式")
    print("=" * 50)
    
    try:
        # 创建CLI实例
        cli = GameCLI()
        
        # 初始化游戏助手
        print("📱 正在初始化游戏助手...")
        await cli.initialize()
        print("✅ 游戏助手初始化完成")
        
        # 显示当前配置
        config = get_config()
        print(f"\n⚙️ 当前配置:")
        print(f"   截图超时: {config.connection.screenshot_timeout}秒")
        print(f"   USB超时: {config.connection.usb_timeout}秒")
        print(f"   VLM模型: {config.vision.ollama_config.model}")
        print(f"   Ollama地址: {config.vision.ollama_config.host}:{config.vision.ollama_config.port}")
        
        # 模拟持续运行模式的参数设置
        interval = 60.0  # 60秒间隔
        max_iterations = 3  # 最多运行3次
        auto_execute = False  # 不自动执行
        
        print(f"\n🚀 启动持续运行模式测试")
        print(f"   分析间隔: {interval}秒")
        print(f"   最大次数: {max_iterations}")
        print(f"   自动执行: {'是' if auto_execute else '否'}")
        print("   按 Ctrl+C 停止运行")
        print("=" * 50)
        
        # 开始持续运行循环
        iteration_count = 0
        start_time = time.time()
        
        while True:
            iteration_count += 1
            current_time = time.strftime("%H:%M:%S")
            
            print(f"\n🔍 第 {iteration_count} 次分析 ({current_time})")
            
            try:
                # 执行分析
                analysis_start = time.time()
                result = await cli.assistant.analyze_current_screen()
                analysis_time = time.time() - analysis_start
                
                if result and result.success:
                    print(f"✅ 分析完成 (耗时: {analysis_time:.2f}秒, 置信度: {result.confidence:.2f})")
                    print(f"🎯 发现元素: {len(result.elements)}个, 操作建议: {len(result.suggestions)}个")
                    
                    # 显示操作建议详情
                    if result.suggestions:
                        print("\n💡 操作建议详情:")
                        print("-" * 50)
                        
                        high_priority_count = 0
                        for i, suggestion in enumerate(result.suggestions, 1):
                            priority_icon = "⚡" if suggestion.priority >= 0.7 else "💡"
                            print(f"{priority_icon} {i}. {suggestion.description}")
                            print(f"   类型: {suggestion.action_type.value}")
                            if suggestion.element and suggestion.element.position:
                                pos = suggestion.element.position
                                print(f"   位置: ({pos.x}, {pos.y})")
                            print(f"   优先级: {suggestion.priority:.2f}")
                            print(f"   置信度: {suggestion.confidence:.2f}")
                            print()
                            
                            if suggestion.priority >= 0.7:
                                high_priority_count += 1
                        
                        if high_priority_count > 0:
                            print(f"⚡ 检测到 {high_priority_count} 个高优先级建议")
                            if auto_execute:
                                print("🚀 自动执行模式已启用，将执行高优先级建议")
                            else:
                                print("💭 自动执行模式已禁用，跳过执行")
                    else:
                        print("\n💭 本次分析未发现可执行的操作建议")
                else:
                    print(f"❌ 分析失败 (耗时: {analysis_time:.2f}秒)")
                    if result and hasattr(result, 'error_message'):
                        print(f"   错误信息: {result.error_message}")
                
            except Exception as e:
                analysis_time = time.time() - analysis_start
                print(f"❌ 分析异常 (耗时: {analysis_time:.2f}秒): {e}")
                logger.error(f"分析异常: {e}")
            
            # 检查是否达到最大次数
            if max_iterations > 0 and iteration_count >= max_iterations:
                print(f"\n🏁 已完成 {max_iterations} 次分析，退出持续运行模式")
                break
            
            # 等待下次分析
            print(f"⏱️ 等待 {interval} 秒后进行下次分析...")
            await asyncio.sleep(interval)
        
        # 显示测试结果
        total_time = time.time() - start_time
        print(f"\n📊 测试完成统计:")
        print(f"   总运行时间: {total_time:.1f}秒")
        print(f"   完成分析次数: {iteration_count}")
        print(f"   平均分析间隔: {total_time/iteration_count:.1f}秒")
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️ 用户中断，持续运行模式已停止")
        print(f"📊 总共完成 {iteration_count} 次分析")
    except Exception as e:
        logger.error(f"持续运行模式测试异常: {e}")
        print(f"❌ 持续运行模式测试异常: {e}")
    finally:
        # 清理资源
        if cli.assistant:
            try:
                await cli.assistant.stop_assistant()
                print("🧹 游戏助手已停止")
            except Exception as e:
                logger.warning(f"停止游戏助手时出现异常: {e}")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    # 运行测试
    asyncio.run(test_continuous_mode())