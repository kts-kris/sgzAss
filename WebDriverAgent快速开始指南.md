# WebDriverAgent快速开始指南

本指南将帮助您快速设置和使用WebDriverAgent实现iPad自动化控制。

## 📋 前置要求

### 系统要求
- **操作系统**: macOS（WebDriverAgent仅支持macOS）
- **Python**: 3.8或更高版本
- **Xcode**: 最新版本（包含Command Line Tools）
- **设备**: iPad（iOS 10.0+）

### 硬件要求
- iPad通过USB连接到Mac
- 确保iPad已信任此电脑

## 🚀 快速安装

### 方法一：自动安装（推荐）

运行我们提供的自动安装脚本：

```bash
# 进入项目目录
cd /path/to/your/project

# 运行安装脚本
python scripts/setup_webdriver.py
```

安装脚本将自动完成以下步骤：
1. 检查系统要求
2. 安装Homebrew（如果未安装）
3. 安装Node.js和npm
4. 安装Appium
5. 安装XCUITest驱动
6. 安装libimobiledevice工具
7. 安装Python依赖
8. 检测连接的设备
9. 创建配置文件
10. 测试连接

### 方法二：手动安装

如果自动安装失败，可以按以下步骤手动安装：

#### 1. 安装Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. 安装Node.js
```bash
brew install node
```

#### 3. 安装Appium
```bash
npm install -g appium
```

#### 4. 安装XCUITest驱动
```bash
appium driver install xcuitest
```

#### 5. 安装libimobiledevice
```bash
brew install libimobiledevice
```

#### 6. 安装Python依赖
```bash
pip install -r requirements.txt
```

## 🔧 配置设备

### 1. 连接iPad
- 使用USB线连接iPad到Mac
- 在iPad上点击"信任此电脑"
- 输入iPad密码确认

### 2. 获取设备UDID
```bash
idevice_id -l
```

### 3. 配置文件
编辑 `config/webdriver_config.json`：

```json
{
  "webdriver": {
    "server_url": "http://localhost:4723",
    "udid": "你的设备UDID",
    "device_name": "iPad",
    "platform_version": "17.0",
    "bundle_id": "com.apple.springboard",
    "automation_name": "XCUITest"
  },
  "device": {
    "connection_type": "usb"
  }
}
```

## 🎯 快速测试

### 1. 启动Appium服务器
```bash
appium
```

### 2. 运行测试示例
```bash
python examples/webdriver_integration_example.py
```

### 3. 基本操作测试

创建一个简单的测试脚本：

```python
from core.webdriver_controller import WebDriverController

# 配置
config = {
    "udid": "你的设备UDID",
    "bundle_id": "com.apple.springboard",
    "server_url": "http://localhost:4723",
    "device_name": "iPad",
    "platform_version": "17.0"
}

# 连接并测试
with WebDriverController(config) as controller:
    # 获取屏幕尺寸
    size = controller.get_window_size()
    print(f"屏幕尺寸: {size}")
    
    # 点击屏幕中心
    if size:
        center_x, center_y = size[0] // 2, size[1] // 2
        controller.tap(center_x, center_y)
        print(f"点击屏幕中心: ({center_x}, {center_y})")
    
    # 执行滑动
    controller.swipe(100, 100, 200, 200, 500)
    print("执行滑动操作")
```

## 📱 常用操作

### 基本触控操作

```python
from core.webdriver_controller import WebDriverController

with WebDriverController(config) as controller:
    # 点击
    controller.tap(x=500, y=300)
    
    # 滑动
    controller.swipe(start_x=100, start_y=100, end_x=200, end_y=200, duration=500)
    
    # 长按
    controller.long_press(x=500, y=300, duration=1000)
    
    # 多点触控
    controller.multi_touch([(100, 100), (200, 200)], duration=500)
```

### 应用控制

```python
# 启动应用
controller.launch_app("com.apple.Preferences")

# 关闭应用
controller.close_app("com.apple.Preferences")

# 按Home键
controller.home_button()
```

### 图像识别和点击

```python
# 查找图像元素
position = controller.find_element_by_image("templates/button.png", threshold=0.8)
if position:
    print(f"找到元素位置: {position}")

# 等待图像出现并点击
success = controller.tap_image("templates/button.png", threshold=0.8, timeout=10)
if success:
    print("图像点击成功")
```

### 截图操作

```python
# 获取截图
screenshot = controller.get_screenshot()
if screenshot:
    with open("screenshot.png", "wb") as f:
        f.write(screenshot)
```

## 🔄 与现有项目集成

### 使用增强设备控制器

