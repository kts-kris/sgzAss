#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
《三国志战略版》游戏助手 v3.0 功能测试脚本

测试本地Ollama VLM、异步分析和提示词优化等核心功能。
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class V3FeatureTester:
    """v3.0功能测试器"""
    
    def __init__(self):
        self.test_results = {}
        
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 《三国志战略版》游戏助手 v3.0 功能测试")
        print("=" * 60)
        
        tests = [
            ("配置加载测试", self.test_config_loading),
            ("Ollama VLM服务测试", self.test_ollama_vlm_service),
            ("异步分析管理器测试", self.test_async_analysis_manager),
            ("游戏助手控制器测试", self.test_game_assistant),
            ("CLI界面测试", self.test_cli_interface),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}...")
            try:
                start_time = time.time()
                await test_func()
                duration = time.time() - start_time
                self.test_results[test_name] = {
                    "status": "PASS",
                    "duration": duration,
                    "error": None
                }
                print(f"   ✅ 通过 ({duration:.2f}s)")
            except Exception as e:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "duration": 0,
                    "error": str(e)
                }
                print(f"   ❌ 失败: {e}")
        
        self._print_test_summary()
    
    async def test_config_loading(self):
        """测试配置加载"""
        from src.utils.config import ConfigManager, get_config
        
        # 测试配置管理器初始化
        config_manager = ConfigManager()
        assert config_manager is not None, "配置管理器初始化失败"
        
        # 测试配置加载
        config = get_config()
        assert config is not None, "配置加载失败"
        
        # 测试关键配置项
        assert hasattr(config.vision, 'ollama_config'), "缺少Ollama配置"
        assert hasattr(config, 'async_analysis'), "缺少异步分析配置"
        
        print(f"   📋 Ollama模型: {config.vision.ollama_config.model}")
        print(f"   📋 异步分析: {'启用' if config.async_analysis.enabled else '禁用'}")
    
    async def test_ollama_vlm_service(self):
        """测试Ollama VLM服务"""
        from src.services.ollama_vlm import OllamaVLMService
        from src.utils.config import get_config
        import requests
        
        # 检查Ollama服务连接
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            assert response.status_code == 200, "Ollama服务未响应"
        except requests.RequestException:
            raise ConnectionError("无法连接到Ollama服务，请确保服务正在运行")
        
        # 获取配置中的模型名称
        config = get_config()
        model_name = config.vision.ollama_config.model
        
        # 测试VLM服务初始化
        vlm_service = OllamaVLMService(model=model_name)
        assert vlm_service is not None, "VLM服务初始化失败"
        
        # 测试服务启动
        await vlm_service.start()
        assert vlm_service.is_running, "VLM服务启动失败"
        
        print(f"   🤖 模型: {vlm_service.model}")
        print(f"   🔗 连接: {vlm_service.host}:{vlm_service.port}")
        
        # 清理
        await vlm_service.stop()
    
    async def test_async_analysis_manager(self):
        """测试异步分析管理器"""
        from src.services.async_analysis_manager import AsyncAnalysisManager
        from src.services.ollama_vlm import OllamaVLMService
        from src.services.connection import ConnectionService
        from src.utils.config import get_config
        
        # 获取配置中的模型名称
        config = get_config()
        model_name = config.vision.ollama_config.model
        
        # 创建VLM服务
        vlm_service = OllamaVLMService(model=model_name)
        await vlm_service.start()
        
        # 创建连接服务（用于测试）
        connection_service = ConnectionService()
        
        try:
            # 测试异步分析管理器初始化
            analysis_manager = AsyncAnalysisManager(
                config_manager=config,
                connection_service=connection_service
            )
            assert analysis_manager is not None, "异步分析管理器初始化失败"
            
            # 测试管理器启动
            await analysis_manager.start()
            assert analysis_manager.is_running, "异步分析管理器启动失败"
            
            # 测试统计信息
            stats = analysis_manager.get_statistics()
            assert isinstance(stats, dict), "统计信息格式错误"
            assert 'total_tasks' in stats, "缺少任务统计"
            
            print(f"   📊 最大并发: {analysis_manager.max_concurrent_tasks}")
            print(f"   📊 历史限制: {analysis_manager.history_limit}")
            
            # 清理
            await analysis_manager.stop()
            
        finally:
            await vlm_service.stop()
    
    async def test_game_assistant(self):
        """测试游戏助手控制器"""
        from src.controllers.game_assistant import GameAssistant
        
        # 测试游戏助手初始化
        assistant = GameAssistant()
        assert assistant is not None, "游戏助手初始化失败"
        
        # 测试服务启动
        await assistant.start()
        
        try:
            # 添加调试信息
            print(f"   🔍 调试: ollama_vlm存在: {hasattr(assistant, 'ollama_vlm')}")
            if hasattr(assistant, 'ollama_vlm') and assistant.ollama_vlm:
                print(f"   🔍 调试: ollama_vlm.is_running: {assistant.ollama_vlm.is_running}")
                print(f"   🔍 调试: ollama_vlm.is_available: {assistant.ollama_vlm.is_available}")
            
            # 检查服务状态
            assert assistant.ollama_vlm.is_running, "Ollama VLM服务未运行"
            assert assistant.async_manager.is_running, "异步分析管理器未运行"
            
            # 测试统计信息
            stats = assistant.get_analysis_statistics()
            assert isinstance(stats, dict), "统计信息格式错误"
            
            print(f"   🎮 VLM服务: {'运行中' if assistant.ollama_vlm.is_running else '已停止'}")
            print(f"   🎮 分析管理器: {'运行中' if assistant.async_manager.is_running else '已停止'}")
            
        finally:
            # 清理
            await assistant.stop()
    
    async def test_cli_interface(self):
        """测试CLI界面"""
        from src.cli.game_cli import GameCLI
        
        # 测试CLI初始化
        cli = GameCLI()
        assert cli is not None, "CLI初始化失败"
        
        # 测试助手初始化
        await cli._initialize_assistant()
        assert cli.assistant is not None, "游戏助手初始化失败"
        
        try:
            # 测试命令处理
            commands = ['help', 'config', 'stats']
            for cmd in commands:
                # 这里只测试命令解析，不实际执行
                assert hasattr(cli, f'_handle_{cmd}'), f"缺少{cmd}命令处理器"
            
            print(f"   💻 支持命令: {len(commands)}个")
            print(f"   💻 助手状态: {'已初始化' if cli.assistant else '未初始化'}")
            
        finally:
            # 清理
            if cli.assistant:
                await cli.assistant.stop()
    
    def _print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📋 测试总结")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        print(f"📈 成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for test_name, result in self.test_results.items():
                if result['status'] == 'FAIL':
                    print(f"   - {test_name}: {result['error']}")
        
        print("\n⏱️ 执行时间:")
        for test_name, result in self.test_results.items():
            if result['status'] == 'PASS':
                print(f"   - {test_name}: {result['duration']:.2f}s")
        
        total_time = sum(result['duration'] for result in self.test_results.values())
        print(f"\n🕐 总耗时: {total_time:.2f}s")
        
        if failed_tests == 0:
            print("\n🎉 所有测试通过！v3.0功能正常工作。")
        else:
            print("\n⚠️ 部分测试失败，请检查相关配置和服务状态。")


async def main():
    """主函数"""
    tester = V3FeatureTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 测试中断")
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)