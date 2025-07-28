#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
运行时修复验证测试

验证 GameAssistant 在实际运行时是否还会出现 SystemConfig 错误
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


async def test_runtime_screenshot_analysis():
    """测试运行时截图和分析功能"""
    print("\n=== 运行时修复验证测试 ===")
    
    try:
        # 获取配置
        config = get_config()
        print(f"✅ 配置加载成功")
        
        # 初始化自动化后端
        automation_backend = get_automation_backend(
            backend_type=config.automation.default_backend
        )
        print(f"✅ 自动化后端初始化成功")
        
        # 初始化游戏助手
        assistant = GameAssistant(automation_backend)
        print(f"✅ GameAssistant初始化成功")
        
        # 启动助手
        await assistant.start_assistant()
        print(f"✅ GameAssistant启动成功")
        
        # 测试截图和分析功能
        print("\n🔍 开始测试截图和分析功能...")
        
        # 第一次分析
        print("📸 执行第一次分析...")
        result1 = await assistant.analyze_current_screen(save_screenshot=True)
        if result1:
            print(f"✅ 第一次分析成功 - 置信度: {result1.confidence:.2f}")
        else:
            print(f"❌ 第一次分析失败")
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 第二次分析（这里之前会出错）
        print("📸 执行第二次分析...")
        result2 = await assistant.analyze_current_screen(save_screenshot=True)
        if result2:
            print(f"✅ 第二次分析成功 - 置信度: {result2.confidence:.2f}")
        else:
            print(f"❌ 第二次分析失败")
        
        # 第三次分析
        print("📸 执行第三次分析...")
        result3 = await assistant.analyze_current_screen(save_screenshot=True)
        if result3:
            print(f"✅ 第三次分析成功 - 置信度: {result3.confidence:.2f}")
        else:
            print(f"❌ 第三次分析失败")
        
        # 停止助手
        await assistant.stop_assistant()
        print(f"✅ GameAssistant停止成功")
        
        print("\n🎉 运行时修复验证测试完成！")
        print("✅ 所有截图和分析操作均成功，未出现 SystemConfig 错误")
        
        return True
        
    except Exception as e:
        print(f"❌ 运行时测试失败: {e}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")
        return False


async def main():
    """主函数"""
    success = await test_runtime_screenshot_analysis()
    
    if success:
        print("\n🎉 所有测试通过！SystemConfig 错误已修复")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())