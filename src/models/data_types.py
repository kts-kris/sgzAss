"""数据类型定义模块

定义系统中使用的所有数据类型和枚举。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Tuple, Any
import numpy as np


class ExecutionMode(Enum):
    """执行模式枚举"""
    AUTO = "auto"          # 自动执行
    CONFIRM = "confirm"    # 需要确认
    SUGGEST = "suggest"    # 仅建议


class ActionType(Enum):
    """操作类型枚举"""
    TAP = "tap"
    SWIPE = "swipe"
    LONG_PRESS = "long_press"
    TYPE_TEXT = "type_text"
    WAIT = "wait"
    HOME = "home"
    BACK = "back"


class ElementType(Enum):
    """界面元素类型枚举"""
    BUTTON = "button"
    TEXT = "text"
    ICON = "icon"
    IMAGE = "image"
    INPUT = "input"
    MENU = "menu"
    DIALOG = "dialog"
    UNKNOWN = "unknown"


class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class Element:
    """界面元素数据类"""
    name: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    confidence: float
    element_type: ElementType = ElementType.UNKNOWN
    template_path: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def center(self) -> Tuple[int, int]:
        """获取元素中心点坐标"""
        x, y = self.position
        w, h = self.size
        return (x + w // 2, y + h // 2)

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """获取元素边界 (x, y, x2, y2)"""
        x, y = self.position
        w, h = self.size
        return (x, y, x + w, y + h)


@dataclass
class ActionSuggestion:
    """操作建议数据类"""
    action_type: ActionType
    target: Element
    parameters: Dict[str, Any]
    priority: int
    description: str
    confidence: float = 1.0

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class Action:
    """操作数据类"""
    action_type: ActionType
    target: Optional[Element] = None
    position: Optional[Tuple[int, int]] = None
    parameters: Dict[str, Any] = None
    timeout: float = 5.0
    retry_count: int = 3
    description: str = ""

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        
        # 验证target和position至少有一个
        if self.target is None and self.position is None:
            if self.action_type not in [ActionType.WAIT, ActionType.HOME, ActionType.BACK]:
                raise ValueError("Action must have either target or position")

    @property
    def target_position(self) -> Optional[Tuple[int, int]]:
        """获取目标位置"""
        if self.target:
            return self.target.center
        return self.position


@dataclass
class MatchResult:
    """模板匹配结果数据类"""
    template_name: str
    element: Optional[Element]
    success: bool
    confidence: float
    match_time: float
    error_message: Optional[str] = None


@dataclass
class AnalysisResult:
    """视觉分析结果数据类"""
    success: bool
    confidence: float
    elements: List[Element]
    suggestions: List[ActionSuggestion]
    analysis_time: float
    raw_data: Dict[str, Any] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}

    def get_element_by_name(self, name: str) -> Optional[Element]:
        """根据名称获取元素"""
        for element in self.elements:
            if element.name == name:
                return element
        return None

    def get_elements_by_type(self, element_type: ElementType) -> List[Element]:
        """根据类型获取元素列表"""
        return [e for e in self.elements if e.element_type == element_type]

    def get_best_suggestion(self) -> Optional[ActionSuggestion]:
        """获取最佳操作建议"""
        if not self.suggestions:
            return None
        return max(self.suggestions, key=lambda s: s.priority * s.confidence)


@dataclass
class ExecutionResult:
    """执行结果数据类"""
    success: bool
    action: Action
    execution_time: float
    error_message: Optional[str] = None
    retry_count: int = 0
    screenshot_before: Optional[np.ndarray] = None
    screenshot_after: Optional[np.ndarray] = None


@dataclass
class DeviceInfo:
    """设备信息数据类"""
    udid: str
    name: str
    ios_version: str
    model: str
    screen_size: Tuple[int, int]
    scale_factor: float = 1.0
    is_connected: bool = False
    connection_type: str = "usb"


@dataclass
class VLMResult:
    """VLM分析结果数据类"""
    success: bool
    description: str
    elements: List[Element]
    suggestions: List[ActionSuggestion]
    confidence: float
    model_name: str
    processing_time: float
    screen_type: str = "unknown"
    error_message: Optional[str] = None
    raw_response: Dict[str, Any] = None

    def __post_init__(self):
        if self.raw_response is None:
            self.raw_response = {}


@dataclass
class TaskConfig:
    """任务配置数据类"""
    name: str
    description: str
    execution_mode: ExecutionMode = ExecutionMode.AUTO
    max_retries: int = 3
    timeout: float = 30.0
    screenshot_interval: float = 1.0
    templates: List[str] = None
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.templates is None:
            self.templates = []
        if self.parameters is None:
            self.parameters = {}


@dataclass
class SystemStatus:
    """系统状态数据类"""
    connection_status: ConnectionStatus
    device_info: Optional[DeviceInfo]
    last_screenshot_time: Optional[float]
    last_action_time: Optional[float]
    error_count: int = 0
    uptime: float = 0.0
    memory_usage: float = 0.0