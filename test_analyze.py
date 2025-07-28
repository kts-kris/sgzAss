#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试分析功能的脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.controllers.game_assistant import GameAssistant
from src.services.automation import get_automation_backend
from src.utils.config import get_config
from loguru import logger

async def test_analyze():
    """测试分析功能"""
    try:
        # 初始化配置
        config = get_config()
        
        # 初始化自动化后端
        automation_backend = get_automation_backend(
            backend_type=config.automation.default_backend
        )
        
        # 初始化游戏助手
        assistant = GameAssistant(automation_backend)
        
        # 启动助手
        await assistant.start_assistant()
        
        print("\n🎮 游戏助手已启动，开始测试分析功能...")
        
        # 执行分析
        print("\n📸 正在分析当前屏幕...")
        result = await assistant.analyze_current_screen()
        
        if result and result.success:
            print(f"✅ 分析成功！")
            print(f"📊 置信度: {result.confidence:.2f}")
            print(f"⏱️ 分析耗时: {result.analysis_time:.2f}秒")
            print(f"🎯 发现元素: {len(result.elements)}个")
            print(f"💡 操作建议: {len(result.suggestions)}个")
            
            # 显示元素详情
            if result.elements:
                print("\n🔍 发现的元素:")
                for i, element in enumerate(result.elements[:5], 1):  # 只显示前5个
                    print(f"  {i}. {element.name} - {element.element_type.value} ({element.position[0]}, {element.position[1]}) 置信度: {element.confidence:.2f}")
            
            # 显示操作建议
            if result.suggestions:
                print("\n💡 操作建议:")
                for i, suggestion in enumerate(result.suggestions[:3], 1):  # 只显示前3个
                    print(f"  {i}. {suggestion.action_type.value}: {suggestion.description} (优先级: {suggestion.priority}, 置信度: {suggestion.confidence:.2f})")
        else:
            print(f"❌ 分析失败")
            if result and result.error_message:
                print(f"错误信息: {result.error_message}")
        
        # 停止助手
        await assistant.stop_assistant()
        print("\n✅ 测试完成，游戏助手已停止")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analyze())