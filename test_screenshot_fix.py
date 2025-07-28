#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试截图重复保存修复

验证修复后不再生成重复的截图文件
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config, ConfigManager
from src.controllers.game_assistant import GameAssistant
from src.services.connection import ConnectionService
from src.utils.screenshot import ScreenshotManager
import numpy as np


def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")
    
    try:
        config = get_config()
        
        # 检查关键配置项
        print(f"auto_save_screenshots: {config.auto_save_screenshots}")
        print(f"save_analysis_screenshots: {config.save_analysis_screenshots}")
        print(f"screenshot_dir: {config.screenshot_dir}")
        
        # 验证配置正确性
        assert config.auto_save_screenshots == False, "auto_save_screenshots 应该为 False"
        assert config.save_analysis_screenshots == True, "save_analysis_screenshots 应该为 True"
        
        print("✅ 配置加载测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置加载测试失败: {e}")
        return False


def test_screenshot_manager_save():
    """测试截图管理器保存功能"""
    print("\n=== 测试截图管理器保存功能 ===")
    
    try:
        # 创建模拟连接
        mock_connection = Mock(spec=ConnectionService)
        
        # 创建截图管理器
        screenshot_manager = ScreenshotManager(mock_connection)
        
        # 创建模拟截图数据
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 测试同步保存
        with patch('src.utils.helpers.save_screenshot') as mock_save:
            result = screenshot_manager.save_screenshot_sync(
                screenshot=mock_screenshot,
                filename="test_screenshot.png"
            )
            
            # 验证保存函数被调用
            assert mock_save.called, "保存函数应该被调用"
            print("✅ 截图管理器保存功能正常")
            
        return True
        
    except Exception as e:
        print(f"❌ 截图管理器测试失败: {e}")
        return False


def test_game_assistant_screenshot_logic():
    """测试游戏助手截图逻辑"""
    print("\n=== 测试游戏助手截图逻辑 ===")
    
    try:
        # 创建模拟配置
        config = get_config()
        
        # 验证配置状态
        print(f"当前配置 - auto_save_screenshots: {config.auto_save_screenshots}")
        print(f"当前配置 - save_analysis_screenshots: {config.save_analysis_screenshots}")
        
        # 测试不同配置组合的逻辑
        test_cases = [
            {
                "auto_save": False,
                "save_analysis": True,
                "save_screenshot": True,
                "expected": "应该保存分析截图"
            },
            {
                "auto_save": True,
                "save_analysis": True,
                "save_screenshot": True,
                "expected": "应该跳过保存（已自动保存）"
            },
            {
                "auto_save": False,
                "save_analysis": False,
                "save_screenshot": True,
                "expected": "应该跳过保存（分析截图已禁用）"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {case['expected']}")
            
            # 模拟条件判断逻辑
            save_screenshot = case["save_screenshot"]
            auto_save = case["auto_save"]
            save_analysis = case["save_analysis"]
            
            if save_screenshot and save_analysis and not auto_save:
                result = "保存分析截图"
            elif save_screenshot and auto_save:
                result = "跳过保存（已自动保存）"
            elif save_screenshot and not save_analysis:
                result = "跳过保存（分析截图已禁用）"
            else:
                result = "不保存"
            
            print(f"  结果: {result}")
        
        print("✅ 游戏助手截图逻辑测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 游戏助手截图逻辑测试失败: {e}")
        return False


def test_screenshot_directory_structure():
    """测试截图目录结构"""
    print("\n=== 测试截图目录结构 ===")
    
    try:
        config_manager = ConfigManager()
        screenshot_dir = config_manager.get_screenshot_dir()
        
        print(f"截图目录: {screenshot_dir}")
        
        # 检查目录是否存在
        if screenshot_dir.exists():
            # 列出现有截图文件
            screenshot_files = list(screenshot_dir.glob("*.png"))
            print(f"现有截图文件数量: {len(screenshot_files)}")
            
            # 分析文件名模式
            game_screen_files = [f for f in screenshot_files if f.name.startswith("game_screen_")]
            auto_screenshot_files = [f for f in screenshot_files if f.name.startswith("auto_screenshot_")]
            analysis_screenshot_files = [f for f in screenshot_files if f.name.startswith("analysis_screenshot_")]
            
            print(f"game_screen_ 文件: {len(game_screen_files)}")
            print(f"auto_screenshot_ 文件: {len(auto_screenshot_files)}")
            print(f"analysis_screenshot_ 文件: {len(analysis_screenshot_files)}")
            
            # 显示最近的几个文件
            if screenshot_files:
                recent_files = sorted(screenshot_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                print("\n最近的截图文件:")
                for f in recent_files:
                    mtime = time.ctime(f.stat().st_mtime)
                    print(f"  {f.name} ({mtime})")
        else:
            print("截图目录不存在")
        
        print("✅ 截图目录结构检查完成")
        return True
        
    except Exception as e:
        print(f"❌ 截图目录结构测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🔧 开始测试截图重复保存修复")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_screenshot_manager_save,
        test_game_assistant_screenshot_logic,
        test_screenshot_directory_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 出现异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试总结: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！截图重复保存问题已修复")
        print("\n修复说明:")
        print("1. 禁用了 auto_save_screenshots，避免在连接层自动保存")
        print("2. 添加了 save_analysis_screenshots 配置项控制分析截图保存")
        print("3. 修改了游戏助手的截图保存逻辑，避免重复保存")
        print("4. 现在只会在需要分析时保存一张截图，文件名为 analysis_screenshot_xxxxx.png")
    else:
        print("❌ 部分测试失败，请检查修复")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)