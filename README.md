# iPad自动化控制系统 v2.0

基于pymobiledevice3的iPad自动化控制解决方案，支持USB连接、模板匹配、VLM视觉识别和多种自动化执行模式。

## 🚀 特性

### 核心功能
- **USB连接**: 使用pymobiledevice3和tunneld实现稳定的iPad USB连接
- **屏幕截图**: 高效的实时屏幕截图获取
- **视觉识别**: 基于模板匹配的界面元素识别，支持VLM大模型扩展
- **自动化执行**: 支持多种执行模式（执行/建议），优雅的iOS操作控制
- **任务编排**: 复杂任务流程的管理和调度

### 技术亮点
- **模块化架构**: 清晰的分层设计，易于维护和扩展
- **类型安全**: 完整的类型注解和数据验证
- **异常处理**: 统一的错误处理机制
- **配置管理**: 灵活的配置系统
- **日志系统**: 完善的日志记录和性能监控

## 📁 项目结构

```
src/
├── models/              # 数据模型和异常定义
│   ├── data_types.py   # 核心数据类型
│   ├── exceptions.py   # 自定义异常
│   └── __init__.py
├── services/           # 核心服务层
│   ├── connection.py   # 设备连接服务
│   ├── vision.py       # 视觉识别服务
│   ├── automation.py   # 自动化执行服务
│   └── __init__.py
├── core/               # 业务逻辑层
│   ├── controller.py   # 主控制器
│   ├── task_manager.py # 任务管理器
│   └── __init__.py
├── utils/              # 工具函数
│   ├── config.py       # 配置管理
│   ├── logger.py       # 日志工具
│   ├── helpers.py      # 通用函数
│   └── __init__.py
└── __init__.py         # 主模块入口
```

## 🛠️ 安装

### 环境要求
- Python 3.8+
- macOS (推荐) 或 Linux
- iPad设备 (iOS 12+)
- USB数据线

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd sgzAss

# 安装依赖
pip install -r requirements.txt

# 安装pymobiledevice3 (如果需要最新版本)
pip install --upgrade pymobiledevice3
```

### 设备准备

1. **启用开发者模式**: 在iPad设置中启用开发者模式
2. **信任电脑**: 首次连接时在iPad上信任电脑
3. **安装开发者磁盘镜像**: 系统会自动处理

## 🚀 快速开始

### 基础使用

```python
from src import quick_start, ExecutionMode

# 快速启动
controller, task_manager = quick_start(
    execution_mode=ExecutionMode.EXECUTE
)

# 连接设备
controller.connect()

# 获取截图
screenshot = controller.get_screenshot()

# 分析屏幕
analysis = controller.analyze_screen(screenshot)
print(f"识别到 {len(analysis.elements)} 个界面元素")

# 查找特定元素
element = controller.find_element("button_template.png")
if element:
    # 点击元素
    result = controller.click_element(element)
    print(f"点击结果: {result.success}")

# 断开连接
controller.disconnect()
```

### 任务编排

```python
from src import TaskManager, ConditionType

# 创建任务
task = task_manager.create_task("示例任务")

# 添加步骤
task_manager.add_click_element_step(task.id, "start_button.png")
task_manager.add_wait_step(task.id, 2.0)
task_manager.add_condition_step(
    task.id, 
    ConditionType.ELEMENT_EXISTS, 
    "success_dialog.png"
)

# 执行任务
result = task_manager.execute_task(task.id)
print(f"任务执行结果: {result.success}")
```

### 配置管理

```python
from src import get_config, ConfigManager

# 获取配置
config = get_config()
print(f"连接超时: {config.connection.timeout}秒")

# 更新配置
config_manager = ConfigManager()
config_manager.update_config({
    "vision": {
        "template_threshold": 0.9,
        "enable_vlm": True
    }
})
```

## 📖 详细文档

### 执行模式

系统支持两种执行模式：

- **EXECUTE**: 实际执行操作
- **SUGGEST_ONLY**: 仅提供操作建议，不执行

```python
from src import ExecutionMode

# 设置为建议模式
controller.set_execution_mode(ExecutionMode.SUGGEST_ONLY)

# 执行操作时会返回建议而不是实际执行
result = controller.click(100, 200)
print(result.suggestion)  # 输出操作建议
```

### 自动化后端

支持多种自动化后端：

- **webdriver**: 基于WebDriverAgent (推荐)
- **pymobiledevice**: 基于pymobiledevice3 (开发中)

```python
# 切换自动化后端
controller.set_automation_backend("webdriver")
```

### VLM大模型支持

系统预留了VLM大模型接口，支持未来扩展：

```python
# 启用VLM识别
controller.enable_vlm()

# VLM分析屏幕
vlm_result = controller.analyze_screen_with_vlm(screenshot)
print(vlm_result.description)
```

### 性能监控

```python
from src import PerformanceTimer

# 性能计时
with PerformanceTimer("screenshot") as timer:
    screenshot = controller.get_screenshot()

print(f"截图耗时: {timer.duration:.2f}秒")

# 获取系统状态
status = controller.get_system_status()
print(f"连接状态: {status.connection_status}")
print(f"性能统计: {status.performance_stats}")
```

## 🔧 配置说明

### 配置文件结构

```yaml
# config.yaml
connection:
  timeout: 30
  retry_count: 3
  tunneld_port: 5000

vision:
  template_threshold: 0.8
  enable_vlm: false
  vlm_provider: "openai"
  template_dir: "templates"

automation:
  backend: "webdriver"
  wda_port: 8100
  action_delay: 0.5
  click_duration: 0.1

logging:
  level: "INFO"
  file_enabled: true
  console_enabled: true
  max_file_size: "10MB"
  backup_count: 5
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_connection.py -v

# 生成覆盖率报告
pytest --cov=src tests/
```

## 🤝 贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 更新日志

### v2.0.0 (重构版本)
- 🔄 完全重构项目架构
- ✨ 新增模块化设计
- 🚀 优化性能和稳定性
- 📚 完善文档和类型注解
- 🛠️ 统一配置和日志系统
- 🔮 预留VLM大模型接口

### v1.x.x (历史版本)
- 基础功能实现
- 模板匹配识别
- 简单自动化操作

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果遇到问题或有建议，请：

1. 查看 [文档](docs/)
2. 搜索 [Issues](issues)
3. 创建新的 [Issue](issues/new)

---

**注意**: 本项目仅用于学习和研究目的，请遵守相关法律法规和设备使用条款。