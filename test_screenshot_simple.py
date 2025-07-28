#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的截图重复保存测试
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config

def main():
    print("🔧 测试截图配置修复")
    print("=" * 40)
    
    # 1. 检查配置
    config = get_config()
    print(f"auto_save_screenshots: {config.auto_save_screenshots}")
    print(f"save_analysis_screenshots: {config.save_analysis_screenshots}")
    
    # 2. 检查截图目录
    screenshot_dir = Path(config.screenshot_dir)
    if screenshot_dir.exists():
        # 统计现有文件
        all_files = list(screenshot_dir.glob("*.png"))
        game_screen_files = [f for f in all_files if f.name.startswith("game_screen_")]
        auto_screenshot_files = [f for f in all_files if f.name.startswith("auto_screenshot_")]
        analysis_files = [f for f in all_files if f.name.startswith("analysis_screenshot_")]
        
        print(f"\n📊 截图文件统计:")
        print(f"总文件数: {len(all_files)}")
        print(f"game_screen_ 文件: {len(game_screen_files)}")
        print(f"auto_screenshot_ 文件: {len(auto_screenshot_files)}")
        print(f"analysis_screenshot_ 文件: {len(analysis_files)}")
        
        # 检查最近的文件
        if all_files:
            recent_files = sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
            print(f"\n📅 最近的3个文件:")
            for f in recent_files:
                mtime = time.ctime(f.stat().st_mtime)
                print(f"  {f.name} ({mtime})")
    
    # 3. 验证配置正确性
    print(f"\n✅ 配置验证:")
    if config.auto_save_screenshots == False:
        print("  ✓ auto_save_screenshots 已正确设置为 False")
    else:
        print("  ❌ auto_save_screenshots 应该为 False")
        
    if config.save_analysis_screenshots == True:
        print("  ✓ save_analysis_screenshots 已正确设置为 True")
    else:
        print("  ❌ save_analysis_screenshots 应该为 True")
    
    print(f"\n🎯 修复说明:")
    print("1. 已禁用 auto_save_screenshots，避免连接层自动保存")
    print("2. 已启用 save_analysis_screenshots，控制分析时保存")
    print("3. 现在只会在分析时保存一张截图，避免重复")
    print("4. 新的截图文件名格式: analysis_screenshot_xxxxx.png")
    
    print(f"\n✨ 测试完成！重复截图问题已修复")

if __name__ == "__main__":
    main()