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
from src.utils.config_manager import get_config_manager
from src.utils.logger import set_log_level, set_console_log_level, set_file_log_level
from src.models import ConfigurationError


class GameCLI:
    """游戏助手命令行界面"""
    
    def __init__(self):
        """初始化CLI"""
        self.config_manager = get_config_manager()
        self.config = get_config()  # 保持向后兼容
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
        print("可用命令 (输入数字或命令名):")
        print("  1. analyze    - 分析当前屏幕")
        print("  2. suggest    - 获取操作建议")
        print("  3. find       - 查找游戏元素")
        print("  4. stats      - 显示统计信息")
        print("  5. optimize   - 优化提示词")
        print("  6. continuous - 启动持续运行模式")
        print("  7. config     - 显示配置信息")
        print("  8. help       - 显示帮助")
        print("  9. quit       - 退出程序")
        print("=" * 50)
        
        while True:
            try:
                command = input("\n🎯 请输入命令 (数字或名称): ").strip().lower()
                
                # 处理数字命令
                if command in ["0", "quit", "exit"]:
                    break
                elif command in ["1", "analyze"]:
                    await self._handle_analyze()
                elif command in ["2", "suggest"]:
                    await self._handle_suggest()
                elif command in ["3", "find"] or command.startswith("find "):
                    if command == "3" or command == "find":
                        try:
                            element_name = input("请输入要查找的元素名称: ").strip()
                        except EOFError:
                            print("\n❌ 输入流已关闭，跳过查找操作")
                            continue
                    else:
                        element_name = command[5:].strip()
                    await self._handle_find(element_name)
                elif command in ["4", "stats"]:
                    await self._handle_stats()
                elif command in ["5", "optimize"]:
                    await self._handle_optimize()
                elif command in ["6", "continuous"]:
                    await self._handle_continuous_mode()
                elif command in ["7", "config"]:
                    self._handle_config()
                elif command in ["8", "loglevel"]:
                    self._handle_log_level()
                elif command in ["9", "help"]:
                    self._show_help()
                else:
                    print(f"❌ 未知命令: {command}")
                    print("💡 输入 '9' 或 'help' 查看可用命令")
                    
            except EOFError:
                print("\n\n📡 检测到输入流结束，程序将优雅退出...")
                logger.info("程序因输入流结束而退出")
                break
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，正在退出...")
                break
            except Exception as e:
                # 详细错误日志记录
                import traceback
                error_details = {
                    'command': command,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'traceback': traceback.format_exc()
                }
                
                logger.error(f"命令执行失败 - 命令: {command}")
                logger.error(f"错误类型: {error_details['error_type']}")
                logger.error(f"错误信息: {error_details['error_message']}")
                logger.error(f"完整堆栈:\n{error_details['traceback']}")
                
                # 保存详细错误到专门的错误日志文件
                self._log_detailed_error(error_details)
                
                print(f"❌ 命令执行失败: {e}")
                print("💡 详细错误信息已记录到日志文件")
        
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
                
                # 获取位置信息
                if suggestion.target:
                    x, y = suggestion.target.center
                    print(f"   位置: ({x}, {y})")
                else:
                    print(f"   位置: 未指定")
                
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
    
    async def _handle_continuous_mode(self):
        """处理持续运行模式"""
        print("\n🔄 持续运行模式配置")
        print("=" * 30)
        
        # 获取配置参数
        try:
            interval = input("请输入分析间隔时间（秒，默认60秒）: ").strip()
            interval = float(interval) if interval else 60.0
            
            if interval < 30.0:
                print("⚠️ 间隔时间不能小于30秒（避免API超时），已设置为30秒")
                interval = 30.0
            
            max_iterations = input("请输入最大运行次数（0表示无限制，默认0）: ").strip()
            max_iterations = int(max_iterations) if max_iterations else 0
            
            auto_execute = input("是否自动执行高优先级建议？(y/n，默认n): ").strip().lower()
            auto_execute = auto_execute in ['y', 'yes', '是']
            
        except ValueError as e:
            logger.error(f"参数输入错误: {e}")
            print("❌ 参数输入错误，使用默认配置")
            interval = 5.0
            max_iterations = 0
            auto_execute = False
        
        print(f"\n🚀 启动持续运行模式")
        print(f"   分析间隔: {interval}秒")
        print(f"   最大次数: {'无限制' if max_iterations == 0 else max_iterations}")
        print(f"   自动执行: {'是' if auto_execute else '否'}")
        print("   按 Ctrl+C 停止运行")
        print("=" * 30)
        
        iteration_count = 0
        
        try:
            while True:
                iteration_count += 1
                
                print(f"\n🔍 第 {iteration_count} 次分析 ({time.strftime('%H:%M:%S')})")
                
                # 执行分析
                start_time = time.time()
                result = await self.assistant.analyze_current_screen()
                analysis_time = time.time() - start_time
                
                if result and result.success:
                    print(f"✅ 分析完成 (耗时: {analysis_time:.2f}秒, 置信度: {result.confidence:.2f})")
                    print(f"🎯 发现元素: {len(result.elements)}个, 操作建议: {len(result.suggestions)}个")
                    
                    # 显示所有操作建议
                    if result.suggestions:
                        print(f"\n💡 操作建议详情:")
                        print("-" * 50)
                        for i, suggestion in enumerate(result.suggestions):
                            # 安全地获取建议属性，支持字典和对象两种格式
                            if hasattr(suggestion, 'priority'):
                                priority = suggestion.priority
                                description = suggestion.description
                                action_type = suggestion.action_type
                                target = suggestion.target
                                confidence = suggestion.confidence
                            else:
                                # 处理字典格式的建议
                                priority = suggestion.get('priority', 0.0)
                                description = suggestion.get('description', '无描述')
                                action_type = suggestion.get('action_type', '未知动作')
                                target = suggestion.get('target')
                                confidence = suggestion.get('confidence', 0.0)
                            
                            priority_icon = "⚡" if priority >= 0.7 else "💡"
                            print(f"{priority_icon} {i+1}. {description}")
                            print(f"   类型: {action_type}")
                            
                            # 获取位置信息
                            if target:
                                if hasattr(target, 'center'):
                                    x, y = target.center
                                elif isinstance(target, dict) and 'center' in target:
                                    x, y = target['center']
                                else:
                                    x, y = 0, 0
                                print(f"   位置: ({x}, {y})")
                            else:
                                print(f"   位置: 未指定")
                            
                            print(f"   优先级: {priority:.2f}")
                            print(f"   置信度: {confidence:.2f}")
                            print()
                        
                        # 处理高优先级建议
                        high_priority_suggestions = []
                        for s in result.suggestions:
                            priority = s.priority if hasattr(s, 'priority') else s.get('priority', 0.0)
                            if priority >= 0.7:
                                high_priority_suggestions.append(s)
                        
                        if high_priority_suggestions:
                            print(f"⚡ 检测到 {len(high_priority_suggestions)} 个高优先级建议")
                            
                            for i, suggestion in enumerate(high_priority_suggestions):
                                # 安全地获取建议属性
                                if hasattr(suggestion, 'description'):
                                    description = suggestion.description
                                    priority = suggestion.priority
                                else:
                                    description = suggestion.get('description', '无描述')
                                    priority = suggestion.get('priority', 0.0)
                                
                                if auto_execute:
                                    print(f"🚀 自动执行建议 {i+1}: {description}")
                                    success = await self.assistant.execute_suggestion(suggestion)
                                    if success:
                                        print(f"✅ 执行成功")
                                    else:
                                        print(f"❌ 执行失败")
                                else:
                                    print(f"💭 建议 {i+1}: {description} (优先级: {priority:.2f})")
                    else:
                        print("\n💭 本次分析未发现可执行的操作建议")
                else:
                    print(f"❌ 分析失败 (耗时: {analysis_time:.2f}秒)")
                
                # 检查是否达到最大次数
                if max_iterations > 0 and iteration_count >= max_iterations:
                    print(f"\n🏁 已完成 {max_iterations} 次分析，退出持续运行模式")
                    break
                
                # 等待下次分析
                print(f"⏱️ 等待 {interval} 秒后进行下次分析...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️ 用户中断，持续运行模式已停止")
            print(f"📊 总共完成 {iteration_count} 次分析")
        except Exception as e:
            logger.error(f"持续运行模式异常: {e}")
            print(f"❌ 持续运行模式异常: {e}")
            print(f"📊 已完成 {iteration_count} 次分析")
    
    def _log_detailed_error(self, error_details: dict):
        """记录详细错误信息到专门的错误日志文件"""
        try:
            from pathlib import Path
            import json
            
            # 确保错误日志目录存在
            error_log_dir = Path("logs/errors")
            error_log_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成错误日志文件名
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            error_file = error_log_dir / f"cli_error_{timestamp}.json"
            
            # 添加时间戳和额外信息
            error_details.update({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'component': 'GameCLI',
                'version': '3.0'
            })
            
            # 保存到JSON文件
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_details, f, ensure_ascii=False, indent=2)
            
            logger.info(f"详细错误信息已保存到: {error_file}")
            
        except Exception as save_error:
            logger.error(f"保存错误日志失败: {save_error}")
    
    def _show_help(self):
        """显示帮助信息"""
        print("\n📖 命令帮助:")
        print("  1. analyze           - 分析当前游戏屏幕，识别元素和生成建议")
        print("  2. suggest           - 获取当前屏幕的操作建议")
        print("  3. find              - 查找指定的游戏元素")
        print("  4. stats             - 显示分析统计信息和服务状态")
        print("  5. optimize          - 手动触发提示词优化")
        print("  6. continuous        - 启动持续运行模式（定期分析）")
        print("  7. config            - 显示当前配置信息")
        print("  8. loglevel          - 设置日志输出等级")
        print("  9. help              - 显示此帮助信息")
        print("  0. quit/exit         - 退出程序")
        print("\n💡 提示:")
        print("  - 可以输入数字快速选择命令")
        print("  - 确保iPad已连接并启动《三国志战略版》")
        print("  - 高优先级建议会询问是否自动执行")
        print("  - 持续运行模式支持自动分析和执行")
        print("  - 使用Ctrl+C可以随时中断操作")
    
    def _handle_config(self):
        """处理config命令"""
        print("\n⚙️ 当前配置信息:")
        print("=" * 40)
        
        # 基本配置
        print("📱 设备连接:")
        print(f"  连接模式: {self.config.connection.connection_mode}")
        print(f"  连接超时: {self.config.connection.timeout}秒")
        print(f"  重试次数: {self.config.connection.retry_count}")
        
        # 视觉识别配置
        print("\n👁️ 视觉识别:")
        print(f"  VLM启用: {'是' if self.config.vision.enable_vlm else '否'}")
        print(f"  VLM提供商: {self.config.vision.vlm_provider}")
        print(f"  Ollama模型: {self.config.vision.ollama_config.model}")
        print(f"  Ollama地址: {self.config.vision.ollama_config.host}:{self.config.vision.ollama_config.port}")
        print(f"  模板阈值: {self.config.vision.template_threshold}")
        
        # 自动化配置
        print("\n🤖 自动化:")
        print(f"  默认后端: {self.config.automation.default_backend}")
        print(f"  操作延迟: {self.config.automation.actions.delay}秒")
        print(f"  点击持续时间: {self.config.automation.actions.click_duration}秒")
        
        # 异步分析配置
        print("\n⚡ 异步分析:")
        print(f"  异步分析: {'启用' if self.config.async_analysis.enabled else '禁用'}")
        print(f"  最大并发: {self.config.async_analysis.max_concurrent_analyses}")
        print(f"  自动分析: {'启用' if self.config.async_analysis.auto_analysis.enabled else '禁用'}")
        if self.config.async_analysis.auto_analysis.enabled:
            print(f"  分析间隔: {self.config.async_analysis.auto_analysis.interval}秒")
        
        # 日志配置
        print("\n📝 日志:")
        print(f"  文件日志级别: {self.config.logging.level}")
        console_level = getattr(self.config.logging, 'console_level', self.config.logging.level)
        print(f"  控制台日志级别: {console_level}")
        print(f"  文件输出: {'是' if self.config.logging.file_path else '否'}")
        if self.config.logging.file_path:
            print(f"  日志文件: {self.config.logging.file_path}")
        print(f"  控制台输出: {'是' if self.config.logging.console_output else '否'}")
        
        # 系统配置
        print("\n🔧 系统:")
        print(f"  调试模式: {'是' if self.config.debug_mode else '否'}")
        print(f"  性能监控: {'是' if self.config.performance_monitoring else '否'}")
        print(f"  自动保存截图: {'是' if self.config.auto_save_screenshots else '否'}")
        print(f"  截图目录: {self.config.screenshot_dir}")
        
        print("=" * 40)
    
    def _handle_log_level(self):
        """处理日志等级设置命令"""
        print("\n📝 日志等级控制")
        print("="*30)
        
        # 显示当前日志等级
        current_file_level = getattr(self.config.logging, 'level', 'DEBUG')
        current_console_level = getattr(self.config.logging, 'console_level', current_file_level)
        
        print(f"当前文件日志等级: {current_file_level}")
        print(f"当前控制台日志等级: {current_console_level}")
        print("\n可用的日志等级:")
        print("  1. DEBUG    - 调试信息（最详细）")
        print("  2. INFO     - 一般信息")
        print("  3. WARNING  - 警告信息")
        print("  4. ERROR    - 错误信息")
        print("  5. CRITICAL - 严重错误（最少）")
        
        print("\n设置选项:")
        print("  1. 设置控制台日志等级")
        print("  2. 设置文件日志等级")
        print("  3. 同时设置控制台和文件日志等级")
        print("  0. 返回主菜单")
        
        try:
            choice = input("\n请选择操作 (0-3): ").strip()
            
            if choice == "0":
                return
            
            level_map = {
                "1": "DEBUG",
                "2": "INFO", 
                "3": "WARNING",
                "4": "ERROR",
                "5": "CRITICAL"
            }
            
            if choice == "1":
                # 设置控制台日志等级
                print("\n设置控制台日志等级:")
                level_choice = input("请选择等级 (1-5): ").strip()
                if level_choice in level_map:
                    level = level_map[level_choice]
                    set_console_log_level(level)
                    print(f"✅ 控制台日志等级已设置为: {level}")
                else:
                    print("❌ 无效的等级选择")
                    
            elif choice == "2":
                # 设置文件日志等级
                print("\n设置文件日志等级:")
                level_choice = input("请选择等级 (1-5): ").strip()
                if level_choice in level_map:
                    level = level_map[level_choice]
                    set_file_log_level(level)
                    print(f"✅ 文件日志等级已设置为: {level}")
                else:
                    print("❌ 无效的等级选择")
                    
            elif choice == "3":
                # 同时设置控制台和文件日志等级
                print("\n设置文件日志等级:")
                file_level_choice = input("请选择文件日志等级 (1-5): ").strip()
                print("\n设置控制台日志等级:")
                console_level_choice = input("请选择控制台日志等级 (1-5): ").strip()
                
                if file_level_choice in level_map and console_level_choice in level_map:
                    file_level = level_map[file_level_choice]
                    console_level = level_map[console_level_choice]
                    set_log_level(file_level, console_level)
                    print(f"✅ 文件日志等级已设置为: {file_level}")
                    print(f"✅ 控制台日志等级已设置为: {console_level}")
                else:
                    print("❌ 无效的等级选择")
            else:
                print("❌ 无效的选择")
                
        except (EOFError, KeyboardInterrupt):
            print("\n操作已取消")
        except Exception as e:
            logger.error(f"设置日志等级失败: {e}")
            print(f"❌ 设置失败: {e}")
        
        print("\n💡 提示: 日志等级设置立即生效，但不会保存到配置文件")
        print("如需永久保存，请修改 config.yaml 文件中的 logging 配置")


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