```python
from examples.webdriver_integration_example import EnhancedDeviceController

# 配置
config = {
    "connection_type": "usb",
    "udid": "你的设备UDID",
    "bundle_id": "com.apple.springboard",
    "server_url": "http://localhost:4723",
    "device_name": "iPad",
    "platform_version": "17.0"
}

# 使用增强控制器（结合截图和触控）
with EnhancedDeviceController(config) as controller:
    # 获取截图
    screenshot = controller.get_screenshot()
    
    # 执行触控操作
    controller.tap(500, 300)
    
    # 模板匹配和点击
    controller.find_and_tap_template("templates/button.png")
```

## 🛠️ 故障排除

### 常见问题

#### 1. Appium连接失败
```bash
# 检查Appium服务器状态
curl -s http://localhost:4723/status

# 重启Appium服务器
pkill -f appium
appium
```

#### 2. 设备未检测到
```bash
# 检查设备连接
idevice_id -l

# 重新信任设备
# 在iPad上：设置 > 通用 > 设备管理 > 信任开发者
```

#### 3. WebDriverAgent启动失败
- 确保Xcode已安装最新版本
- 检查iOS版本兼容性
- 重新安装XCUITest驱动：`appium driver install xcuitest`

#### 4. Python依赖问题
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 检查Appium-Python-Client版本
pip show Appium-Python-Client
```

### 调试技巧

#### 1. 启用详细日志
```bash
# 启动Appium时启用详细日志
appium --log-level debug
```

#### 2. 检查WebDriverAgent日志
```python
# 在代码中启用日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 3. 验证设备连接
```python
from core.webdriver_controller import WebDriverController

config = {"udid": "你的设备UDID", ...}
controller = WebDriverController(config)

if controller.connect():
    print("连接成功")
    size = controller.get_window_size()
    print(f"屏幕尺寸: {size}")
else:
    print("连接失败")
```

## 📚 进阶使用

### 自定义配置

```python
# 高级配置选项
config = {
    "udid": "你的设备UDID",
    "bundle_id": "com.apple.springboard",
    "server_url": "http://localhost:4723",
    "device_name": "iPad",
    "platform_version": "17.0",
    "automation_name": "XCUITest",
    "new_command_timeout": 300,
    "wda_launch_timeout": 60000,
    "wda_connection_timeout": 60000,
    "use_new_wda": False,
    "no_reset": True,
    "full_reset": False,
    "implicit_wait": 10,
    "explicit_wait": 30
}
```

### 批量操作

```python
# 定义操作序列
operations = [
    {"action": "tap", "x": 500, "y": 300},
    {"action": "swipe", "start_x": 100, "start_y": 100, "end_x": 200, "end_y": 200},
    {"action": "wait", "duration": 2},
    {"action": "tap_image", "template": "templates/button.png"}
]

# 执行操作序列
with WebDriverController(config) as controller:
    for op in operations:
        if op["action"] == "tap":
            controller.tap(op["x"], op["y"])
        elif op["action"] == "swipe":
            controller.swipe(op["start_x"], op["start_y"], op["end_x"], op["end_y"])
        elif op["action"] == "wait":
            time.sleep(op["duration"])
        elif op["action"] == "tap_image":
            controller.tap_image(op["template"])
```

## 🔗 相关资源

### 官方文档
- [Appium官方文档](https://appium.io/docs/en/about-appium/intro/)
- [WebDriverAgent GitHub](https://github.com/appium/WebDriverAgent)
- [XCUITest驱动文档](https://appium.io/docs/en/drivers/ios-xcuitest/)

### 社区资源
- [Appium社区论坛](https://discuss.appium.io/)
- [iOS自动化最佳实践](https://github.com/appium/appium/blob/master/docs/en/writing-running-appium/ios/ios-xcuitest.md)

### 项目文件
- `core/webdriver_controller.py` - WebDriverAgent控制器
- `examples/webdriver_integration_example.py` - 集成示例
- `scripts/setup_webdriver.py` - 自动安装脚本
- `config/webdriver_config.json` - 配置文件

## 💡 最佳实践

1. **连接管理**: 使用上下文管理器确保连接正确关闭
2. **错误处理**: 添加适当的异常处理和重试机制
3. **性能优化**: 合理设置超时时间，避免不必要的等待
4. **日志记录**: 启用详细日志以便调试
5. **模板管理**: 使用模板制作工具创建高质量的匹配模板
6. **设备管理**: 定期重启设备和Appium服务器以保持稳定性

---

现在您已经可以使用WebDriverAgent实现强大的iPad自动化控制了！如果遇到问题，请参考故障排除部分或查看相关文档。