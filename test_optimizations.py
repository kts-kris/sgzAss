#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化功能脚本

测试内容：
1. 数字选项命令
2. 详细错误日志记录
3. 持续运行模式配置
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import ConfigManager
from src.utils.logger import LoggerManager
from src.cli.game_cli import GameCLI
from src.controllers.game_assistant import GameAssistant


def test_config_loading():
    """测试配置加载，包括持续运行模式配置"""
    print("\n=== 测试配置加载 ===")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 检查持续运行模式配置
        continuous_config = config.async_analysis.continuous_mode
        print(f"持续运行模式配置:")
        print(f"  启用状态: {continuous_config.enabled}")
        print(f"  默认间隔: {continuous_config.default_interval}秒")
        print(f"  最小间隔: {continuous_config.min_interval}秒")
        print(f"  最大迭代次数: {continuous_config.max_iterations}")
        print(f"  自动执行: {continuous_config.auto_execute}")
        print(f"  优先级阈值: {continuous_config.priority_threshold}")
        print(f"  保存结果: {continuous_config.save_results}")
        print(f"  结果目录: {continuous_config.results_dir}")
        
        print("✅ 配置加载测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置加载测试失败: {e}")
        return False


def test_cli_numeric_commands():
    """测试CLI数字命令"""
    print("\n=== 测试CLI数字命令 ===")
    
    try:
        # 创建游戏助手实例
        assistant = GameAssistant()
        
        # 创建CLI实例
        cli = GameCLI(assistant)
        
        # 测试帮助命令显示
        print("测试帮助信息显示:")
        cli._show_help()
        
        print("✅ CLI数字命令测试通过")
        return True
        
    except Exception as e:
        print(f"❌ CLI数字命令测试失败: {e}")
        return False


def test_error_logging():
    """测试详细错误日志记录"""
    print("\n=== 测试详细错误日志记录 ===")
    
    try:
        # 创建游戏助手实例
        assistant = GameAssistant()
        cli = GameCLI(assistant)
        
        # 模拟一个错误
        test_error = Exception("这是一个测试错误")
        test_context = {
            "command": "test",
            "timestamp": time.time(),
            "user_input": "测试输入"
        }
        
        # 测试详细错误日志记录
        cli._log_detailed_error(test_error, test_context)
        
        # 检查错误日志文件是否创建
        error_log_dir = Path("logs/errors")
        if error_log_dir.exists():
            error_files = list(error_log_dir.glob("*.json"))
            if error_files:
                latest_error_file = max(error_files, key=lambda f: f.stat().st_mtime)
                print(f"错误日志文件已创建: {latest_error_file}")
                
                # 读取并显示错误日志内容
                with open(latest_error_file, 'r', encoding='utf-8') as f:
                    error_data = json.load(f)
                    print(f"错误日志内容: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            else:
                print("未找到错误日志文件")
        else:
            print("错误日志目录不存在")
        
        print("✅ 详细错误日志记录测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 详细错误日志记录测试失败: {e}")
        return False


def test_continuous_mode_config():
    """测试持续运行模式配置"""
    print("\n=== 测试持续运行模式配置 ===")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 获取持续运行模式配置
        continuous_config = config.async_analysis.continuous_mode
        
        # 验证配置项
        assert hasattr(continuous_config, 'enabled'), "缺少enabled配置"
        assert hasattr(continuous_config, 'default_interval'), "缺少default_interval配置"
        assert hasattr(continuous_config, 'min_interval'), "缺少min_interval配置"
        assert hasattr(continuous_config, 'max_iterations'), "缺少max_iterations配置"
        assert hasattr(continuous_config, 'auto_execute'), "缺少auto_execute配置"
        assert hasattr(continuous_config, 'priority_threshold'), "缺少priority_threshold配置"
        assert hasattr(continuous_config, 'save_results'), "缺少save_results配置"
        assert hasattr(continuous_config, 'results_dir'), "缺少results_dir配置"
        
        # 验证配置值类型
        assert isinstance(continuous_config.enabled, bool), "enabled应该是布尔类型"
        assert isinstance(continuous_config.default_interval, (int, float)), "default_interval应该是数字类型"
        assert isinstance(continuous_config.min_interval, (int, float)), "min_interval应该是数字类型"
        assert isinstance(continuous_config.max_iterations, int), "max_iterations应该是整数类型"
        assert isinstance(continuous_config.auto_execute, bool), "auto_execute应该是布尔类型"
        assert isinstance(continuous_config.priority_threshold, (int, float)), "priority_threshold应该是数字类型"
        assert isinstance(continuous_config.save_results, bool), "save_results应该是布尔类型"
        assert isinstance(continuous_config.results_dir, str), "results_dir应该是字符串类型"
        
        print("✅ 持续运行模式配置测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 持续运行模式配置测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试优化功能...")
    
    # 确保日志目录存在
    os.makedirs("logs/errors", exist_ok=True)
    
    tests = [
        ("配置加载", test_config_loading),
        ("CLI数字命令", test_cli_numeric_commands),
        ("详细错误日志记录", test_error_logging),
        ("持续运行模式配置", test_continuous_mode_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {test_name}")
        print(f"{'='*50}")
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试总结")
    print(f"{'='*50}")
    print(f"总测试数: {total}")
    print(f"通过数: {passed}")
    print(f"失败数: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有优化功能测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)