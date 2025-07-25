"""数据模型模块

导出所有数据类型和异常定义。
"""

from .data_types import (
    # 枚举类型
    ExecutionMode,
    ActionType,
    ElementType,
    ConnectionStatus,
    
    # 数据类
    Element,
    ActionSuggestion,
    Action,
    MatchResult,
    AnalysisResult,
    ExecutionResult,
    DeviceInfo,
    VLMResult,
    TaskConfig,
    SystemStatus,
)

from .exceptions import (
    # 基础异常
    iPadAutomationError,
    
    # 连接异常
    ConnectionError,
    DeviceNotFoundError,
    DeviceConnectionTimeoutError,
    TunneldError,
    
    # 截图异常
    ScreenshotError,
    
    # 视觉异常
    VisionError,
    TemplateNotFoundError,
    TemplateMatchError,
    VLMError,
    VLMProviderNotAvailableError,
    
    # 操作异常
    ActionError,
    ActionTimeoutError,
    ActionExecutionError,
    WebDriverError,
    WebDriverConnectionError,
    
    # 配置异常
    ConfigurationError,
    InvalidConfigError,
    MissingConfigError,
    
    # 任务异常
    TaskError,
    TaskTimeoutError,
    TaskExecutionError,
    
    # 验证异常
    ValidationError,
    InvalidActionError,
    InvalidElementError,
)

__all__ = [
    # 枚举类型
    "ExecutionMode",
    "ActionType",
    "ElementType",
    "ConnectionStatus",
    
    # 数据类
    "Element",
    "ActionSuggestion",
    "Action",
    "MatchResult",
    "AnalysisResult",
    "ExecutionResult",
    "DeviceInfo",
    "VLMResult",
    "TaskConfig",
    "SystemStatus",
    
    # 异常类
    "iPadAutomationError",
    "ConnectionError",
    "DeviceNotFoundError",
    "DeviceConnectionTimeoutError",
    "TunneldError",
    "ScreenshotError",
    "VisionError",
    "TemplateNotFoundError",
    "TemplateMatchError",
    "VLMError",
    "VLMProviderNotAvailableError",
    "ActionError",
    "ActionTimeoutError",
    "ActionExecutionError",
    "WebDriverError",
    "WebDriverConnectionError",
    "ConfigurationError",
    "InvalidConfigError",
    "MissingConfigError",
    "TaskError",
    "TaskTimeoutError",
    "TaskExecutionError",
    "ValidationError",
    "InvalidActionError",
    "InvalidElementError",
]