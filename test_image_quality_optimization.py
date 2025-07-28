#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图像质量优化测试脚本

测试不同图像质量设置对VLM分析性能的影响：
1. 不同JPEG压缩质量（30, 50, 70, 85, 95）
2. 不同图像分辨率（512x512, 768x768, 1024x1024, 1280x1280）
3. 不同图像格式（JPEG vs PNG）

分析指标：
- 处理时间
- 文件大小
- 分析准确性
- API响应时间
"""

import asyncio
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from io import BytesIO
import base64

import cv2
import numpy as np
from PIL import Image
from loguru import logger

# 导入项目模块
from src.services.ollama_vlm import OllamaVLMService
from src.services.connection import ConnectionService
from src.utils.config import ConfigManager
from src.utils.helpers import save_screenshot, get_timestamp

class ImageQualityTester:
    """图像质量优化测试器"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.connection_service = ConnectionService(self.config)
        self.vlm_service = None
        self.test_results = []
        
        # 测试参数
        self.quality_levels = [30, 50, 70, 85, 95]  # JPEG质量
        self.resolution_levels = [
            (512, 512),
            (768, 768), 
            (1024, 1024),
            (1280, 1280)
        ]
        self.formats = ['JPEG', 'PNG']
        
        # 结果保存目录
        self.results_dir = Path("logs/image_quality_tests")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            # 初始化连接服务
            if not await self.connection_service.connect():
                logger.error("无法连接到设备")
                return False
                
            # 初始化VLM服务
            self.vlm_service = OllamaVLMService(self.config.vision.ollama_config)
            if not await self.vlm_service.initialize():
                logger.error("无法初始化VLM服务")
                return False
                
            logger.info("服务初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def get_test_screenshot(self) -> Optional[np.ndarray]:
        """获取测试用截图"""
        try:
            screenshot = await self.connection_service.take_screenshot()
            if screenshot is not None:
                logger.info(f"获取测试截图成功，尺寸: {screenshot.shape}")
                return screenshot
            else:
                logger.error("无法获取截图")
                return None
        except Exception as e:
            logger.error(f"获取截图失败: {e}")
            return None
    
    def prepare_image_with_settings(self, image: np.ndarray, 
                                   max_size: Tuple[int, int],
                                   quality: int,
                                   format_type: str) -> Tuple[str, int, float]:
        """根据设置准备图像
        
        Returns:
            Tuple[str, int, float]: (base64_string, file_size_bytes, processing_time)
        """
        start_time = time.time()
        
        try:
            # 转换为PIL Image
            if len(image.shape) == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            pil_image = Image.fromarray(image_rgb)
            
            # 调整分辨率
            pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为base64
            buffer = BytesIO()
            if format_type == 'JPEG':
                pil_image.save(buffer, format="JPEG", quality=quality)
            else:  # PNG
                pil_image.save(buffer, format="PNG")
            
            file_size = len(buffer.getvalue())
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            processing_time = time.time() - start_time
            
            return image_base64, file_size, processing_time
            
        except Exception as e:
            logger.error(f"图像准备失败: {e}")
            return "", 0, time.time() - start_time
    
    async def test_vlm_with_settings(self, image_base64: str, 
                                   test_config: Dict) -> Dict:
        """使用指定设置测试VLM分析"""
        start_time = time.time()
        
        try:
            # 构建测试提示词
            prompt = """请分析这张游戏截图，识别：
1. 当前界面类型
2. 可见的UI元素（按钮、文本等）
3. 推荐的操作建议

请以JSON格式返回结果。"""
            
            # 调用VLM API
            response = await self.vlm_service._call_ollama_api(prompt, image_base64)
            
            analysis_time = time.time() - start_time
            
            # 解析响应
            response_text = response.get("response", "")
            response_length = len(response_text)
            
            # 尝试解析JSON
            json_parsed = False
            try:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    parsed_data = json.loads(json_text)
                    json_parsed = True
            except:
                pass
            
            return {
                "success": True,
                "analysis_time": analysis_time,
                "response_length": response_length,
                "json_parsed": json_parsed,
                "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }
            
        except Exception as e:
            return {
                "success": False,
                "analysis_time": time.time() - start_time,
                "error": str(e),
                "response_length": 0,
                "json_parsed": False,
                "response_preview": ""
            }
    
    async def run_comprehensive_test(self) -> None:
        """运行全面的图像质量测试"""
        logger.info("开始图像质量优化测试")
        
        # 获取测试截图
        test_image = await self.get_test_screenshot()
        if test_image is None:
            logger.error("无法获取测试截图，测试终止")
            return
        
        # 保存原始截图
        original_path = self.results_dir / f"original_screenshot_{get_timestamp()}.png"
        save_screenshot(test_image, str(original_path))
        logger.info(f"原始截图已保存: {original_path}")
        
        test_count = 0
        total_tests = len(self.quality_levels) * len(self.resolution_levels) * len(self.formats)
        
        for format_type in self.formats:
            for resolution in self.resolution_levels:
                for quality in self.quality_levels:
                    # PNG格式不需要质量参数
                    if format_type == 'PNG' and quality != self.quality_levels[0]:
                        continue
                        
                    test_count += 1
                    logger.info(f"\n=== 测试 {test_count}/{total_tests} ===")
                    logger.info(f"格式: {format_type}, 分辨率: {resolution}, 质量: {quality if format_type == 'JPEG' else 'N/A'}")
                    
                    # 准备图像
                    image_base64, file_size, prep_time = self.prepare_image_with_settings(
                        test_image, resolution, quality, format_type
                    )
                    
                    if not image_base64:
                        logger.error("图像准备失败，跳过此测试")
                        continue
                    
                    # 测试配置
                    test_config = {
                        "format": format_type,
                        "resolution": resolution,
                        "quality": quality if format_type == 'JPEG' else None,
                        "file_size": file_size,
                        "prep_time": prep_time
                    }
                    
                    logger.info(f"图像大小: {file_size/1024:.1f}KB, 准备时间: {prep_time:.3f}s")
                    
                    # 执行VLM分析
                    vlm_result = await self.test_vlm_with_settings(image_base64, test_config)
                    
                    # 记录结果
                    result = {
                        "timestamp": get_timestamp(),
                        "config": test_config,
                        "vlm_result": vlm_result,
                        "total_time": prep_time + vlm_result.get("analysis_time", 0)
                    }
                    
                    self.test_results.append(result)
                    
                    # 输出结果摘要
                    if vlm_result["success"]:
                        logger.info(f"✅ VLM分析成功: {vlm_result['analysis_time']:.2f}s, 响应长度: {vlm_result['response_length']}")
                        logger.info(f"JSON解析: {'✅' if vlm_result['json_parsed'] else '❌'}")
                    else:
                        logger.error(f"❌ VLM分析失败: {vlm_result.get('error', 'Unknown error')}")
                    
                    # 等待一段时间避免API限制
                    await asyncio.sleep(2)
        
        # 保存测试结果
        await self.save_results()
        
        # 分析结果
        self.analyze_results()
    
    async def save_results(self) -> None:
        """保存测试结果"""
        results_file = self.results_dir / f"test_results_{get_timestamp()}.json"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"测试结果已保存: {results_file}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def analyze_results(self) -> None:
        """分析测试结果"""
        logger.info("\n" + "="*50)
        logger.info("测试结果分析")
        logger.info("="*50)
        
        if not self.test_results:
            logger.warning("没有测试结果可分析")
            return
        
        # 成功率统计
        successful_tests = [r for r in self.test_results if r["vlm_result"]["success"]]
        success_rate = len(successful_tests) / len(self.test_results) * 100
        
        logger.info(f"总测试数: {len(self.test_results)}")
        logger.info(f"成功测试数: {len(successful_tests)}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        if not successful_tests:
            logger.warning("没有成功的测试结果可分析")
            return
        
        # 性能分析
        logger.info("\n📊 性能分析:")
        
        # 按格式分析
        jpeg_results = [r for r in successful_tests if r["config"]["format"] == "JPEG"]
        png_results = [r for r in successful_tests if r["config"]["format"] == "PNG"]
        
        if jpeg_results:
            avg_jpeg_time = sum(r["total_time"] for r in jpeg_results) / len(jpeg_results)
            avg_jpeg_size = sum(r["config"]["file_size"] for r in jpeg_results) / len(jpeg_results)
            logger.info(f"JPEG平均处理时间: {avg_jpeg_time:.2f}s, 平均文件大小: {avg_jpeg_size/1024:.1f}KB")
        
        if png_results:
            avg_png_time = sum(r["total_time"] for r in png_results) / len(png_results)
            avg_png_size = sum(r["config"]["file_size"] for r in png_results) / len(png_results)
            logger.info(f"PNG平均处理时间: {avg_png_time:.2f}s, 平均文件大小: {avg_png_size/1024:.1f}KB")
        
        # 最佳配置推荐
        logger.info("\n🏆 最佳配置推荐:")
        
        # 按总时间排序
        sorted_by_time = sorted(successful_tests, key=lambda x: x["total_time"])
        fastest = sorted_by_time[0]
        
        logger.info(f"最快配置: {fastest['config']['format']} {fastest['config']['resolution']} 质量{fastest['config']['quality']}")
        logger.info(f"处理时间: {fastest['total_time']:.2f}s, 文件大小: {fastest['config']['file_size']/1024:.1f}KB")
        
        # 按文件大小排序
        sorted_by_size = sorted(successful_tests, key=lambda x: x["config"]["file_size"])
        smallest = sorted_by_size[0]
        
        logger.info(f"最小文件: {smallest['config']['format']} {smallest['config']['resolution']} 质量{smallest['config']['quality']}")
        logger.info(f"处理时间: {smallest['total_time']:.2f}s, 文件大小: {smallest['config']['file_size']/1024:.1f}KB")
        
        # 质量vs性能分析
        if len(jpeg_results) > 1:
            logger.info("\n📈 JPEG质量vs性能分析:")
            for quality in self.quality_levels:
                quality_results = [r for r in jpeg_results if r["config"]["quality"] == quality]
                if quality_results:
                    avg_time = sum(r["total_time"] for r in quality_results) / len(quality_results)
                    avg_size = sum(r["config"]["file_size"] for r in quality_results) / len(quality_results)
                    logger.info(f"质量{quality}: 平均时间{avg_time:.2f}s, 平均大小{avg_size/1024:.1f}KB")
        
        # 分辨率vs性能分析
        logger.info("\n📐 分辨率vs性能分析:")
        for resolution in self.resolution_levels:
            res_results = [r for r in successful_tests if r["config"]["resolution"] == resolution]
            if res_results:
                avg_time = sum(r["total_time"] for r in res_results) / len(res_results)
                avg_size = sum(r["config"]["file_size"] for r in res_results) / len(res_results)
                logger.info(f"{resolution[0]}x{resolution[1]}: 平均时间{avg_time:.2f}s, 平均大小{avg_size/1024:.1f}KB")
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.connection_service:
                await self.connection_service.disconnect()
            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")

async def main():
    """主函数"""
    tester = ImageQualityTester()
    
    try:
        # 初始化
        if not await tester.initialize():
            logger.error("初始化失败")
            return
        
        # 运行测试
        await tester.run_comprehensive_test()
        
    except KeyboardInterrupt:
        logger.info("用户中断测试")
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
    finally:
        # 清理
        await tester.cleanup()

if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        "logs/image_quality_test.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:HH:mm:ss} | {level} | {message}",
        level="INFO",
        colorize=True
    )
    
    # 运行测试
    asyncio.run(main())