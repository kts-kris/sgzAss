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

from .template_matcher import TemplateMatcher

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
        
        # 初始化模板匹配器
        self.template_matcher = TemplateMatcher()
        
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
            
            # 确保result是字典类型
            if not isinstance(result, dict):
                logger.warning(f"解析结果不是字典格式: {type(result)}")
                result = {
                    "description": str(result) if result else "解析失败",
                    "elements": [],
                    "suggestions": [],
                    "confidence": 0.3
                }
            
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
                error_message=None,
                used_prompt=prompt  # 添加使用的提示词
            )
            
        except Exception as e:
            logger.error(f"VLM分析失败: {e}")
            
            # 使用模板匹配作为回退
            logger.info("VLM分析失败，尝试使用模板匹配")
            try:
                # 创建基础分析结果用于模板匹配
                basic_analysis = {
                    "scene": "未知界面",
                    "description": "VLM分析失败，使用模板匹配",
                    "elements": [],
                    "suggestions": []
                }
                
                # 使用模板匹配
                template_result = self.template_matcher.match_elements(basic_analysis, confidence_threshold=0.3)
                
                # 转换为VLMResult格式
                elements = []
                for elem in template_result.get("elements", []):
                    element_type = ElementType.BUTTON if elem.get("type") == "button" else ElementType.TEXT
                    elements.append(Element(
                        name=elem.get("name", "unknown"),
                        position=(elem.get("x", 0), elem.get("y", 0)),
                        size=(elem.get("width", 100), elem.get("height", 50)),
                        confidence=elem.get("confidence", 0.5),
                        element_type=element_type
                    ))
                
                suggestions = []
                for sugg in template_result.get("suggestions", []):
                    action_type = ActionType.TAP
                    if sugg.get("action") == "swipe":
                        action_type = ActionType.SWIPE
                    elif sugg.get("action") == "type_text":
                        action_type = ActionType.TYPE_TEXT
                    elif sugg.get("action") == "wait":
                        action_type = ActionType.WAIT
                    
                    target_element = elements[0] if elements else Element(
                        name="screen_center",
                        position=(400, 600),
                        size=(50, 50),
                        confidence=0.5
                    )
                    
                    suggestions.append(ActionSuggestion(
                        action_type=action_type,
                        target=target_element,
                        parameters=sugg.get("parameters", {}),
                        priority=sugg.get("priority", 1),
                        description=sugg.get("description", ""),
                        confidence=sugg.get("confidence", 0.5)
                    ))
                
                logger.info(f"模板匹配成功，使用模板: {template_result.get('template_used', 'unknown')}")
                return VLMResult(
                    success=True,
                    description=template_result.get("description", "基于模板匹配的分析结果"),
                    elements=elements,
                    suggestions=suggestions,
                    confidence=template_result.get("confidence", 0.5),
                    model_name="template_matcher",
                    processing_time=time.time() - start_time,
                    screen_type=template_result.get("scene", "模板匹配界面"),
                    error_message=None,
                    used_prompt="template_matching_fallback"
                )
                
            except Exception as template_error:
                logger.error(f"模板匹配也失败: {template_error}")
                
                # 最终回退方案
                return VLMResult(
                    success=False,
                    description=f"VLM和模板匹配都失败: {str(e)}",
                    elements=[],
                    suggestions=[],
                    confidence=0.0,
                    model_name=self.model,
                    processing_time=time.time() - start_time,
                    screen_type="unknown",
                    error_message=str(e),
                    used_prompt=custom_prompt or self.prompt_manager.get_prompt("default_prompts.fallback")
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
        """调用Ollama API，支持重试和更好的错误处理"""
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
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # 动态调整超时时间
                current_timeout = self.timeout + (attempt * 10)  # 每次重试增加10秒
                timeout = aiohttp.ClientTimeout(total=current_timeout)
                
                logger.debug(f"调用Ollama API (尝试 {attempt + 1}/{self.max_retries})，超时: {current_timeout}秒")
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    ) as response:
                        if response.status == 200:
                            if attempt > 0:
                                logger.info(f"Ollama API在第 {attempt + 1} 次尝试后成功")
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.warning(f"Ollama API错误 {response.status} (尝试 {attempt + 1}/{self.max_retries}): {error_text}")
                            last_error = VLMError(f"API调用失败: {response.status} - {error_text}")
                            if response.status >= 500 and attempt < self.max_retries - 1:
                                # 服务器错误，可以重试
                                continue
                            elif attempt == self.max_retries - 1:
                                raise last_error
                            
            except asyncio.TimeoutError as e:
                last_error = VLMError(f"API调用超时 (>{current_timeout}秒)")
                logger.warning(f"Ollama API调用超时 (尝试 {attempt + 1}/{self.max_retries})，超时时间: {current_timeout}秒")
                if attempt < self.max_retries - 1:
                    retry_delay = 2 ** attempt  # 指数退避
                    logger.debug(f"等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise last_error
            except aiohttp.ClientError as e:
                last_error = VLMError(f"API连接失败: {e}")
                logger.warning(f"Ollama API连接错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    retry_delay = 2 ** attempt
                    logger.debug(f"等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise last_error
            except Exception as e:
                last_error = VLMError(f"API调用异常: {e}")
                logger.error(f"Ollama API调用异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    retry_delay = 2 ** attempt
                    logger.debug(f"等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise last_error
        
        # 如果所有重试都失败，抛出最后一个错误
        if last_error:
            raise last_error
        else:
            raise VLMError(f"API调用在 {self.max_retries} 次尝试后仍然失败")
    
    async def _parse_vlm_response(self, response: Dict, analysis_type: str) -> Dict:
        """解析VLM响应"""
        try:
            # 安全地获取响应文本
            response_text = ""
            if isinstance(response, dict):
                response_text = response.get("response", "")
            elif isinstance(response, str):
                response_text = response
            else:
                logger.warning(f"响应格式异常: {type(response)}")
                return {
                    "description": str(response) if response else "空响应",
                    "elements": [],
                    "suggestions": [],
                    "confidence": 0.3
                }
            
            if not response_text:
                logger.warning("响应文本为空")
                return {
                    "description": "空响应",
                    "elements": [],
                    "suggestions": [],
                    "confidence": 0.3
                }
            
            # 尝试解析JSON格式的响应
            try:
                # 查找JSON部分，支持多种JSON格式
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    # 清理可能的格式问题
                    json_text = json_text.strip()
                    parsed_data = json.loads(json_text)
                    
                    # 验证解析结果的有效性
                    if isinstance(parsed_data, dict):
                        logger.info(f"成功解析JSON响应，包含字段: {list(parsed_data.keys())}")
                        return self._convert_parsed_data(parsed_data)
                    else:
                        logger.warning(f"JSON解析结果不是字典: {type(parsed_data)}")
                        
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败: {e}，尝试文本解析")
            except Exception as e:
                logger.warning(f"JSON处理异常: {e}，尝试文本解析")
            
            # 如果无法解析JSON，使用文本解析
            logger.info("使用文本解析模式")
            return self._parse_text_response(response_text, analysis_type)
            
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            # 安全地处理response，避免.get()调用错误
            fallback_description = "解析失败"
            try:
                if isinstance(response, dict):
                    fallback_description = response.get("response", "解析失败")
                elif isinstance(response, str):
                    fallback_description = response[:200] + "..." if len(response) > 200 else response
                elif response:
                    fallback_description = str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
            except Exception:
                fallback_description = "解析失败"
            
            return {
                "description": fallback_description,
                "elements": [],
                "suggestions": [],
                "confidence": 0.5
            }
    
    def _convert_parsed_data(self, data: Dict) -> Dict:
        """转换解析后的数据为标准格式"""
        result = {
            "description": data.get("description", data.get("current_scene", "")),
            "elements": [],
            "suggestions": [],
            "confidence": data.get("confidence", 0.8)
        }
        
        # 转换元素数据，支持多种字段名
        elements_data = data.get("elements", data.get("ui_elements", []))
        if isinstance(elements_data, list):
            for elem_data in elements_data:
                if not isinstance(elem_data, dict):
                    continue
                    
                # 解析元素类型，处理组合字符串如'button/icon/text'
                element_type_str = elem_data.get("type", elem_data.get("element_type", "unknown"))
                element_type = self._parse_element_type(element_type_str)
                
                # 支持多种位置字段格式
                position = (0, 0)
                if "position" in elem_data and isinstance(elem_data["position"], (list, tuple)) and len(elem_data["position"]) >= 2:
                    position = (elem_data["position"][0], elem_data["position"][1])
                elif "x" in elem_data and "y" in elem_data:
                    position = (elem_data.get("x", 0), elem_data.get("y", 0))
                
                # 支持多种尺寸字段格式
                size = (50, 50)
                if "size" in elem_data and isinstance(elem_data["size"], (list, tuple)) and len(elem_data["size"]) >= 2:
                    size = (elem_data["size"][0], elem_data["size"][1])
                elif "width" in elem_data and "height" in elem_data:
                    size = (elem_data.get("width", 50), elem_data.get("height", 50))
                
                element = Element(
                    name=elem_data.get("name", elem_data.get("text", "unknown")),
                    position=position,
                    size=size,
                    confidence=elem_data.get("confidence", 0.8),
                    element_type=element_type
                )
                result["elements"].append(element)
        
        # 转换建议数据，支持多种字段名
        suggestions_data = data.get("suggestions", data.get("actions", data.get("recommendations", [])))
        if isinstance(suggestions_data, list):
            for sugg_data in suggestions_data:
                if not isinstance(sugg_data, dict):
                    continue
                    
                # 查找目标元素
                target_element = None
                target_name = sugg_data.get("target", sugg_data.get("target_element", ""))
                
                if target_name and result["elements"]:
                    # 尝试匹配目标元素
                    for elem in result["elements"]:
                        if elem.name == target_name or target_name in elem.name:
                            target_element = elem
                            break
                
                if not target_element:
                    if result["elements"]:
                        target_element = result["elements"][0]  # 使用第一个元素
                    else:
                        target_element = Element(
                            name="screen_center",
                            position=(400, 600),
                            size=(50, 50),
                            confidence=0.5
                        )
                
                # 安全解析action类型
                action_str = sugg_data.get("action", sugg_data.get("action_type", "tap"))
                action_type = self._parse_action_type(action_str)
                
                suggestion = ActionSuggestion(
                    action_type=action_type,
                    target=target_element,
                    parameters=sugg_data.get("parameters", {}),
                    priority=sugg_data.get("priority", 1),
                    description=sugg_data.get("description", sugg_data.get("reason", "")),
                    confidence=sugg_data.get("confidence", 0.8)
                )
                result["suggestions"].append(suggestion)
        
        return result
    
    def _parse_action_type(self, action_str: str) -> ActionType:
        """安全解析ActionType字符串"""
        if not action_str:
            return ActionType.TAP
        
        # 转换为小写并去除空格
        action_str = action_str.lower().strip()
        
        # 映射常见的action别名
        action_mapping = {
            'click': 'tap',
            'press': 'tap',
            'touch': 'tap',
            'slide': 'swipe',
            'drag': 'swipe',
            'hold': 'long_press',
            'longpress': 'long_press',
            'long-press': 'long_press',
            'input': 'type_text',
            'type': 'type_text',
            'text': 'type_text',
            'sleep': 'wait',
            'pause': 'wait',
            'delay': 'wait'
        }
        
        # 尝试映射
        mapped_action = action_mapping.get(action_str, action_str)
        
        # 尝试创建ActionType
        try:
            return ActionType(mapped_action)
        except ValueError:
            logger.warning(f"未知的action类型: {action_str}，使用默认值TAP")
            return ActionType.TAP
    
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
        """解析文本格式的响应，增强解析能力"""
        result = {
            "description": text[:500] + "..." if len(text) > 500 else text,
            "elements": [],
            "suggestions": [],
            "confidence": 0.6
        }
        
        # 尝试从文本中提取JSON格式的内容
        json_match = self._extract_json_from_text(text)
        if json_match:
            try:
                parsed_json = json.loads(json_match)
                return self._convert_parsed_data(parsed_json)
            except json.JSONDecodeError:
                logger.debug("JSON解析失败，继续使用文本解析")
        
        # 尝试从文本中提取基本信息
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 识别章节
            if any(keyword in line.lower() for keyword in ['元素', 'elements', 'ui', '界面']):
                current_section = 'elements'
                continue
            elif any(keyword in line.lower() for keyword in ['建议', 'suggestions', 'actions', '操作']):
                current_section = 'suggestions'
                continue
            elif any(keyword in line.lower() for keyword in ['描述', 'description', '场景', 'scene']):
                current_section = 'description'
                continue
                
            # 根据当前章节解析内容
            if current_section == 'elements':
                # 增强的元素提取
                element = self._extract_element_from_line(line)
                if element:
                    result["elements"].append(element)
                    
            elif current_section == 'suggestions':
                # 增强的建议提取
                suggestion = self._extract_suggestion_from_line(line)
                if suggestion:
                    result["suggestions"].append(suggestion)
        
        # 如果没有找到任何元素或建议，尝试全文分析
        if not result["elements"] and not result["suggestions"]:
            result = self._fallback_text_analysis(text, result)
        
        logger.info(f"文本解析结果: 元素数量={len(result['elements'])}, 建议数量={len(result['suggestions'])}")
        return result
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """从文本中提取JSON格式的内容"""
        import re
        
        # 尝试匹配完整的JSON对象
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # 简单JSON匹配
            r'```json\s*([\s\S]*?)\s*```',      # Markdown代码块
            r'```\s*([\s\S]*?)\s*```',          # 通用代码块
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # 验证是否为有效JSON
                    json.loads(match)
                    return match
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _extract_element_from_line(self, line: str) -> Optional[Dict]:
        """从单行文本中提取元素信息"""
        import re
        
        # 元素类型关键词映射
        element_keywords = {
            "button": ["按钮", "button", "btn", "点击"],
            "text": ["文本", "text", "label", "标签"],
            "input": ["输入框", "input", "textfield", "输入"],
            "image": ["图片", "image", "图标", "icon"],
            "menu": ["菜单", "menu", "选项", "option"]
        }
        
        # 检查是否包含元素关键词
        element_type = "unknown"
        for etype, keywords in element_keywords.items():
            if any(keyword in line.lower() for keyword in keywords):
                element_type = etype
                break
        
        if element_type == "unknown":
            return None
        
        # 尝试提取位置信息
        position_match = re.search(r'\((\d+),\s*(\d+)\)', line)
        if position_match:
            x, y = int(position_match.group(1)), int(position_match.group(2))
        else:
            x, y = 400, 300  # 默认位置
        
        element_name = line.split(':')[0].strip() if ':' in line else line
        
        return {
            "name": element_name,
            "type": element_type,
            "x": x,
            "y": y,
            "width": 100,
            "height": 50,
            "confidence": 0.7
        }
    
    def _extract_suggestion_from_line(self, line: str) -> Optional[Dict]:
        """从单行文本中提取建议信息"""
        # 动作关键词映射
        action_keywords = {
            "tap": ["点击", "click", "tap", "按"],
            "swipe": ["滑动", "swipe", "scroll", "拖拽"],
            "type_text": ["输入", "input", "type", "填写"],
            "wait": ["等待", "wait", "观察", "停留"]
        }
        
        # 检查是否包含动作关键词
        action_type = "wait"
        for atype, keywords in action_keywords.items():
            if any(keyword in line.lower() for keyword in keywords):
                action_type = atype
                break
        
        # 计算优先级
        priority = 1
        if "重要" in line or "urgent" in line.lower():
            priority = 3
        elif "建议" in line or "recommend" in line.lower():
            priority = 2
        elif "可选" in line or "optional" in line.lower():
            priority = 1
        
        return {
            "action": action_type,
            "description": line.strip(),
            "priority": priority,
            "confidence": 0.7
        }
    
    def _fallback_text_analysis(self, text: str, result: Dict) -> Dict:
        """当常规解析失败时的回退分析"""
        # 关键词分析
        if any(keyword in text.lower() for keyword in ["游戏", "game", "界面", "ui", "屏幕", "screen"]):
            result["confidence"] = 0.8
        
        # 如果文本中包含明显的UI元素描述，创建通用建议
        if any(keyword in text.lower() for keyword in ["按钮", "button", "点击", "click"]):
            result["suggestions"].append({
                "action": "tap",
                "description": "检测到可点击元素，建议进行交互",
                "priority": 2,
                "confidence": 0.6
            })
        else:
            result["suggestions"].append({
                "action": "wait",
                "description": "等待或观察当前界面",
                "priority": 1,
                "confidence": 0.3
            })
        
        # 创建一个默认元素
        if not result["elements"]:
            result["elements"].append({
                "name": "screen_center",
                "type": "unknown",
                "x": 400,
                "y": 300,
                "width": 100,
                "height": 50,
                "confidence": 0.5
            })
        
        return result
    
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
        base_prompt = self.prompt_manager.get_prompt("prompt_optimization")
        
        return base_prompt.format(
            patterns=json.dumps(patterns, ensure_ascii=False, indent=2),
            feedback=feedback or "无"
        )
    
    def _extract_optimized_prompt(self, response: Dict) -> str:
        """提取优化后的提示词"""
        response_text = response.get("response", "")
        
        # 简化实现：直接返回响应文本
        # 实际可以更智能地提取和验证提示词
        return response_text or self.prompt_manager.get_prompt("game_analysis")
    
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