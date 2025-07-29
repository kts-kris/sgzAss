"""连接服务模块

负责与iPad设备建立USB连接并获取屏幕截图。
仅使用pymobiledevice3和tunneld，移除所有其他连接方式。
"""

import io
import sys
import time
import subprocess
import tempfile
import os
from typing import Optional, Tuple
from PIL import Image
import numpy as np
from loguru import logger

# pymobiledevice3 相关导入
try:
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.screenshot import ScreenshotService
    from pymobiledevice3.exceptions import (
        InvalidServiceError, 
        PasswordRequiredError, 
        NoDeviceConnectedError, 
        PairingError
    )
    PYMOBILEDEVICE3_AVAILABLE = True
except ImportError:
    PYMOBILEDEVICE3_AVAILABLE = False
    logger.error("pymobiledevice3 未安装，无法使用USB连接功能")

from ..models import (
    DeviceInfo, 
    ConnectionStatus,
    ConnectionError,
    DeviceNotFoundError,
    DeviceConnectionTimeoutError,
    TunneldError,
    ScreenshotError
)
from ..utils.config import get_config


class TunneldManager:
    """管理 pymobiledevice3 tunneld 服务"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.started: bool = False
    
    def is_running(self) -> bool:
        """检查 tunneld 服务是否在运行"""
        try:
            check_cmd = "ps aux | grep 'pymobiledevice3 remote tunneld' | grep -v grep"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            return bool(result.stdout.strip())
        except Exception as e:
            logger.debug(f"检查tunneld服务状态失败: {e}")
            return False
    
    def force_stop(self) -> None:
        """强制停止所有 tunneld 进程"""
        try:
            # 查找并终止所有 tunneld 进程
            find_cmd = "ps aux | grep 'pymobiledevice3 remote tunneld' | grep -v grep | awk '{print $2}'"
            result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        try:
                            kill_cmd = f"kill -9 {pid.strip()}"
                            subprocess.run(kill_cmd, shell=True, check=True)
                            logger.debug(f"强制终止 tunneld 进程: {pid.strip()}")
                        except subprocess.CalledProcessError:
                            logger.debug(f"无法终止进程 {pid.strip()}，可能已经停止")
                
                # 等待进程完全停止
                time.sleep(1)
                logger.info("已强制停止所有 tunneld 进程")
            else:
                logger.debug("没有发现运行中的 tunneld 进程")
                
        except Exception as e:
            logger.debug(f"强制停止 tunneld 进程时出错: {e}")
    
    def start(self) -> bool:
        """启动 tunneld 服务"""
        try:
            # 首先强制关闭所有现有的 tunneld 进程
            logger.debug("启动前强制关闭现有 tunneld 进程...")
            self.force_stop()
            
            if self.is_running():
                logger.debug("tunneld 服务已在运行")
                self.started = True
                return True
            
            logger.info("正在启动 pymobiledevice3 tunneld 服务...")
            
            # 首先尝试不使用sudo启动
            cmd = [sys.executable, "-m", "pymobiledevice3", "remote", "tunneld"]
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # 等待服务启动
            time.sleep(3)
            
            if self.process.poll() is None and self.is_running():
                logger.info("tunneld 服务启动成功")
                self.started = True
                return True
            else:
                # 检查是否因为权限问题失败
                stderr_output = ""
                if self.process:
                    try:
                        stdout, stderr = self.process.communicate(timeout=1)
                        if stderr:
                            stderr_output = stderr.decode()
                            logger.debug(f"tunneld 错误输出: {stderr_output}")
                    except subprocess.TimeoutExpired:
                        pass
                
                # 如果是权限问题，尝试使用sudo重新启动
                if "root privileges" in stderr_output or "permission denied" in stderr_output.lower():
                    logger.info("检测到需要root权限，尝试使用sudo启动tunneld...")
                    return self._start_with_sudo()
                else:
                    logger.error("tunneld 服务启动失败")
                    if stderr_output:
                        logger.error(f"错误信息: {stderr_output}")
                    return False
                
        except Exception as e:
            logger.error(f"启动 tunneld 服务失败: {e}")
            return False
    
    def _start_with_sudo(self) -> bool:
        """使用sudo启动tunneld服务"""
        try:
            import platform
            
            # 提示用户需要管理员权限
            logger.info("tunneld服务需要管理员权限才能启动")
            
            # 在macOS上使用osascript获取管理员权限
            if platform.system() == "Darwin":
                return self._start_with_osascript()
            else:
                # 其他系统提供手动指导
                logger.error("检测到需要管理员权限，但当前环境不支持自动权限提升")
                logger.error("请手动使用以下命令启动tunneld服务:")
                logger.error(f"sudo {sys.executable} -m pymobiledevice3 remote tunneld")
                logger.error("然后重新运行此程序")
                return False
                
        except Exception as e:
            logger.error(f"权限提升失败: {e}")
            return False
    
    def _start_with_osascript(self) -> bool:
        """在macOS上使用osascript启动tunneld服务"""
        try:
            # 构建AppleScript命令
            script = f'''do shell script "{sys.executable} -m pymobiledevice3 remote tunneld" with administrator privileges'''
            
            logger.info("正在请求管理员权限...")
            
            # 使用osascript执行命令
            cmd = ["osascript", "-e", script]
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # 等待服务启动
            time.sleep(5)
            
            if self.process.poll() is None and self.is_running():
                logger.info("tunneld 服务已使用管理员权限启动成功")
                self.started = True
                return True
            else:
                # 检查是否用户取消了权限请求
                stderr_output = ""
                if self.process:
                    try:
                        stdout, stderr = self.process.communicate(timeout=1)
                        if stderr:
                            stderr_output = stderr.decode()
                    except subprocess.TimeoutExpired:
                        pass
                
                if "User canceled" in stderr_output or "cancelled" in stderr_output:
                    logger.warning("用户取消了管理员权限请求")
                    logger.info("如需连接iPad设备，请重新运行并授予管理员权限")
                else:
                    logger.error("使用管理员权限启动tunneld服务失败")
                    if stderr_output:
                        logger.error(f"错误信息: {stderr_output}")
                
                return False
                
        except Exception as e:
            logger.error(f"使用osascript启动tunneld服务失败: {e}")
            return False
    
    def stop(self) -> None:
        """停止 tunneld 服务"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("tunneld 服务已停止")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("强制终止 tunneld 服务")
            except Exception as e:
                logger.error(f"停止 tunneld 服务失败: {e}")
        
        self.started = False
        self.process = None


