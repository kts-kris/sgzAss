#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ollama VLM服务模块

提供本地Ollama大模型的视觉语言模型(VLM)支持，
实现异步截图分析和智能操作建议生成。
"""

import asyncio
import base64
import json
import time
from io import BytesIO
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

import cv2
import numpy as np
import aiohttp
from PIL import Image
from loguru import logger

from ..models import (
    Element, ElementType, ActionSuggestion, ActionType, AnalysisResult,
    VLMResult, VLMError, VLMProviderNotAvailableError
)
from ..utils.prompt_manager import get_prompt_manager


class OllamaVLMService:
    """Ollama VLM服务类，提供本地大模型视觉分析能力"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 11434,
                 model: str = "llava:latest",
                 timeout: int = 60,
                 max_retries: int = 3,
                 image_max_size: Optional[Tuple[int, int]] = None,
                 image_quality: int = 85):
        """
        初始化Ollama VLM服务
        
        Args:
            host: Ollama服务主机地址
            port: Ollama服务端口
            model: 使用的VLM模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            image_max_size: 图像最大尺寸 (width, height)
            image_quality: JPEG压缩质量 (1-100)
        """
        self.host = host
        self.port = port
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = f"http://{host}:{port}"
        self.is_available = False
        self.is_running = False
        
        # 图像处理配置
        self.image_max_size = image_max_size or (1024, 1024)
        self.image_quality = image_quality
        
        # 提示词管理器
        self.prompt_manager = get_prompt_manager()
        
        # 提示词优化历史
        self.prompt_optimization_history = []
        
    async def initialize(self) -> bool:
        """
        初始化服务，检查Ollama可用性
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 检查Ollama服务是否运行
            if not await self._check_ollama_service():
                logger.error("Ollama服务未运行或不可访问")
                return False
            
            # 检查模型是否可用
            if not await self._check_model_availability():
                logger.error(f"模型 {self.model} 不可用")
                return False
            
            self.is_available = True
            logger.info(f"Ollama VLM服务初始化成功，使用模型: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"Ollama VLM服务初始化失败: {e}")
            return False
    
    async def analyze_screenshot_async(self, 
                                     image: np.ndarray,
                                     analysis_type: str = "game_analysis",
                                     custom_prompt: Optional[str] = None) -> VLMResult:
        """
        异步分析游戏截图
        
        Args:
            image: 截图图像数组
            analysis_type: 分析类型 (game_analysis/ui_elements/action_suggestion)
            custom_prompt: 自定义提示词
            
        Returns:
            VLMResult: VLM分析结果
        """
        if not self.is_available:
            raise VLMProviderNotAvailableError("Ollama VLM服务不可用")
        
        start_time = time.time()
        
        try:
            # 准备图像数据
            image_base64 = await self._prepare_image(image)
            
            # 选择提示词
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self.prompt_manager.get_optimized_prompt(
                    category=analysis_type,
                    context={
                        "recent_failures": 0,  # 可以从历史记录中获取
                        "avg_response_time": 0  # 可以从历史记录中获取
                    }
                )
            
            # 调用Ollama API
            response = await self._call_ollama_api(prompt, image_base64)
            
            # 解析响应
            result = await self._parse_vlm_response(response, analysis_type)
            
            analysis_time = time.time() - start_time
            logger.info(f"VLM分析完成，耗时: {analysis_time:.2f}秒")
            
            # 更新提示词性能统计
            success = result.get("confidence", 0) > 0.5
            self.prompt_manager.update_prompt_performance(
                category=analysis_type,
                language=self.prompt_manager.config.prompt.default_language,
                success=success,
                response_time=analysis_time
            )
            
            return VLMResult(
                success=True,
                description=result.get("description", ""),
                elements=result.get("elements", []),
                suggestions=result.get("suggestions", []),
                confidence=result.get("confidence", 0.8),
                model_name=self.model,
                processing_time=analysis_time,
                screen_type=result.get("current_scene", "unknown"),
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"VLM分析失败: {e}")
            return VLMResult(
                success=False,
                description=f"分析失败: {str(e)}",
                elements=[],
                suggestions=[],
                confidence=0.0,
                model_name=self.model,
                processing_time=time.time() - start_time,
                screen_type="unknown",
                error_message=str(e)
            )
    
    async def generate_optimized_prompt(self, 
                                      screenshot_analysis_history: List[Dict],
                                      user_feedback: Optional[str] = None) -> str:
        """
        基于历史分析结果和用户反馈生成优化的提示词
        
        Args:
            screenshot_analysis_history: 历史截图分析结果
            user_feedback: 用户反馈
            
        Returns:
            str: 优化后的提示词
        """
        try:
            # 分析历史数据，找出常见模式和问题
            patterns = self._analyze_historical_patterns(screenshot_analysis_history)
            
            # 构建提示词优化请求
            optimization_prompt = self._build_optimization_prompt(patterns, user_feedback)
            
            # 调用Ollama生成优化提示词
            response = await self._call_ollama_api(optimization_prompt)
            
            # 解析优化后的提示词
            optimized_prompt = self._extract_optimized_prompt(response)
            
            # 记录优化历史
            self.prompt_optimization_history.append({
                "timestamp": time.time(),
                "original_patterns": patterns,
                "user_feedback": user_feedback,
                "optimized_prompt": optimized_prompt
            })
            
            logger.info("提示词优化完成")
            return optimized_prompt
            
        except Exception as e:
            logger.error(f"提示词优化失败: {e}")
            return self.prompt_manager.get_prompt("game_analysis")  # 返回默认提示词
    
    async def _check_ollama_service(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _check_model_availability(self) -> bool:
        """检查指定模型是否可用"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]
                        return self.model in models
            return False
        except Exception:
            return False
    
    async def _prepare_image(self, image: np.ndarray) -> str:
        """准备图像数据，转换为base64格式"""
        try:
            # 转换为PIL Image
            if len(image.shape) == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            pil_image = Image.fromarray(image_rgb)
            
            # 使用配置的图像压缩参数
            pil_image.thumbnail(self.image_max_size, Image.Resampling.LANCZOS)
            
            # 转换为base64
            buffer = BytesIO()
            pil_image.save(buffer, format="JPEG", quality=self.image_quality)
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            return image_base64
            
        except Exception as e:
            raise VLMError(f"图像准备失败: {e}")
    
    async def _call_ollama_api(self, prompt: str, image_base64: Optional[str] = None) -> Dict:
        """调用Ollama API"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 1000
            }
        }
        
        if image_base64:
            payload["images"] = [image_base64]
        
        for attempt in range(self.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            raise VLMError(f"API调用失败: {response.status} - {error_text}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"API调用超时，重试 {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise VLMError("API调用超时")
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise VLMError(f"API调用失败: {e}")
                await asyncio.sleep(1)  # 重试前等待
    
    async def _parse_vlm_response(self, response: Dict, analysis_type: str) -> Dict:
        """解析VLM响应"""
        try:
            response_text = response.get("response", "")
            
            # 尝试解析JSON格式的响应
            try:
                # 查找JSON部分
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    parsed_data = json.loads(json_text)
                    return self._convert_parsed_data(parsed_data)
            except json.JSONDecodeError:
                pass
            
            # 如果无法解析JSON，使用文本解析
            return self._parse_text_response(response_text, analysis_type)
            
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            return {
                "description": response.get("response", "解析失败"),
                "elements": [],
                "suggestions": [],
                "confidence": 0.5
            }
    
    def _convert_parsed_data(self, data: Dict) -> Dict:
        """转换解析后的数据为标准格式"""
        result = {
            "description": data.get("description", ""),
            "elements": [],
            "suggestions": [],
            "confidence": data.get("confidence", 0.8)
        }
        
        # 转换元素数据
        for elem_data in data.get("elements", []):
            # 解析元素类型，处理组合字符串如'button/icon/text'
            element_type_str = elem_data.get("type", "unknown")
            element_type = self._parse_element_type(element_type_str)
            
            element = Element(
                name=elem_data.get("name", "unknown"),
                position=(elem_data.get("x", 0), elem_data.get("y", 0)),
                size=(elem_data.get("width", 50), elem_data.get("height", 50)),
                confidence=elem_data.get("confidence", 0.8),
                element_type=element_type
            )
            result["elements"].append(element)
        
        # 转换建议数据
        for sugg_data in data.get("suggestions", []):
            if result["elements"]:
                target_element = result["elements"][0]  # 简化处理
            else:
                target_element = Element(
                    name="screen_center",
                    position=(400, 600),
                    size=(50, 50),
                    confidence=0.5
                )
            
            # 将click映射为tap
            action_str = sugg_data.get("action", "tap")
            if action_str == "click":
                action_str = "tap"
            
            suggestion = ActionSuggestion(
                action_type=ActionType(action_str),
                target=target_element,
                parameters=sugg_data.get("parameters", {}),
                priority=sugg_data.get("priority", 1),
                description=sugg_data.get("description", ""),
                confidence=sugg_data.get("confidence", 0.8)
            )
            result["suggestions"].append(suggestion)
        
        return result
    
    def _parse_element_type(self, type_str: str) -> ElementType:
        """解析元素类型字符串，处理组合类型如'button/icon/text'"""
        if not type_str:
            return ElementType.UNKNOWN
        
        # 转换为小写并分割
        type_str = type_str.lower().strip()
        
        # 处理组合类型，取第一个有效类型
        if '/' in type_str:
            types = [t.strip() for t in type_str.split('/')]
            for t in types:
                try:
                    return ElementType(t)
                except ValueError:
                    continue
        
        # 处理单一类型
        try:
            return ElementType(type_str)
        except ValueError:
            # 如果不是有效的ElementType，尝试映射
            type_mapping = {
                'btn': 'button',
                'img': 'image',
                'txt': 'text',
                'ui': 'unknown',
                'interactive': 'button'
            }
            mapped_type = type_mapping.get(type_str, 'unknown')
            try:
                return ElementType(mapped_type)
            except ValueError:
                return ElementType.UNKNOWN
    
    def _parse_text_response(self, text: str, analysis_type: str) -> Dict:
        """解析文本格式的响应"""
        return {
            "description": text,
            "elements": [],
            "suggestions": [],
            "confidence": 0.6
        }
    
    def get_prompt_stats(self) -> Dict[str, Any]:
        """获取提示词使用统计"""
        return self.prompt_manager.get_prompt_stats()
    
    def reload_prompts(self):
        """重新加载提示词配置"""
        self.prompt_manager.reload_prompts()
        logger.info("提示词配置已重新加载")
    
    def _analyze_historical_patterns(self, history: List[Dict]) -> Dict:
        """分析历史模式"""
        # 简化实现，实际可以更复杂
        patterns = {
            "common_scenes": [],
            "frequent_actions": [],
            "accuracy_issues": []
        }
        
        for record in history[-10:]:  # 分析最近10次
            if "scene" in record:
                patterns["common_scenes"].append(record["scene"])
            if "actions" in record:
                patterns["frequent_actions"].extend(record["actions"])
        
        return patterns
    
    def _build_optimization_prompt(self, patterns: Dict, feedback: Optional[str]) -> str:
        """构建优化提示词"""
        base_prompt = """
基于以下游戏分析历史和用户反馈，请优化游戏截图分析的提示词：

历史模式：
{patterns}

用户反馈：
{feedback}

请生成一个更准确、更有针对性的提示词，提高分析质量。
"""
        
        return base_prompt.format(
            patterns=json.dumps(patterns, ensure_ascii=False, indent=2),
            feedback=feedback or "无"
        )
    
    def _extract_optimized_prompt(self, response: Dict) -> str:
        """提取优化后的提示词"""
        response_text = response.get("response", "")
        
        # 简化实现：直接返回响应文本
        # 实际可以更智能地提取和验证提示词
        return response_text or self.prompt_templates["game_analysis"]
    
    async def start(self):
        """启动Ollama VLM服务"""
        self.is_running = await self.initialize()
        return self.is_running
    
    async def stop(self):
        """停止服务"""
        self.is_available = False
        self.is_running = False
        logger.info("Ollama VLM服务已停止")
    
    async def close(self):
        """关闭服务"""
        await self.stop()