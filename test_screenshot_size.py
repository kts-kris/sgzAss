#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试截图尺寸优化是否生效

验证保存的截图是否使用了优化后的尺寸配置
"""

import sys
import asyncio
from pathlib import Path
from PIL import Image
import numpy as np
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.controllers.game_assistant import GameAssistant
from src.utils.config import get_config, get_config_manager
from src.services.ollama_vlm import OllamaVLMService

async def test_screenshot_optimization():
    """测试截图优化功能"""
    print("🔧 测试截图尺寸优化")
    print("=" * 50)
    
    # 1. 检查配置
    config = get_config()
    config_manager = get_config_manager()
    
    print(f"📋 配置信息:")
    print(f"   图像最大尺寸: {config.vision.ollama_config.image_max_size}")
    print(f"   图像质量: {config.vision.ollama_config.image_quality}")
    print(f"   截图目录: {config_manager.get_screenshot_dir()}")
    
    # 2. 初始化游戏助手
    print(f"\n🎮 初始化游戏助手...")
    assistant = GameAssistant()
    
    try:
        # 3. 启动服务
        await assistant.start_assistant()
        print(f"✅ 游戏助手启动成功")
        
        # 4. 获取一张截图
        print(f"\n📸 获取截图...")
        screenshot = assistant.connection_service.get_screenshot()
        
        if screenshot is not None:
            print(f"✅ 原始截图尺寸: {screenshot.shape[1]}x{screenshot.shape[0]}")
            
            # 5. 测试VLM服务的图像处理
            print(f"\n🤖 测试VLM图像处理...")
            vlm_service = assistant.ollama_service
            
            if vlm_service:
                # 使用VLM服务的_prepare_image方法处理图像
                processed_image = await vlm_service._prepare_image(screenshot)
                
                if processed_image:
                    # 获取处理后的图像尺寸
                    if isinstance(processed_image, str):  # base64字符串
                        import base64
                        import io
                        image_data = base64.b64decode(processed_image)
                        pil_image = Image.open(io.BytesIO(image_data))
                        processed_size = pil_image.size
                    else:
                        processed_size = processed_image.size if hasattr(processed_image, 'size') else "未知"
                    
                    print(f"✅ VLM处理后尺寸: {processed_size}")
                    
                    # 验证尺寸是否符合配置
                    expected_max_size = tuple(config.vision.ollama_config.image_max_size)
                    if isinstance(processed_size, tuple):
                        if (processed_size[0] <= expected_max_size[0] and 
                            processed_size[1] <= expected_max_size[1]):
                            print(f"🎉 图像尺寸优化生效！处理后尺寸 {processed_size} 符合配置 {expected_max_size}")
                        else:
                            print(f"⚠️  图像尺寸可能未优化：处理后 {processed_size} 超过配置 {expected_max_size}")
                    else:
                        print(f"⚠️  无法验证处理后的图像尺寸")
                else:
                    print(f"❌ VLM图像处理失败")
            else:
                print(f"❌ VLM服务未初始化")
            
            # 6. 测试保存截图
            print(f"\n💾 测试截图保存...")
            screenshot_path = assistant.screenshot_manager.save_screenshot_sync(
                screenshot=screenshot,
                filename="test_optimization.png"
            )
            
            if screenshot_path:
                print(f"✅ 截图已保存: {screenshot_path}")
                
                # 检查保存的文件尺寸
                saved_image = Image.open(screenshot_path)
                saved_size = saved_image.size
                print(f"📏 保存的截图尺寸: {saved_size}")
                
                # 注意：保存的截图可能是原始尺寸，因为save_screenshot_sync不会压缩
                # VLM处理时才会应用尺寸优化
                
            else:
                print(f"❌ 截图保存失败")
        else:
            print(f"❌ 无法获取截图")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        logger.exception("测试异常")
        
    finally:
        # 清理
        print(f"\n🧹 清理资源...")
        await assistant.stop_assistant()
        print(f"✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_screenshot_optimization())