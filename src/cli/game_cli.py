#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
《三国志战略版》游戏助手命令行工具

提供命令行界面来使用游戏助手的各种功能。
"""

import asyncio
import sys
import time
from typing import Optional
from pathlib import Path
import argparse
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.controllers.game_assistant import GameAssistant
from src.services.automation import get_automation_backend
from src.utils.config import get_config
from src.models import ConfigurationError


class GameCLI:
    """游戏助手命令行界面"""
    
    def __init__(self):
        """初始化CLI"""
        self.config = get_config()
        self.assistant: Optional[GameAssistant] = None
        self.automation_backend = None
    
    async def initialize(self):
        """初始化游戏助手"""
        try:
            # 初始化自动化后端
            self.automation_backend = get_automation_backend(
                backend_type=self.config.automation.default_backend
            )
            
            # 初始化游戏助手
            self.assistant = GameAssistant(self.automation_backend)
            
            logger.info("✅ 游戏助手初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            raise
    
    async def _initialize_assistant(self):
        """初始化助手（别名方法）"""
        await self.initialize()
    
    async def start_interactive_mode(self):
        """启动交互模式"""
        if not self.assistant:
            await self.initialize()
        
        await self.assistant.start_assistant()
        
        print("\n🎮 《三国志战略版》游戏助手 v3.0")
        print("=" * 50)
        print("可用命令:")
        print("  analyze    - 分析当前屏幕")
        print("  suggest    - 获取操作建议")
        print("  find <元素> - 查找游戏元素")
        print("  stats      - 显示统计信息")
        print("  optimize   - 优化提示词")
        print("  help       - 显示帮助")
        print("  quit       - 退出程序")
        print("=" * 50)
        
        while True:
            try:
                command = input("\n🎯 请输入命令: ").strip().lower()
                
                if command == "quit" or command == "exit":
                    break
                elif command == "analyze":
                    await self._handle_analyze()
                elif command == "suggest":
                    await self._handle_suggest()
                elif command.startswith("find "):
                    element_name = command[5:].strip()
                    await self._handle_find(element_name)
                elif command == "stats":
                    await self._handle_stats()
                elif command == "optimize":
                    await self._handle_optimize()
                elif command == "help":
                    self._show_help()
                else:
                    print(f"❌ 未知命令: {command}")
                    print("💡 输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，正在退出...")
                break
            except Exception as e:
                logger.error(f"处理命令时出错: {e}")
                print(f"❌ 命令执行失败: {e}")
        
        # 停止助手
        if self.assistant:
            await self.assistant.stop_assistant()
        
        print("\n👋 再见！")
    
    async def _handle_analyze(self):
        """处理分析命令"""
        print("\n📸 正在分析当前屏幕...")
        
        start_time = time.time()
        result = await self.assistant.analyze_current_screen()
        analysis_time = time.time() - start_time
        
        if result and result.success:
            print(f"✅ 分析完成 (耗时: {analysis_time:.2f}秒)")
            print(f"📊 置信度: {result.confidence:.2f}")
            print(f"🎯 发现元素: {len(result.elements)}个")
            print(f"💡 操作建议: {len(result.suggestions)}个")
            
            # 显示前几个元素
            if result.elements:
                print("\n🔍 发现的元素:")
                for i, element in enumerate(result.elements[:5]):
                    print(f"  {i+1}. {element.name} (置信度: {element.confidence:.2f})")
            
            # 显示操作建议
            if result.suggestions:
                print("\n💡 操作建议:")
                for i, suggestion in enumerate(result.suggestions[:3]):
                    print(f"  {i+1}. {suggestion.description} (优先级: {suggestion.priority})")
        else:
            print("❌ 分析失败")
    
    async def _handle_suggest(self):
        """处理建议命令"""
        print("\n🤔 正在获取操作建议...")
        
        suggestions = await self.assistant.get_game_suggestions()
        
        if suggestions:
            print(f"✅ 获取到 {len(suggestions)} 个操作建议:")
            for i, suggestion in enumerate(suggestions):
                print(f"\n{i+1}. {suggestion.description}")
                print(f"   类型: {suggestion.action_type}")
                print(f"   位置: ({suggestion.x}, {suggestion.y})")
                print(f"   优先级: {suggestion.priority}")
                print(f"   置信度: {suggestion.confidence:.2f}")
                
                # 询问是否执行
                if suggestion.priority >= 0.7:  # 高优先级建议
                    execute = input(f"   🚀 是否执行此建议? (y/n): ").strip().lower()
                    if execute == 'y' or execute == 'yes':
                        success = await self.assistant.execute_suggestion(suggestion)
                        if success:
                            print("   ✅ 建议已执行")
                        else:
                            print("   ❌ 建议执行失败")
        else:
            print("❌ 未获取到操作建议")
    
    async def _handle_find(self, element_name: str):
        """处理查找命令"""
        if not element_name:
            print("❌ 请指定要查找的元素名称")
            return
        
        print(f"\n🔍 正在查找元素: {element_name}")
        
        element = await self.assistant.find_game_element(element_name)
        
        if element:
            print(f"✅ 找到元素: {element.name}")
            print(f"   位置: ({element.x}, {element.y})")
            print(f"   大小: {element.width} x {element.height}")
            print(f"   置信度: {element.confidence:.2f}")
        else:
            print(f"❌ 未找到元素: {element_name}")
    
    async def _handle_stats(self):
        """处理统计命令"""
        print("\n📊 统计信息:")
        
        stats = self.assistant.get_analysis_statistics()
        
        print(f"   总分析次数: {stats['total_analyses']}")
        print(f"   运行状态: {'🟢 运行中' if stats['is_running'] else '🔴 已停止'}")
        
        if stats['last_analysis_time'] > 0:
            last_time = time.strftime('%H:%M:%S', time.localtime(stats['last_analysis_time']))
            print(f"   最后分析时间: {last_time}")
        
        print("\n🔧 服务状态:")
        services = stats['services_status']
        for service, status in services.items():
            status_icon = "🟢" if status else "🔴"
            print(f"   {service}: {status_icon}")
        
        # 显示异步分析统计
        if 'async_analysis' in stats:
            async_stats = stats['async_analysis']
            print("\n⚡ 异步分析统计:")
            print(f"   待处理任务: {async_stats.get('pending_tasks', 0)}")
            print(f"   已完成任务: {async_stats.get('completed_tasks', 0)}")
            print(f"   失败任务: {async_stats.get('failed_tasks', 0)}")
    
    async def _handle_optimize(self):
        """处理优化命令"""
        print("\n🔧 正在优化提示词...")
        
        success = await self.assistant.optimize_prompts()
        
        if success:
            print("✅ 提示词优化完成")
        else:
            print("❌ 提示词优化失败")
    
    def _show_help(self):
        """显示帮助信息"""
        print("\n📖 命令帮助:")
        print("  analyze           - 分析当前游戏屏幕，识别元素和生成建议")
        print("  suggest           - 获取当前屏幕的操作建议")
        print("  find <元素名称>    - 查找指定的游戏元素")
        print("  stats             - 显示分析统计信息和服务状态")
        print("  optimize          - 手动触发提示词优化")
        print("  help              - 显示此帮助信息")
        print("  quit/exit         - 退出程序")
        print("\n💡 提示:")
        print("  - 确保iPad已连接并启动《三国志战略版》")
        print("  - 高优先级建议会询问是否自动执行")
        print("  - 使用Ctrl+C可以随时中断操作")
    
    def _handle_help(self):
        """处理help命令"""
        self._show_help()
    
    def _handle_config(self):
        """处理config命令"""
        print("\n⚙️ 当前配置:")
        print(f"  Ollama模型: {self.config.vision.ollama_config.model}")
        print(f"  异步分析: {'启用' if self.config.async_analysis.enabled else '禁用'}")
        print(f"  自动化后端: {self.config.automation.default_backend}")
    
    def _handle_stats(self):
        """处理stats命令"""
        if self.assistant:
            stats = self.assistant.get_analysis_statistics()
            print("\n📊 统计信息:")
            print(f"  总分析次数: {stats.get('total_analyses', 0)}")
            print(f"  运行状态: {'🟢 运行中' if stats.get('is_running', False) else '🔴 已停止'}")
        else:
            print("\n❌ 游戏助手未初始化")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="《三国志战略版》游戏助手 v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        help="配置文件路径"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="启用调试模式"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    try:
        # 创建CLI实例
        cli = GameCLI()
        
        # 启动交互模式
        await cli.start_interactive_mode()
        
    except ConfigurationError as e:
        logger.error(f"配置错误: {e}")
        print(f"❌ 配置错误: {e}")
        print("💡 请检查配置文件和Ollama服务状态")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，正在退出...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常: {e}")
        print(f"❌ 程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())