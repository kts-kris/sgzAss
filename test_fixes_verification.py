#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复验证测试脚本
验证图像质量优化和SystemConfig错误修复是否生效
"""

import asyncio
import sys
import os
from pathlib import Path
import time
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config, get_config_manager
from src.services.ollama_vlm import OllamaVLMService
from src.services.async_analysis_manager import AsyncAnalysisManager
from src.services.connection import ConnectionService
from src.controllers.game_assistant import GameAssistant

class FixesVerificationTest:
    """修复验证测试类"""
    
    def __init__(self):
        self.config = get_config()
        self.config_manager = get_config_manager()
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        result = f"{status} {test_name}"
        if message:
            result += f": {message}"
        print(result)
        self.test_results.append((test_name, success, message))
        
    def test_config_loading(self):
        """测试配置加载"""
        try:
            # 检查图像质量配置
            ollama_config = self.config.vision.ollama_config
            
            # 验证图像尺寸配置
            expected_size = [800, 600]
            actual_size = list(ollama_config.image_max_size)
            size_correct = actual_size == expected_size
            
            # 验证图像质量配置
            expected_quality = 75
            actual_quality = ollama_config.image_quality
            quality_correct = actual_quality == expected_quality
            
            if size_correct and quality_correct:
                self.log_test_result(
                    "配置加载", True, 
                    f"图像尺寸: {actual_size}, 质量: {actual_quality}"
                )
            else:
                self.log_test_result(
                    "配置加载", False,
                    f"期望尺寸: {expected_size}, 实际: {actual_size}; 期望质量: {expected_quality}, 实际: {actual_quality}"
                )
                
        except Exception as e:
            self.log_test_result("配置加载", False, str(e))
            
    def test_ollama_vlm_initialization(self):
        """测试OllamaVLMService初始化"""
        try:
            ollama_config = self.config.vision.ollama_config
            
            # 创建OllamaVLMService实例
            vlm_service = OllamaVLMService(
                host=ollama_config.host,
                port=ollama_config.port,
                model=ollama_config.model,
                timeout=ollama_config.timeout,
                image_max_size=ollama_config.image_max_size,
                image_quality=ollama_config.image_quality
            )
            
            # 验证参数是否正确设置
            size_correct = vlm_service.image_max_size == ollama_config.image_max_size
            quality_correct = vlm_service.image_quality == ollama_config.image_quality
            
            if size_correct and quality_correct:
                self.log_test_result(
                    "OllamaVLM初始化", True,
                    f"图像参数正确设置: 尺寸{vlm_service.image_max_size}, 质量{vlm_service.image_quality}"
                )
            else:
                self.log_test_result(
                    "OllamaVLM初始化", False,
                    f"参数设置错误: 尺寸{vlm_service.image_max_size}, 质量{vlm_service.image_quality}"
                )
                
        except Exception as e:
            self.log_test_result("OllamaVLM初始化", False, str(e))
            
    async def test_async_analysis_manager(self):
        """测试AsyncAnalysisManager的get_screenshot_dir方法"""
        try:
            connection_service = ConnectionService()
            async_manager = AsyncAnalysisManager(
                config_manager=self.config_manager,
                connection_service=connection_service
            )
            
            # 测试get_screenshot_dir方法是否存在且可调用
            screenshot_dir = async_manager.config.get_screenshot_dir()
            
            if isinstance(screenshot_dir, Path):
                self.log_test_result(
                    "AsyncAnalysisManager截图目录", True,
                    f"截图目录: {screenshot_dir}"
                )
            else:
                self.log_test_result(
                    "AsyncAnalysisManager截图目录", False,
                    f"返回类型错误: {type(screenshot_dir)}"
                )
                
        except AttributeError as e:
            if "get_screenshot_dir" in str(e):
                self.log_test_result(
                    "AsyncAnalysisManager截图目录", False,
                    "get_screenshot_dir方法不存在"
                )
            else:
                self.log_test_result(
                    "AsyncAnalysisManager截图目录", False,
                    str(e)
                )
        except Exception as e:
            self.log_test_result("AsyncAnalysisManager截图目录", False, str(e))
            
    async def test_game_assistant_initialization(self):
        """测试GameAssistant初始化"""
        try:
            assistant = GameAssistant()
            
            # 检查OllamaVLMService是否正确初始化
            if assistant.ollama_service:
                vlm_service = assistant.ollama_service
                
                # 验证图像参数
                expected_size = self.config.vision.ollama_config.image_max_size
                expected_quality = self.config.vision.ollama_config.image_quality
                
                size_correct = vlm_service.image_max_size == expected_size
                quality_correct = vlm_service.image_quality == expected_quality
                
                if size_correct and quality_correct:
                    self.log_test_result(
                        "GameAssistant初始化", True,
                        f"VLM服务图像参数正确: 尺寸{vlm_service.image_max_size}, 质量{vlm_service.image_quality}"
                    )
                else:
                    self.log_test_result(
                        "GameAssistant初始化", False,
                        f"VLM服务图像参数错误: 期望尺寸{expected_size}, 实际{vlm_service.image_max_size}; 期望质量{expected_quality}, 实际{vlm_service.image_quality}"
                    )
            else:
                self.log_test_result(
                    "GameAssistant初始化", False,
                    "OllamaVLMService未初始化"
                )
                
        except Exception as e:
            self.log_test_result("GameAssistant初始化", False, str(e))
            
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("🔍 修复验证测试总结")
        print("="*60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"\n📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("\n🎉 所有修复验证通过！")
            print("\n✅ 修复内容:")
            print("   • 图像质量优化参数已正确应用")
            print("   • SystemConfig.get_screenshot_dir错误已修复")
            print("   • OllamaVLMService初始化已更新")
            print("   • AsyncAnalysisManager配置已修正")
            print("   • GameAssistant服务初始化已完善")
        else:
            print("\n⚠️  部分测试失败，请检查以下问题:")
            for test_name, success, message in self.test_results:
                if not success:
                    print(f"   • {test_name}: {message}")
                    
        print("\n" + "="*60)
        
async def main():
    """主函数"""
    print("🔧 开始修复验证测试...")
    print("="*60)
    
    tester = FixesVerificationTest()
    
    # 运行测试
    print("\n1. 测试配置加载...")
    tester.test_config_loading()
    
    print("\n2. 测试OllamaVLM初始化...")
    tester.test_ollama_vlm_initialization()
    
    print("\n3. 测试AsyncAnalysisManager...")
    await tester.test_async_analysis_manager()
    
    print("\n4. 测试GameAssistant初始化...")
    await tester.test_game_assistant_initialization()
    
    # 打印总结
    tester.print_summary()
    
if __name__ == "__main__":
    asyncio.run(main())