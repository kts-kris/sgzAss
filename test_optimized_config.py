#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证优化后的图像质量配置
"""

import asyncio
import aiohttp
import base64
import time
import yaml
from PIL import Image, ImageDraw
from io import BytesIO
from loguru import logger

class ConfigTester:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "qwen2.5vl:latest"
        self.timeout = 60
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            ollama_config = config.get('vision', {}).get('ollama_config', {})
            return {
                'image_max_size': ollama_config.get('image_max_size', [800, 600]),
                'image_quality': ollama_config.get('image_quality', 75)
            }
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            return {'image_max_size': [800, 600], 'image_quality': 75}
    
    def prepare_test_image(self, max_size, quality) -> str:
        """根据配置准备测试图像"""
        try:
            # 创建一个更复杂的测试图像
            image = Image.new('RGB', (1200, 900), color='white')
            draw = ImageDraw.Draw(image)
            
            # 绘制更多元素来测试分析质量
            # 标题区域
            draw.rectangle([50, 50, 1150, 150], fill='lightblue', outline='navy', width=3)
            draw.text((60, 80), "Game Interface Test", fill='navy')
            
            # 按钮区域
            buttons = [
                {'pos': [100, 200, 250, 280], 'color': 'red', 'text': 'Attack'},
                {'pos': [300, 200, 450, 280], 'color': 'green', 'text': 'Defend'},
                {'pos': [500, 200, 650, 280], 'color': 'blue', 'text': 'Magic'},
                {'pos': [700, 200, 850, 280], 'color': 'orange', 'text': 'Item'}
            ]
            
            for btn in buttons:
                draw.rectangle(btn['pos'], fill=btn['color'], outline='black', width=2)
                # 计算文字位置
                text_x = btn['pos'][0] + 20
                text_y = btn['pos'][1] + 30
                draw.text((text_x, text_y), btn['text'], fill='white')
            
            # 状态栏
            draw.rectangle([100, 350, 850, 450], fill='lightgray', outline='black', width=2)
            draw.text((120, 370), "HP: 100/100", fill='red')
            draw.text((120, 390), "MP: 50/50", fill='blue')
            draw.text((120, 410), "Level: 25", fill='black')
            
            # 小地图
            draw.ellipse([900, 350, 1100, 550], fill='lightgreen', outline='darkgreen', width=3)
            draw.text((920, 440), "Mini Map", fill='darkgreen')
            
            # 聊天框
            draw.rectangle([100, 500, 600, 700], fill='lightyellow', outline='brown', width=2)
            draw.text((120, 520), "Chat Window:", fill='brown')
            draw.text((120, 550), "Player1: Hello!", fill='black')
            draw.text((120, 580), "Player2: Ready?", fill='black')
            
            # 应用配置的压缩设置
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为base64
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            # 计算压缩后的信息
            compressed_size = len(image_base64) * 3 / 4 / 1024  # KB
            
            logger.info(f"✅ 测试图像准备完成")
            logger.info(f"   原始尺寸: 1200x900")
            logger.info(f"   压缩后尺寸: {image.size}")
            logger.info(f"   质量设置: {quality}")
            logger.info(f"   文件大小: {compressed_size:.1f}KB")
            
            return image_base64, compressed_size
            
        except Exception as e:
            logger.error(f"❌ 图像准备失败: {e}")
            raise
    
    async def test_vlm_analysis(self, image_base64: str, config_name: str) -> dict:
        """测试VLM分析性能"""
        prompt = """请详细分析这个游戏界面截图，识别所有可见的UI元素。请用JSON格式回答：
{
  "description": "界面的整体描述",
  "elements": [
    {
      "name": "元素名称",
      "type": "button/text/window/map等",
      "color": "颜色",
      "position": "位置描述",
      "function": "功能描述"
    }
  ],
  "ui_quality": "界面清晰度评价",
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
                "num_predict": 1500
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
                        
                        response_text = data.get("response", "")
                        
                        # 尝试解析JSON响应来评估分析质量
                        import json
                        analysis_quality = "unknown"
                        elements_count = 0
                        
                        try:
                            # 查找JSON部分
                            json_start = response_text.find("{")
                            json_end = response_text.rfind("}") + 1
                            
                            if json_start != -1 and json_end > json_start:
                                json_text = response_text[json_start:json_end]
                                parsed_data = json.loads(json_text)
                                elements_count = len(parsed_data.get("elements", []))
                                analysis_quality = parsed_data.get("ui_quality", "unknown")
                        except:
                            pass
                        
                        result = {
                            "config_name": config_name,
                            "processing_time": processing_time,
                            "response_length": len(response_text),
                            "elements_detected": elements_count,
                            "analysis_quality": analysis_quality,
                            "success": True,
                            "response_preview": response_text[:300] + "..." if len(response_text) > 300 else response_text
                        }
                        
                        logger.info(f"✅ {config_name} - 处理时间: {processing_time:.2f}s")
                        logger.info(f"   检测到元素: {elements_count}个")
                        logger.info(f"   分析质量: {analysis_quality}")
                        
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ {config_name} - API调用失败: {response.status}")
                        return {
                            "config_name": config_name,
                            "processing_time": time.time() - start_time,
                            "success": False,
                            "error": f"{response.status} - {error_text[:100]}"
                        }
                        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ {config_name} - 测试失败: {e}")
            return {
                "config_name": config_name,
                "processing_time": processing_time,
                "success": False,
                "error": str(e)
            }

async def main():
    """主测试函数"""
    logger.info("开始验证优化后的图像质量配置")
    
    tester = ConfigTester()
    
    # 加载当前配置
    current_config = tester.load_config()
    logger.info(f"当前配置: {current_config}")
    
    # 测试配置对比
    test_configs = [
        {
            "name": "原始配置",
            "max_size": [1024, 1024],
            "quality": 85
        },
        {
            "name": "优化配置",
            "max_size": current_config['image_max_size'],
            "quality": current_config['image_quality']
        }
    ]
    
    results = []
    
    for config in test_configs:
        logger.info(f"\n=== 测试 {config['name']} ===")
        logger.info(f"图像尺寸: {config['max_size']}, 质量: {config['quality']}")
        
        try:
            # 准备测试图像
            image_base64, file_size = tester.prepare_test_image(
                max_size=config["max_size"], 
                quality=config["quality"]
            )
            
            # 测试VLM分析
            result = await tester.test_vlm_analysis(image_base64, config["name"])
            result["file_size_kb"] = file_size
            results.append(result)
            
        except Exception as e:
            logger.error(f"配置 {config['name']} 测试失败: {e}")
            results.append({
                "config_name": config["name"],
                "success": False,
                "error": str(e)
            })
        
        # 测试间隔
        await asyncio.sleep(3)
    
    # 分析对比结果
    logger.info("\n=== 配置对比分析 ===")
    
    successful_results = [r for r in results if r.get("success", False)]
    
    if len(successful_results) >= 2:
        original = next((r for r in successful_results if "原始" in r["config_name"]), None)
        optimized = next((r for r in successful_results if "优化" in r["config_name"]), None)
        
        if original and optimized:
            # 性能对比
            time_improvement = ((original["processing_time"] - optimized["processing_time"]) / original["processing_time"]) * 100
            size_reduction = ((original["file_size_kb"] - optimized["file_size_kb"]) / original["file_size_kb"]) * 100
            
            logger.info(f"\n📊 性能对比:")
            logger.info(f"   处理时间: {original['processing_time']:.2f}s → {optimized['processing_time']:.2f}s")
            logger.info(f"   时间改善: {time_improvement:+.1f}%")
            logger.info(f"   文件大小: {original['file_size_kb']:.1f}KB → {optimized['file_size_kb']:.1f}KB")
            logger.info(f"   大小减少: {size_reduction:.1f}%")
            
            # 质量对比
            logger.info(f"\n🔍 分析质量对比:")
            logger.info(f"   原始配置检测元素: {original.get('elements_detected', 0)}个")
            logger.info(f"   优化配置检测元素: {optimized.get('elements_detected', 0)}个")
            logger.info(f"   原始配置分析质量: {original.get('analysis_quality', 'unknown')}")
            logger.info(f"   优化配置分析质量: {optimized.get('analysis_quality', 'unknown')}")
            
            # 总结
            if time_improvement > 0 and optimized.get('elements_detected', 0) >= original.get('elements_detected', 0) * 0.8:
                logger.info(f"\n✅ 优化成功！")
                logger.info(f"   性能提升 {time_improvement:.1f}%，分析质量保持良好")
            elif time_improvement > 0:
                logger.info(f"\n⚠️  优化有效但需注意")
                logger.info(f"   性能提升 {time_improvement:.1f}%，但分析质量可能有所下降")
            else:
                logger.info(f"\n❌ 优化效果不明显")
                logger.info(f"   建议重新调整配置参数")
    
    else:
        logger.error("测试结果不足，无法进行对比分析")
    
    # 显示详细结果
    logger.info("\n📋 详细测试结果:")
    for result in results:
        if result.get("success"):
            logger.info(f"\n{result['config_name']}:")
            logger.info(f"  处理时间: {result['processing_time']:.2f}秒")
            logger.info(f"  文件大小: {result.get('file_size_kb', 0):.1f}KB")
            logger.info(f"  检测元素: {result.get('elements_detected', 0)}个")
            logger.info(f"  响应长度: {result.get('response_length', 0)}字符")
        else:
            logger.error(f"\n{result['config_name']}: 测试失败 - {result.get('error', '未知错误')}")

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