class ConnectionService:
    """连接服务类
    
    负责与iPad设备建立USB连接并获取屏幕截图。
    仅支持pymobiledevice3 + tunneld的USB连接方式。
    """
    
    def __init__(self, auto_start_tunneld: bool = True, config: Optional[dict] = None):
        """初始化连接服务
        
        Args:
            auto_start_tunneld: 是否自动启动tunneld服务
            config: 配置字典
        """
        if not PYMOBILEDEVICE3_AVAILABLE:
            raise ConnectionError("pymobiledevice3 未安装，无法使用连接服务")
        
        # 配置相关
        self.config = config or {}
        device_config = self.config.get('device', {})
        screenshot_config = device_config.get('screenshot', {})
        
        # 截图配置
        self.screenshot_timeout = screenshot_config.get('timeout', 15)
        self.screenshot_max_retries = screenshot_config.get('max_retries', 3)
        self.screenshot_retry_interval = screenshot_config.get('retry_interval', 2)
        self.external_timeout = screenshot_config.get('external_timeout', 10)
        self.quality_check = screenshot_config.get('quality_check', True)
        self.min_file_size = screenshot_config.get('min_file_size', 1024)
        
        self.auto_start_tunneld = auto_start_tunneld
        self.tunneld_manager = TunneldManager()
        
        # 连接状态
        self._status = ConnectionStatus.DISCONNECTED
        self._device_info: Optional[DeviceInfo] = None
        
        # pymobiledevice3 对象
        self._lockdown_client = None
        self._screenshot_service = None
        self._dvt_screenshot = None
        self._use_external_screenshot = False
        
        # 性能统计
        self._last_screenshot_time: Optional[float] = None
        self._screenshot_count = 0
    
    @property
    def status(self) -> ConnectionStatus:
        """获取连接状态"""
        return self._status
    
    @property
    def device_info(self) -> Optional[DeviceInfo]:
        """获取设备信息"""
        return self._device_info
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._status == ConnectionStatus.CONNECTED
    
    def connect(self, timeout: float = 30.0) -> bool:
        """连接到iPad设备
        
        Args:
            timeout: 连接超时时间（秒）
            
        Returns:
            bool: 连接是否成功
            
        Raises:
            ConnectionError: 连接失败
            DeviceNotFoundError: 设备未找到
            TunneldError: tunneld服务异常
        """
        if self.is_connected:
            logger.info("设备已连接")
            return True
        
        self._status = ConnectionStatus.CONNECTING
        start_time = time.time()
        
        try:
            # 启动tunneld服务
            if self.auto_start_tunneld and not self.tunneld_manager.is_running():
                logger.info("启动tunneld服务...")
                if not self.tunneld_manager.start():
                    raise TunneldError("无法启动tunneld服务")
            
            # 连接设备
            logger.info("正在连接USB设备...")
            
            try:
                # 创建 lockdown 客户端
                self._lockdown_client = create_using_usbmux()
                
                # 获取设备信息
                device_name = self._lockdown_client.get_value('DeviceName') or "Unknown Device"
                product_version = self._lockdown_client.get_value('ProductVersion') or "Unknown"
                device_class = self._lockdown_client.get_value('DeviceClass') or "Unknown"
                udid = self._lockdown_client.get_value('UniqueDeviceID') or "Unknown"
                
                logger.info(f"检测到设备: {device_name} (iOS {product_version}, {device_class})")
                
                # 尝试创建截图服务
                screen_width, screen_height = 0, 0
                screenshot_service_created = False
                
                try:
                    self._screenshot_service = ScreenshotService(lockdown=self._lockdown_client)
                    logger.info("标准截图服务初始化成功")
                    
                    # 测试截图功能
                    test_screenshot = self._take_screenshot()
                    if test_screenshot is not None:
                        screen_height, screen_width = test_screenshot.shape[:2]
                        logger.info(f"屏幕尺寸: {screen_width}x{screen_height}")
                        screenshot_service_created = True
                    else:
                        screen_width, screen_height = 0, 0
                        logger.warning("无法获取屏幕尺寸")
                    
                except InvalidServiceError as e:
                    logger.warning(f"标准截图服务不可用: {e}")
                    logger.info("尝试使用外部命令进行截图...")
                    
                    # 清理当前连接
                    self._cleanup_connection()
                    
                    # 确保 tunneld 服务运行
                    if not self.tunneld_manager.is_running():
                        logger.info("启动tunneld服务以支持开发者功能...")
                        if not self.tunneld_manager.start():
                            raise TunneldError("无法启动tunneld服务")
                        # 等待服务启动
                        time.sleep(2)
                    
                    # 标记使用外部命令截图
                    self._use_external_screenshot = True
                    screenshot_service_created = True
                    logger.info("将使用外部命令进行截图")
                    
                    # 测试外部截图命令（使用更短的超时时间）
                    try:
                        logger.info("正在测试外部截图命令...")
                        test_screenshot = self._take_external_screenshot_with_timeout(5)  # 使用5秒超时
                        if test_screenshot is not None:
                            screen_height, screen_width = test_screenshot.shape[:2]
                            logger.info(f"屏幕尺寸: {screen_width}x{screen_height}")
                        else:
                            logger.warning("外部截图测试失败，可能设备未连接或权限不足")
                            raise ConnectionError(f"所有截图方法都不可用。标准服务错误: {e}")
                    except Exception as ext_e:
                        logger.error(f"外部截图命令也失败: {ext_e}")
                        raise ConnectionError(f"所有截图方法都不可用。标准服务错误: {e}，外部命令错误: {ext_e}")
                        
                except Exception as e:
                    logger.error(f"截图服务初始化失败: {e}")
                    logger.debug(f"异常类型: {type(e).__name__}")
                    logger.debug(f"异常详情: {str(e)}")
                    
                    # 输出更详细的调试信息
                    import traceback
                    logger.debug(f"完整异常堆栈:\n{traceback.format_exc()}")
                    
                    self._cleanup_connection()
                    
                    if "PasswordRequired" in str(e):
                        raise ConnectionError(f"设备需要解锁并信任此电脑。详细错误: {e}")
                    else:
                        raise ConnectionError(f"截图服务初始化失败: {e}")
                
                if not screenshot_service_created:
                    raise ConnectionError("无法创建任何可用的截图服务")
                
                # 创建设备信息对象
                self._device_info = DeviceInfo(
                    udid=udid,
                    name=device_name,
                    ios_version=product_version,
                    model=device_class,
                    screen_size=(screen_width, screen_height),
                    is_connected=True,
                    connection_type="usb"
                )
                
                self._status = ConnectionStatus.CONNECTED
                connection_time = time.time() - start_time
                logger.info(f"USB连接成功，耗时: {connection_time:.2f}秒")
                return True
                
            except NoDeviceConnectedError:
                raise DeviceNotFoundError("未检测到USB连接的iOS设备")
            except PairingError as e:
                raise ConnectionError(f"设备配对失败: {e}")
            except Exception as e:
                raise ConnectionError(f"连接失败: {e}")
            
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            self._cleanup_connection()
            
            if time.time() - start_time > timeout:
                raise DeviceConnectionTimeoutError(f"连接超时 ({timeout}秒)")
            
            # 重新抛出已知异常
            if isinstance(e, (ConnectionError, DeviceNotFoundError, TunneldError)):
                raise
            else:
                raise ConnectionError(f"连接失败: {e}")
    
    def disconnect(self) -> None:
        """断开设备连接"""
        if self._status == ConnectionStatus.DISCONNECTED:
            return
        
        logger.info("正在断开设备连接...")
        
        self._cleanup_connection()
        
        # 停止tunneld服务（如果是自动启动的）
        if self.auto_start_tunneld and self.tunneld_manager.started:
            self.tunneld_manager.stop()
        
        self._status = ConnectionStatus.DISCONNECTED
        self._device_info = None
        
        logger.info("设备连接已断开")
    
    def get_screenshot(self) -> Optional[np.ndarray]:
        """获取设备屏幕截图
        
        Returns:
            Optional[np.ndarray]: 屏幕截图图像数据，BGR格式
            
        Raises:
            ScreenshotError: 截图失败
        """
        if not self.is_connected:
            raise ScreenshotError("设备未连接，无法获取截图")
        
        try:
            start_time = time.time()
            screenshot = self._take_screenshot()
            
            if screenshot is not None:
                self._last_screenshot_time = time.time()
                self._screenshot_count += 1
                
                screenshot_time = time.time() - start_time
                logger.debug(f"截图成功，耗时: {screenshot_time:.3f}秒")
                
                # 检查是否需要自动保存截图
                self._auto_save_screenshot_if_enabled(screenshot)
                
                return screenshot
            else:
                raise ScreenshotError("截图数据为空")
                
        except Exception as e:
            if isinstance(e, ScreenshotError):
                raise
            else:
                raise ScreenshotError(f"获取截图失败: {e}")
    
    def _take_screenshot(self) -> Optional[np.ndarray]:
        """执行截图操作
        
        Returns:
            Optional[np.ndarray]: 截图数据，BGR格式
        """
        # 如果使用外部命令截图
        if hasattr(self, '_use_external_screenshot') and self._use_external_screenshot:
            return self._take_external_screenshot()
        
        # 优先使用标准截图服务
        if self._screenshot_service:
            try:
                # 获取截图数据
                screenshot_data = self._screenshot_service.take_screenshot()
                return self._process_screenshot_data(screenshot_data)
            except Exception as e:
                logger.warning(f"标准截图服务失败: {e}")
                # 如果标准服务失败，尝试 DVT 服务
        
        # 使用 DVT 截图服务
        if self._dvt_screenshot:
            return self._take_dvt_screenshot()
        
        logger.error("没有可用的截图服务")
        return None
    
    def _take_dvt_screenshot(self) -> Optional[np.ndarray]:
        """使用 DVT 服务执行截图操作
        
        Returns:
            Optional[np.ndarray]: 截图数据，BGR格式
        """
        if not self._dvt_screenshot:
            return None
        
        try:
            # 获取截图数据
            screenshot_data = self._dvt_screenshot.get_screenshot()
            return self._process_screenshot_data(screenshot_data)
            
        except Exception as e:
            logger.error(f"DVT 截图操作失败: {e}")
            return None
    
    def _take_external_screenshot(self) -> Optional[np.ndarray]:
         """使用外部命令执行截图操作
         
         Returns:
             Optional[np.ndarray]: 截图数据，BGR格式
         """
         return self._take_external_screenshot_with_timeout(10)
    
    def _take_external_screenshot_with_timeout(self, timeout_seconds: Optional[int] = None) -> Optional[np.ndarray]:
         """使用外部命令执行截图操作，支持自定义超时时间和重试机制
         
         Args:
             timeout_seconds: 超时时间（秒），如果为None则使用配置值
             
         Returns:
             Optional[np.ndarray]: 截图数据，BGR格式
         """
         if timeout_seconds is None:
             timeout_seconds = self.external_timeout
             
         max_retries = self.screenshot_max_retries
         retry_delay = self.screenshot_retry_interval
         
         for attempt in range(max_retries):
             try:
                 # 创建临时文件
                 with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                     temp_path = temp_file.name
                 
                 try:
                     # 使用 pymobiledevice3 命令行工具截图
                     cmd = [sys.executable, "-m", "pymobiledevice3", "developer", "dvt", "screenshot", temp_path]
                     
                     logger.debug(f"执行外部截图命令 (尝试 {attempt + 1}/{max_retries})，超时: {timeout_seconds}秒")
                     
                     result = subprocess.run(
                         cmd,
                         capture_output=True,
                         timeout=timeout_seconds,
                         text=True
                     )
                     
                     if result.returncode == 0 and os.path.exists(temp_path):
                         # 检查文件大小
                         file_size = os.path.getsize(temp_path)
                         
                         # 检查文件大小是否符合要求
                         if self.quality_check and file_size < self.min_file_size:
                             logger.warning(f"截图文件过小: {file_size} 字节 (最小要求: {self.min_file_size} 字节) (尝试 {attempt + 1}/{max_retries})")
                         elif file_size > 0:
                             # 读取截图文件
                             with open(temp_path, 'rb') as f:
                                 screenshot_data = f.read()
                             logger.debug(f"外部截图成功，文件大小: {file_size} 字节")
                             return self._process_screenshot_data(screenshot_data)
                         else:
                             logger.warning(f"外部截图文件为空 (尝试 {attempt + 1}/{max_retries})")
                     else:
                         error_msg = result.stderr.strip() if result.stderr else '未知错误'
                         logger.warning(f"外部截图命令失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                         
                 finally:
                     # 清理临时文件
                     if os.path.exists(temp_path):
                         os.unlink(temp_path)
                 
             except subprocess.TimeoutExpired:
                 logger.warning(f"外部截图命令超时 (尝试 {attempt + 1}/{max_retries})，超时时间: {timeout_seconds}秒")
             except Exception as e:
                 logger.warning(f"外部截图命令异常 (尝试 {attempt + 1}/{max_retries}): {e}")
             
             # 如果不是最后一次尝试，等待后重试
             if attempt < max_retries - 1:
                 logger.debug(f"等待 {retry_delay} 秒后重试...")
                 time.sleep(retry_delay)
                 retry_delay *= 1.5  # 指数退避
         
         logger.error(f"外部截图命令在 {max_retries} 次尝试后仍然失败")
         return None
    
    def _process_screenshot_data(self, screenshot_data: bytes) -> Optional[np.ndarray]:
        """处理截图数据，转换为 numpy 数组
        
        Args:
            screenshot_data: 原始截图字节数据
            
        Returns:
            Optional[np.ndarray]: 处理后的截图数据，BGR格式
        """
        try:
            # 将字节数据转换为PIL图像
            image = Image.open(io.BytesIO(screenshot_data))
            
            # 确保图像是RGB格式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 转换为numpy数组 (RGB -> BGR for OpenCV)
            img_array = np.array(image)
            img_bgr = img_array[:, :, ::-1]  # RGB to BGR
            
            return img_bgr
            
        except Exception as e:
            logger.error(f"处理截图数据失败: {e}")
            return None
    
    def _auto_save_screenshot_if_enabled(self, screenshot: np.ndarray) -> None:
        """如果启用了自动保存，则保存截图
        
        Args:
            screenshot: 截图数据，BGR格式
        """
        try:
            # 获取配置
            config = get_config()
            
            if config.auto_save_screenshots:
                # 获取截图保存目录
                from ..utils.config import get_config_manager
                config_manager = get_config_manager()
                screenshot_dir = config_manager.get_screenshot_dir()
                
                # 确保目录存在
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成文件名（使用时间戳）
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
                filename = f"auto_screenshot_{timestamp}.png"
                filepath = screenshot_dir / filename
                
                # 转换BGR到RGB并保存
                screenshot_rgb = screenshot[:, :, ::-1]  # BGR to RGB
                image = Image.fromarray(screenshot_rgb)
                image.save(filepath)
                
                logger.debug(f"自动保存截图: {filename}")
                
        except Exception as e:
            logger.warning(f"自动保存截图失败: {e}")
    
    def _cleanup_connection(self) -> None:
        """清理连接资源"""
        if self._screenshot_service:
            self._screenshot_service = None
        
        if self._dvt_screenshot:
            self._dvt_screenshot = None
        
        if self._lockdown_client:
            self._lockdown_client = None
            
        # 重置外部截图标志
        self._use_external_screenshot = False
    
    def get_statistics(self) -> dict:
        """获取连接统计信息"""
        return {
            "status": self._status.value,
            "device_info": self._device_info.__dict__ if self._device_info else None,
            "screenshot_count": self._screenshot_count,
            "last_screenshot_time": self._last_screenshot_time,
            "tunneld_running": self.tunneld_manager.is_running()
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()