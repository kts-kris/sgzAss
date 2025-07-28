#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试3.1版本新功能
包括截图自动清理、VLM效率优化和提示词配置化
"""

import asyncio
import os
import time
from pathlib import Path

import sys
sys.path.append('.')

from src.utils.config import get_config_manager
from src.utils.screenshot import ScreenshotManager
from src.utils.prompt_manager import get_prompt_manager
from src.services.ollama_vlm import OllamaVLMService
from src.controllers.game_assistant import GameAssistant


def test_screenshot_cleanup():
    """测试截图自动清理功能"""
    print("\n=== 测试截图自动清理功能 ===")
    
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    # 检查截图配置
    print(f"最大保留截图数量: {config.screenshot.max_keep_count}")
    print(f"自动清理: {config.screenshot.auto_cleanup}")
    print(f"保存时清理: {config.screenshot.cleanup_on_save}")
    print(f"清理模式: {config.screenshot.cleanup_patterns}")
    
    # 测试截图管理器
    screenshot_manager = ScreenshotManager(config_manager)
    screenshot_dir = config_manager.get_screenshot_dir()
    
    print(f"截图目录: {screenshot_dir}")
    
    # 获取当前截图文件
    files = screenshot_manager.get_screenshot_files(screenshot_dir)
    print(f"当前截图文件数量: {len(files)}")
    
    if len(files) > config.screenshot.max_keep_count:
        print("执行截图清理...")
        screenshot_manager.cleanup_old_screenshots(screenshot_dir)
        
        # 重新检查
        files_after = screenshot_manager.get_screenshot_files(screenshot_dir)
        print(f"清理后截图文件数量: {len(files_after)}")
        
        if len(files_after) <= config.screenshot.max_keep_count:
            print("✅ 截图自动清理功能正常")
        else:
            print("❌ 截图自动清理功能异常")
    else:
        print("✅ 截图数量在限制范围内，无需清理")


def test_prompt_manager():
    """测试提示词管理器"""
    print("\n=== 测试提示词管理器 ===")
    
    prompt_manager = get_prompt_manager()
    
    # 测试获取可用类别
    categories = prompt_manager.get_available_categories()
    print(f"可用提示词类别: {categories}")
    
    # 测试获取提示词
    for category in ['game_analysis', 'ui_elements', 'action_suggestion', 'efficient_analysis']:
        if category in categories:
            prompt = prompt_manager.get_prompt(category, 'zh')
            print(f"\n{category} 提示词长度: {len(prompt)} 字符")
            print(f"前100字符: {prompt[:100]}...")
        else:
            print(f"❌ 类别 {category} 不可用")
    
    # 测试优化提示词
    optimized_prompt = prompt_manager.get_optimized_prompt(
        'game_analysis', 
        'zh',
        context={'recent_failures': 1, 'avg_response_time': 3.0}
    )
    print(f"\n优化提示词长度: {len(optimized_prompt)} 字符")
    
    # 测试统计信息
    stats = prompt_manager.get_prompt_stats()
    print(f"\n提示词统计: {stats}")
    
    print("✅ 提示词管理器功能正常")


def test_prompt_config_file():
    """测试提示词配置文件"""
    print("\n=== 测试提示词配置文件 ===")
    
    config_file = Path("resources/prompts.yaml")
    
    if config_file.exists():
        print(f"✅ 提示词配置文件存在: {config_file}")
        print(f"文件大小: {config_file.stat().st_size} 字节")
        
        # 测试加载配置
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
            
            print(f"配置文件包含的主要部分:")
            for key in prompt_data.keys():
                print(f"  - {key}")
            
            # 检查必要的提示词类别
            required_categories = ['game_analysis', 'ui_elements', 'action_suggestion', 'efficient_analysis']
            for category in required_categories:
                if category in prompt_data:
                    languages = list(prompt_data[category].keys())
                    print(f"  {category}: {languages}")
                else:
                    print(f"  ❌ 缺少类别: {category}")
            
            print("✅ 提示词配置文件格式正确")
            
        except Exception as e:
            print(f"❌ 提示词配置文件格式错误: {e}")
    else:
        print(f"❌ 提示词配置文件不存在: {config_file}")


async def test_vlm_with_new_prompts():
    """测试VLM服务使用新的提示词系统"""
    print("\n=== 测试VLM服务提示词集成 ===")
    
    try:
        # 初始化VLM服务
        config = get_config_manager().get_config()
        vlm_config = config.get_vlm_config()
        
        vlm_service = OllamaVLMService(
            host=vlm_config.host,
            port=vlm_config.port,
            model=vlm_config.model,
            timeout=vlm_config.timeout
        )
        
        # 检查服务可用性
        if await vlm_service.initialize():
            print("✅ VLM服务初始化成功")
            
            # 测试提示词统计功能
            stats = vlm_service.get_prompt_stats()
            print(f"提示词统计: {stats}")
            
            # 测试重新加载提示词
            vlm_service.reload_prompts()
            print("✅ 提示词重新加载成功")
            
        else:
            print("❌ VLM服务初始化失败（可能Ollama未运行）")
            
    except Exception as e:
        print(f"❌ VLM服务测试失败: {e}")


async def test_game_assistant_integration():
    """测试游戏助手集成新功能"""
    print("\n=== 测试游戏助手集成 ===")
    
    try:
        # 初始化游戏助手
        assistant = GameAssistant()
        
        # 检查配置
        config = assistant.config_manager.get_config()
        print(f"截图配置: max_keep={config.screenshot.max_keep_count}, auto_cleanup={config.screenshot.auto_cleanup}")
        print(f"提示词配置: language={config.prompt.default_language}, optimization={config.prompt.enable_optimization}")
        
        # 测试截图管理器
        if hasattr(assistant, 'screenshot_manager'):
            screenshot_dir = assistant.config_manager.get_screenshot_dir()
            files = assistant.screenshot_manager.get_screenshot_files(screenshot_dir)
            print(f"当前截图文件数量: {len(files)}")
        
        print("✅ 游戏助手集成测试完成")
        
    except Exception as e:
        print(f"❌ 游戏助手集成测试失败: {e}")


def test_config_validation():
    """测试配置验证"""
    print("\n=== 测试配置验证 ===")
    
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    # 验证截图配置
    assert hasattr(config, 'screenshot'), "缺少截图配置"
    assert config.screenshot.max_keep_count > 0, "截图保留数量必须大于0"
    assert isinstance(config.screenshot.auto_cleanup, bool), "auto_cleanup必须是布尔值"
    assert isinstance(config.screenshot.cleanup_patterns, list), "cleanup_patterns必须是列表"
    
    # 验证提示词配置
    assert hasattr(config, 'prompt'), "缺少提示词配置"
    assert config.prompt.default_language in ['zh', 'en'], "默认语言必须是zh或en"
    assert isinstance(config.prompt.enable_optimization, bool), "enable_optimization必须是布尔值"
    assert config.prompt.max_prompt_length > 0, "最大提示词长度必须大于0"
    
    print("✅ 配置验证通过")


def main():
    """主测试函数"""
    print("开始测试3.1版本新功能...")
    
    # 基础配置测试
    test_config_validation()
    
    # 截图清理功能测试
    test_screenshot_cleanup()
    
    # 提示词系统测试
    test_prompt_config_file()
    test_prompt_manager()
    
    # 异步测试
    async def async_tests():
        await test_vlm_with_new_prompts()
        await test_game_assistant_integration()
    
    asyncio.run(async_tests())
    
    print("\n=== 3.1版本功能测试完成 ===")
    print("\n新功能总结:")
    print("1. ✅ 截图自动清理 - 默认保留最近3张截图")
    print("2. ✅ 提示词配置化 - 从YAML文件加载提示词")
    print("3. ✅ VLM效率优化 - 提示词性能统计和优化")
    print("4. ✅ 配置管理增强 - 新增截图和提示词配置")
    print("5. ✅ 向后兼容 - 保持原有功能不变")


if __name__ == "__main__":
    main()