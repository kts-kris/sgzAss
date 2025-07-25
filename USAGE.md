# 三国志战略版自动化助手使用说明

本文档详细介绍了如何设置和使用三国志战略版自动化助手，帮助您自动完成游戏中的重复性操作。

## 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [初始化项目](#初始化项目)
4. [模板采集](#模板采集)
5. [配置系统](#配置系统)
6. [运行助手](#运行助手)
7. [iPad客户端设置](#ipad客户端设置)
8. [常见问题](#常见问题)
9. [进阶使用](#进阶使用)

## 系统要求

### 电脑端

- Python 3.8 或更高版本
- macOS、Windows 或 Linux 操作系统
- 足够的磁盘空间（至少 500MB）

### iPad端

- iPad Pro 或其他可运行三国志战略版的iPad设备
- 与电脑在同一网络环境下，或通过有线方式连接
- 可选：安装 Pythonista 或其他可运行Python的应用（用于网络连接模式）

## 安装步骤

1. 克隆或下载本项目到您的电脑

2. 安装依赖包

```bash
pip install -r requirements.txt
```

3. 如果您使用的是macOS，可能需要安装额外的依赖

```bash
brew install opencv
brew install tesseract
```

4. 如果您使用的是Windows，确保已安装Visual C++ Redistributable

## 初始化项目

运行初始化脚本，创建必要的目录结构和文件：

```bash
python init_project.py
```

这将创建以下目录结构：

```
├── core/               # 核心功能模块
├── utils/              # 工具函数
├── tasks/              # 任务实现
├── resources/          # 资源文件
│   ├── templates/      # 模板图像
│   └── screenshots/    # 屏幕截图
├── logs/               # 日志文件
├── client/             # iPad客户端
└── tools/              # 辅助工具
```

## 模板采集

在使用助手之前，需要先采集游戏界面元素的模板图像，以便系统能够识别游戏中的各种元素。

### 运行模板采集工具

```bash
python tools/template_collector.py
```

### 采集步骤

1. 选择连接方式（模拟模式、网络连接或USB连接）
2. 获取屏幕截图
3. 在截图上框选要采集的元素
4. 输入模板名称（参考`config.py`中的`GAME_TEMPLATES`列表）
5. 重复步骤2-4，采集所有需要的模板

### 必要的模板

以下是系统正常运行所必需的模板：

- `main_menu`：游戏主界面
- `world_map`：世界地图
- `empty_land`：空闲土地
- `resource_point`：资源点
- `army_idle`：空闲部队
- `confirm_button`：确认按钮
- `cancel_button`：取消按钮
- `back_button`：返回按钮

## 配置系统

编辑`config.py`文件，根据您的需求调整系统配置：

### 游戏设置

```python
GAME_SETTINGS = {
    # 匹配阈值：图像识别的匹配度阈值，值越高要求越精确
    "match_threshold": 0.8,  # 可根据识别效果调整
    
    # 操作延迟：模拟人类操作的随机延迟范围（秒）
    "action_delay_min": 0.5,  # 最小延迟
    "action_delay_max": 1.5,  # 最大延迟
    
    # 安全设置
    "enable_safe_mode": True,  # 启用安全模式
    "max_continuous_actions": 50,  # 最大连续操作次数
}
```

### 设备连接设置

```python
DEVICE_SETTINGS = {
    # 连接方式：'usb'、'network'或'simulation'
    "connection_type": "network",
    
    # 网络连接设置
    "device_ip": "192.168.1.100",  # iPad的IP地址
    "device_port": 5555,  # 连接端口
    
    # 屏幕分辨率
    "screen_width": 2732,  # iPad Pro默认宽度
    "screen_height": 2048,  # iPad Pro默认高度
}
```

### 任务设置

```python
TASK_SETTINGS = {
    # 土地占领任务
    "land_occupation": {
        "enabled": True,  # 是否启用
        "target_count": 10,  # 目标占领数量
        "prefer_resources": True,  # 优先占领资源点
    },
    
    # 部队移动任务
    "army_movement": {
        "enabled": True,  # 是否启用
        "idle_army_check_interval": 300,  # 检查间隔（秒）
    },
}
```

## 运行助手

### 基本运行

```bash
python main.py
```

### 运行选项

```bash
python main.py --task land  # 只执行土地占领任务
python main.py --task army  # 只执行部队移动任务
python main.py --debug  # 启用调试模式
python main.py --dry-run  # 仅识别不执行操作
python main.py --duration 60  # 运行60分钟后自动停止
```

## iPad客户端设置

如果您选择使用网络连接模式，需要在iPad上设置客户端。

### 使用Pythonista（推荐）

1. 在iPad上安装Pythonista应用
2. 将`client/ipad_client.py`文件复制到Pythonista
3. 安装必要的依赖（可能需要使用StaSh）
4. 运行客户端脚本

```python
python ipad_client.py --host 0.0.0.0 --port 5555
```

### 使用其他方法

如果您不想使用Pythonista，也可以考虑以下方法：

1. 使用VNC或远程桌面软件
2. 使用iOS自动化工具如Shortcuts
3. 使用模拟模式（在电脑上模拟iPad屏幕）

## 常见问题

### 识别不准确

**问题**：系统无法正确识别游戏元素。

**解决方案**：
- 重新采集更清晰的模板
- 调整`match_threshold`值
- 确保游戏界面没有遮挡

### 连接失败

**问题**：无法连接到iPad设备。

**解决方案**：
- 确认iPad和电脑在同一网络下
- 检查IP地址和端口设置
- 确认防火墙未阻止连接

### 操作不响应

**问题**：系统识别了元素但点击操作无效。

**解决方案**：
- 调整操作延迟设置
- 检查iPad是否进入了休眠状态
- 确认游戏未被其他应用覆盖

## 进阶使用

### 自定义任务

您可以通过创建新的任务类来扩展系统功能：

1. 在`tasks`目录下创建新的任务文件
2. 继承`BaseTask`类并实现必要的方法
3. 在`TaskManager`中注册新任务

### 优化模板识别

对于复杂的游戏界面，可以采用以下策略提高识别准确率：

1. 使用多个特征点而非整个界面元素
2. 为同一元素创建多个模板（不同状态）
3. 结合颜色过滤和边缘检测

### 安全措施

为避免过度使用导致游戏账号风险，建议：

1. 启用安全模式
2. 设置合理的操作间隔
3. 避免24小时持续运行
4. 定期手动检查游戏状态

---

## 免责声明

本工具仅供学习和研究目的使用。使用者应自行承担使用本工具的风险和责任。开发者不对因使用本工具而导致的任何问题负责。

请确保您的使用符合游戏服务条款和相关法律法规。