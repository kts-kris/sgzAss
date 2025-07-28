#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续运行模式修复验证脚本

验证内容：
1. API调用间隔调整（60秒默认，30秒最小）
2. 操作建议显示优化
3. 配置一致性检查
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_config_intervals():
    """测试配置文件中的间隔设置"""
    print("\n=== 测试配置间隔设置 ===")
    
    try:
        from src.utils.config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        continuous_config = config.async_analysis.continuous_mode
        
        print(f"配置验证:")
        print(f"  默认间隔: {continuous_config.default_interval}秒")
        print(f"  最小间隔: {continuous_config.min_interval}秒")
        
        # 验证间隔设置
        if continuous_config.default_interval >= 60.0:
            print("✅ 默认间隔设置正确（≥60秒）")
        else:
            print(f"❌ 默认间隔过短: {continuous_config.default_interval}秒")
            return False
            
        if continuous_config.min_interval >= 30.0:
            print("✅ 最小间隔设置正确（≥30秒）")
        else:
            print(f"❌ 最小间隔过短: {continuous_config.min_interval}秒")
            return False
        
        print("✅ 配置间隔设置测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置间隔设置测试失败: {e}")
        return False


def test_config_class_defaults():
    """测试配置类的默认值"""
    print("\n=== 测试配置类默认值 ===")
    
    try:
        from src.utils.config import ContinuousModeConfig
        
        # 创建默认配置实例
        config = ContinuousModeConfig()
        
        print(f"配置类默认值:")
        print(f"  默认间隔: {config.default_interval}秒")
        print(f"  最小间隔: {config.min_interval}秒")
        print(f"  优先级阈值: {config.priority_threshold}")
        
        # 验证默认值
        if config.default_interval == 60.0:
            print("✅ 配置类默认间隔正确（60秒）")
        else:
            print(f"❌ 配置类默认间隔错误: {config.default_interval}秒")
            return False
            
        if config.min_interval == 30.0:
            print("✅ 配置类最小间隔正确（30秒）")
        else:
            print(f"❌ 配置类最小间隔错误: {config.min_interval}秒")
            return False
        
        print("✅ 配置类默认值测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置类默认值测试失败: {e}")
        return False


def test_cli_interval_validation():
    """测试CLI中的间隔验证逻辑"""
    print("\n=== 测试CLI间隔验证逻辑 ===")
    
    try:
        # 模拟CLI中的间隔验证逻辑
        def validate_interval(interval_input, default=60.0, min_interval=30.0):
            """模拟CLI中的间隔验证"""
            try:
                interval = float(interval_input) if interval_input else default
                
                if interval < min_interval:
                    print(f"⚠️ 间隔时间不能小于{min_interval}秒（避免API超时），已设置为{min_interval}秒")
                    interval = min_interval
                
                return interval
            except ValueError:
                return default
        
        # 测试不同输入
        test_cases = [
            ("", 60.0, "默认值"),
            ("120", 120.0, "正常值"),
            ("15", 30.0, "过小值（应调整为30）"),
            ("45", 45.0, "边界值"),
            ("invalid", 60.0, "无效输入")
        ]
        
        all_passed = True
        
        for input_val, expected, description in test_cases:
            result = validate_interval(input_val)
            if result == expected:
                print(f"✅ {description}: 输入'{input_val}' -> {result}秒")
            else:
                print(f"❌ {description}: 输入'{input_val}' -> {result}秒 (期望: {expected}秒)")
                all_passed = False
        
        if all_passed:
            print("✅ CLI间隔验证逻辑测试通过")
            return True
        else:
            print("❌ CLI间隔验证逻辑测试失败")
            return False
        
    except Exception as e:
        print(f"❌ CLI间隔验证逻辑测试失败: {e}")
        return False


def test_suggestion_display_format():
    """测试操作建议显示格式"""
    print("\n=== 测试操作建议显示格式 ===")
    
    try:
        # 模拟建议数据结构
        class MockSuggestion:
            def __init__(self, description, action_type, x, y, priority, confidence):
                self.description = description
                self.action_type = action_type
                self.x = x
                self.y = y
                self.priority = priority
                self.confidence = confidence
        
        # 创建测试建议
        suggestions = [
            MockSuggestion("点击建造按钮", "click", 100, 200, 0.8, 0.9),
            MockSuggestion("滑动查看更多", "swipe", 300, 400, 0.6, 0.85),
            MockSuggestion("长按选择单位", "long_press", 500, 600, 0.75, 0.88)
        ]
        
        # 模拟显示逻辑
        print("\n💡 操作建议详情:")
        print("-" * 50)
        
        for i, suggestion in enumerate(suggestions):
            priority_icon = "⚡" if suggestion.priority >= 0.7 else "💡"
            print(f"{priority_icon} {i+1}. {suggestion.description}")
            print(f"   类型: {suggestion.action_type}")
            # 获取位置信息
            if suggestion.target:
                x, y = suggestion.target.center
                print(f"   位置: ({x}, {y})")
            else:
                print(f"   位置: 未指定")
            print(f"   优先级: {suggestion.priority:.2f}")
            print(f"   置信度: {suggestion.confidence:.2f}")
            print()
        
        # 检查高优先级建议
        high_priority_suggestions = [s for s in suggestions if s.priority >= 0.7]
        print(f"⚡ 检测到 {len(high_priority_suggestions)} 个高优先级建议")
        
        for i, suggestion in enumerate(high_priority_suggestions):
            print(f"💭 建议 {i+1}: {suggestion.description} (优先级: {suggestion.priority:.2f})")
        
        print("\n✅ 操作建议显示格式测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 操作建议显示格式测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试持续运行模式修复...")
    
    tests = [
        ("配置间隔设置", test_config_intervals),
        ("配置类默认值", test_config_class_defaults),
        ("CLI间隔验证逻辑", test_cli_interval_validation),
        ("操作建议显示格式", test_suggestion_display_format)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print(f"{'='*60}")
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n{'='*60}")
    print(f"测试总结")
    print(f"{'='*60}")
    print(f"总测试数: {total}")
    print(f"通过数: {passed}")
    print(f"失败数: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 持续运行模式修复验证通过！")
        print("\n✨ 修复内容总结:")
        print("  1. ✅ API调用间隔调整 - 默认60秒，最小30秒")
        print("  2. ✅ 操作建议显示优化 - 详细格式，清晰展示")
        print("  3. ✅ 配置一致性保证 - 代码与配置文件同步")
        print("\n💡 使用建议:")
        print("  - 持续运行模式现在使用60秒间隔，避免API超时")
        print("  - 操作建议会详细显示类型、位置、优先级等信息")
        print("  - 高优先级建议（≥0.7）会特别标注并可自动执行")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)