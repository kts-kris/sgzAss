#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的VLM服务测试
"""

import asyncio
import aiohttp
import base64
import time
import numpy as np
from PIL import Image
from io import BytesIO
from loguru import logger

class SimpleVLMTester:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "qwen2.5vl:latest"
        self.timeout = 60
        self.max_retries = 3
    
    async def check_service(self) -> bool:
        """检查Ollama服务"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]
                        logger.info(f"✅ 服务正常，可用模型: {models}")
                        return self.model in models
                    return False
        except Exception as e:
            logger.error(f"❌ 服务检查失败: {e}")
            return False
    
    def prepare_test_image(self, size=(800, 600), quality=85) -> str:
        """创建测试图像"""
        try:
            # 创建一个简单的测试图像
            image = Image.new('RGB', size, color='lightblue')
            
            # 添加一些简单的图形
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(image)
            
            # 绘制一些基本形状
            draw.rectangle([50, 50, 200, 150], fill='red', outline='black')
            draw.ellipse([250, 50, 400, 150], fill='green', outline='black')
            draw.rectangle([450, 50, 600, 150], fill='blue', outline='black')
            
            # 添加文字
            try:
                draw.text((50, 200), "Test Image for VLM", fill='black')
                draw.text((50, 250), "Red Rectangle", fill='black')
                draw.text((250, 250), "Green Circle", fill='black')
                draw.text((450, 250), "Blue Rectangle", fill='black')
            except:
                pass  # 如果字体不可用，跳过文字
            
            # 压缩图像
            max_size = (1024, 1024)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为base64
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            logger.info(f"✅ 测试图像准备完成，尺寸: {image.size}, 质量: {quality}")
            return image_base64
            
        except Exception as e:
            logger.error(f"❌ 图像准备失败: {e}")
            raise
    
    async def test_vlm_analysis(self, image_base64: str, quality_label: str) -> dict:
        """测试VLM分析"""
        prompt = """请分析这张图片，描述你看到的内容。请用JSON格式回答：
{
  "description": "图片的整体描述",
  "elements": [
    {
      "name": "元素名称",
      "type": "元素类型",
      "color": "颜色",
      "position": "位置描述"
    }
  ],
  "confidence": 0.9
}"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 1000
            }
        }
        
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        processing_time = time.time() - start_time
                        
                        # 计算图像大小
                        image_size_kb = len(image_base64) * 3 / 4 / 1024  # base64解码后的大小
                        
                        result = {
                            "quality_label": quality_label,
                            "processing_time": processing_time,
                            "image_size_kb": image_size_kb,
                            "response_length": len(data.get("response", "")),
                            "success": True,
                            "response": data.get("response", "")[:200] + "..." if len(data.get("response", "")) > 200 else data.get("response", "")
                        }
                        
                        logger.info(f"✅ {quality_label} - 处理时间: {processing_time:.2f}s, 图像大小: {image_size_kb:.1f}KB")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ {quality_label} - API调用失败: {response.status} - {error_text}")
                        return {
                            "quality_label": quality_label,
                            "processing_time": time.time() - start_time,
                            "success": False,
                            "error": f"{response.status} - {error_text}"
                        }
                        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ {quality_label} - 测试失败: {e}")
            return {
                "quality_label": quality_label,
                "processing_time": processing_time,
                "success": False,
                "error": str(e)
            }

async def main():
    """主测试函数"""
    logger.info("开始VLM图像质量测试")
    
    tester = SimpleVLMTester()
    
    # 检查服务
    if not await tester.check_service():
        logger.error("Ollama服务或模型不可用，退出测试")
        return
    
    # 测试不同的图像质量配置
    test_configs = [
        {"size": (400, 300), "quality": 60, "label": "低质量(400x300, Q60)"},
        {"size": (800, 600), "quality": 75, "label": "中等质量(800x600, Q75)"},
        {"size": (800, 600), "quality": 85, "label": "当前配置(800x600, Q85)"},
        {"size": (1024, 768), "quality": 85, "label": "高分辨率(1024x768, Q85)"},
        {"size": (800, 600), "quality": 95, "label": "高质量(800x600, Q95)"},
    ]
    
    results = []
    
    for config in test_configs:
        logger.info(f"\n测试配置: {config['label']}")
        
        try:
            # 准备测试图像
            image_base64 = tester.prepare_test_image(
                size=config["size"], 
                quality=config["quality"]
            )
            
            # 测试VLM分析
            result = await tester.test_vlm_analysis(image_base64, config["label"])
            results.append(result)
            
        except Exception as e:
            logger.error(f"配置 {config['label']} 测试失败: {e}")
            results.append({
                "quality_label": config["label"],
                "success": False,
                "error": str(e)
            })
        
        # 测试间隔
        await asyncio.sleep(2)
    
    # 分析结果
    logger.info("\n=== 测试结果分析 ===")
    
    successful_results = [r for r in results if r.get("success", False)]
    
    if successful_results:
        # 按处理时间排序
        successful_results.sort(key=lambda x: x["processing_time"])
        
        logger.info("\n性能排名 (按处理时间):")
        for i, result in enumerate(successful_results, 1):
            logger.info(f"{i}. {result['quality_label']} - {result['processing_time']:.2f}s ({result['image_size_kb']:.1f}KB)")
        
        # 推荐配置
        best_result = successful_results[0]
        logger.info(f"\n🎯 推荐配置: {best_result['quality_label']}")
        logger.info(f"   处理时间: {best_result['processing_time']:.2f}秒")
        logger.info(f"   图像大小: {best_result['image_size_kb']:.1f}KB")
        
    else:
        logger.error("所有测试都失败了")
    
    # 显示失败的测试
    failed_results = [r for r in results if not r.get("success", False)]
    if failed_results:
        logger.info("\n❌ 失败的测试:")
        for result in failed_results:
            logger.error(f"   {result['quality_label']}: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:HH:mm:ss} | {level} | {message}",
        level="INFO",
        colorize=True
    )
    
    # 运行测试
    asyncio.run(main())