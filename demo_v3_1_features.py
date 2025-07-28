#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国志霸王大陆游戏助手 v3.1 新功能演示

本脚本演示 v3.1 版本的核心新功能：
1. 截图自动清理
2. 提示词配置化
3. VLM效率优化
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append('.')

from src.utils.config import get_config_manager
from src.utils.screenshot import ScreenshotManager
from src.utils.prompt_manager import get_prompt_manager
from src.services.ollama_vlm import OllamaVLMService


def demo_screenshot_cleanup():
    """演示截图自动清理功能"""
    print("\n=== 📸 截图自动清理功能演示 ===")
    
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    # 显示截图配置
    print(f"📋 当前截图配置:")
    print(f"   最大保留数量: {config.screenshot.max_keep_count}")
    print(f"   自动清理: {config.screenshot.auto_cleanup}")
    print(f"   保存时清理: {config.screenshot.cleanup_on_save}")
    print(f"   清理模式: {config.screenshot.cleanup_patterns}")
    
    # 创建截图管理器
    screenshot_manager = ScreenshotManager(config)
    
    # 检查当前截图数量
    screenshot_dir = Path(config.screenshot_dir)
    if screenshot_dir.exists():
        current_files = screenshot_manager.get_screenshot_files(str(screenshot_dir))
        print(f"📁 当前截图文件数量: {len(current_files)}")
        
        if len(current_files) > config.screenshot.max_keep_count:
            print(f"🧹 触发自动清理，将保留最新 {config.screenshot.max_keep_count} 张截图")
            screenshot_manager.cleanup_old_screenshots(str(screenshot_dir))
            
            # 再次检查
            remaining_files = screenshot_manager.get_screenshot_files(str(screenshot_dir))
            print(f"✅ 清理完成，剩余文件: {len(remaining_files)}")
        else:
            print(f"✅ 文件数量在限制范围内，无需清理")
    else:
        print(f"📁 截图目录不存在: {screenshot_dir}")


def demo_prompt_manager():
    """演示提示词配置化功能"""
    print("\n=== 📝 提示词配置化功能演示 ===")
    
    prompt_manager = get_prompt_manager()
    
    # 显示可用的提示词类别
    print("📋 可用提示词类别:")
    categories = ["game_analysis", "ui_elements", "action_suggestion", "efficient_analysis"]
    
    for category in categories:
        prompt = prompt_manager.get_prompt(category, "zh")
        if prompt:
            print(f"   ✅ {category}: 已加载 ({len(prompt)} 字符)")
        else:
            print(f"   ❌ {category}: 未找到")
    
    # 演示获取优化提示词
    print("\n🎯 获取优化提示词:")
    optimized_prompt = prompt_manager.get_optimized_prompt("game_analysis", "zh")
    print(f"   优化提示词长度: {len(optimized_prompt)} 字符")
    
    # 显示性能统计
    print("\n📊 提示词性能统计:")
    stats = prompt_manager.get_prompt_stats()
    if stats:
        for category, count in stats.items():
            print(f"   {category}: 使用次数 {count}")
    else:
        print("   暂无统计数据")


async def demo_vlm_optimization():
    """演示VLM效率优化功能"""
    print("\n=== 🧠 VLM效率优化功能演示 ===")
    
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    # 检查VLM配置
    vlm_config = config.get_vlm_config()
    print(f"📋 VLM配置:")
    print(f"   主机: {vlm_config.host}:{vlm_config.port}")
    print(f"   模型: {vlm_config.model}")
    print(f"   超时时间: {vlm_config.timeout}s")
    print(f"   最大重试: {vlm_config.max_retries}")
    print(f"   图像质量: {vlm_config.image_quality}%")
    
    # 创建VLM服务（仅演示，不实际调用）
    try:
        vlm_service = OllamaVLMService(config)
        print(f"✅ VLM服务初始化成功")
        
        # 显示提示词统计
        stats = vlm_service.get_prompt_stats()
        if stats:
            print(f"📊 提示词使用统计:")
            for category, count in stats.items():
                print(f"   {category}: {count} 次使用")
        else:
            print(f"📊 暂无提示词使用统计")
            
    except Exception as e:
        print(f"⚠️ VLM服务初始化失败: {e}")
        print(f"   这是正常的，因为可能没有运行Ollama服务")


def demo_config_customization():
    """演示配置自定义功能"""
    print("\n=== ⚙️ 配置自定义功能演示 ===")
    
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    print("📋 当前配置概览:")
    print(f"   调试模式: {config.debug_mode}")
    print(f"   截图目录: {config.screenshot_dir}")
    print(f"   日志级别: {config.logging.level}")
    print(f"   性能监控: {config.performance_monitoring}")
    
    print("\n📝 提示词配置:")
    print(f"   配置文件: {config.prompt.config_file}")
    print(f"   默认语言: {config.prompt.default_language}")
    print(f"   启用优化: {config.prompt.enable_optimization}")
    print(f"   优化频率: {config.prompt.optimization_frequency}")
    print(f"   缓存提示词: {config.prompt.cache_prompts}")
    print(f"   回退机制: {config.prompt.fallback_to_builtin}")
    
    print("\n📸 截图配置:")
    print(f"   最大保留: {config.screenshot.max_keep_count}")
    print(f"   自动清理: {config.screenshot.auto_cleanup}")
    print(f"   保存时清理: {config.screenshot.cleanup_on_save}")
    print(f"   清理模式: {config.screenshot.cleanup_patterns}")
    
    # 演示配置文件检查
    config_file = Path("config.yaml")
    prompts_file = Path(config.prompt.config_file)
    
    print("\n📁 配置文件状态:")
    print(f"   config.yaml: {'✅ 存在' if config_file.exists() else '❌ 不存在'}")
    print(f"   prompts.yaml: {'✅ 存在' if prompts_file.exists() else '❌ 不存在'}")


def print_upgrade_tips():
    """显示升级提示"""
    print("\n=== 🚀 v3.1 升级提示 ===")
    print("")
    print("🎯 主要改进:")
    print("   1. 截图自动清理 - 节省磁盘空间")
    print("   2. 提示词配置化 - 便于调优")
    print("   3. VLM效率优化 - 提升识别准确性")
    print("")
    print("⚙️ 配置建议:")
    print("   • 根据磁盘空间调整截图保留数量")
    print("   • 根据游戏特点自定义提示词")
    print("   • 监控VLM性能统计进行优化")
    print("")
    print("\n📚 更多信息:")
    print("   • 查看 v3.1_release_notes.md 了解详细功能")
    print("   • 运行 test_v3_1_features.py 验证功能")
    print("   • 编辑 prompts.yaml 自定义提示词")


async def main():
    """主演示函数"""
    print("🎮 三国志霸王大陆游戏助手 v3.1 新功能演示")
    print("=" * 50)
    
    try:
        # 演示各项新功能
        demo_screenshot_cleanup()
        demo_prompt_manager()
        await demo_vlm_optimization()
        demo_config_customization()
        print_upgrade_tips()
        
        print("\n✅ 所有功能演示完成！")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("请检查配置文件和依赖是否正确安装")


if __name__ == "__main__":
    asyncio.run(main())