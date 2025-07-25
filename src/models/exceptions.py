"""异常定义模块

定义系统中使用的所有自定义异常类。
"""


class iPadAutomationError(Exception):
    """iPad自动化系统基础异常类"""
    pass


class ConnectionError(iPadAutomationError):
    """连接相关异常"""
    pass


class DeviceNotFoundError(ConnectionError):
    """设备未找到异常"""
    pass


class DeviceConnectionTimeoutError(ConnectionError):
    """设备连接超时异常"""
    pass


class TunneldError(ConnectionError):
    """Tunneld服务异常"""
    pass


class ScreenshotError(iPadAutomationError):
    """截图相关异常"""
    pass


class VisionError(iPadAutomationError):
    """视觉识别相关异常"""
    pass


class TemplateNotFoundError(VisionError):
    """模板未找到异常"""
    pass


class TemplateMatchError(VisionError):
    """模板匹配失败异常"""
    pass


class VLMError(VisionError):
    """VLM相关异常"""
    pass


class VLMProviderNotAvailableError(VLMError):
    """VLM提供者不可用异常"""
    pass


class ActionError(iPadAutomationError):
    """操作执行相关异常"""
    pass


class ActionTimeoutError(ActionError):
    """操作超时异常"""
    pass


class ActionExecutionError(ActionError):
    """操作执行失败异常"""
    pass


class WebDriverError(ActionError):
    """WebDriver相关异常"""
    pass


class WebDriverConnectionError(WebDriverError):
    """WebDriver连接异常"""
    pass


class ConfigurationError(iPadAutomationError):
    """配置相关异常"""
    pass


class InvalidConfigError(ConfigurationError):
    """无效配置异常"""
    pass


class MissingConfigError(ConfigurationError):
    """缺失配置异常"""
    pass


class TaskError(iPadAutomationError):
    """任务相关异常"""
    pass


class TaskTimeoutError(TaskError):
    """任务超时异常"""
    pass


class TaskExecutionError(TaskError):
    """任务执行失败异常"""
    pass


class ValidationError(iPadAutomationError):
    """数据验证异常"""
    pass


class InvalidActionError(ValidationError):
    """无效操作异常"""
    pass


class InvalidElementError(ValidationError):
    """无效元素异常"""
    pass