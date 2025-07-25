# iPad自动化系统重构产品需求文档

## 项目概述

### 项目名称
iPad自动化控制系统 v2.0

### 项目目标
重构现有的iPad自动化系统，构建一个简洁、高效、可扩展的自动化框架，专注于游戏自动化场景。

### 核心价值
- **简洁性**：移除冗余代码和多余的连接方式，专注核心功能
- **可靠性**：使用稳定的pymobiledevice3作为唯一连接方案
- **扩展性**：为未来VLM大模型集成预留接口
- **灵活性**：支持自动执行和手动确认两种模式

## 系统架构设计

### 整体架构
```
┌─────────────────────────────────────────────────────────┐
│                    iPad自动化系统                        │
├─────────────────────────────────────────────────────────┤
│  用户界面层 (UI Layer)                                   │
│  - 命令行界面                                           │
│  - 配置管理                                             │
│  - 日志输出                                             │
├─────────────────────────────────────────────────────────┤
│  业务逻辑层 (Business Logic Layer)                       │
│  - 任务管理器                                           │
│  - 决策引擎                                             │
│  - 执行策略                                             │
├─────────────────────────────────────────────────────────┤
│  核心服务层 (Core Services Layer)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │ 连接服务    │ │ 视觉服务    │ │ 执行服务    │        │
│  │ Connection  │ │ Vision      │ │ Action      │        │
│  │ Service     │ │ Service     │ │ Service     │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
├─────────────────────────────────────────────────────────┤
│  设备接口层 (Device Interface Layer)                     │
│  - pymobiledevice3                                      │
│  - tunneld                                              │
│  - WebDriverAgent                                       │
└─────────────────────────────────────────────────────────┘
```

## 功能模块详细设计

### 1. 连接服务 (Connection Service)

#### 功能描述
负责与iPad设备建立连接并获取屏幕截图

#### 技术要求
- **唯一连接方式**：pymobiledevice3 + tunneld
- **物理连接**：仅支持USB连接
- **截图功能**：高效的屏幕截图获取

#### 核心接口
```python
class ConnectionService:
    def connect() -> bool
    def disconnect() -> bool
    def get_screenshot() -> np.ndarray
    def get_device_info() -> dict
    def is_connected() -> bool
```

#### 实现要点
- 移除所有非pymobiledevice3的连接方式
- 移除网络连接、AirPlay、模拟等模式
- 专注USB连接的稳定性和性能优化
- 统一错误处理和重连机制

### 2. 视觉服务 (Vision Service)

#### 功能描述
提供通用的图像识别和分析能力，支持模板匹配和VLM扩展

#### 设计原则
- **当前版本**：基于OpenCV的模板匹配
- **未来扩展**：预留VLM大模型接口
- **通用性**：统一的识别接口和结果格式

#### 核心接口
```python
class VisionService:
    def analyze_screen(image: np.ndarray, context: str = None) -> AnalysisResult
    def find_template(image: np.ndarray, template_name: str) -> MatchResult
    def find_multiple_templates(image: np.ndarray, template_names: list) -> list[MatchResult]
    def register_vlm_provider(provider: VLMProvider) -> bool
```

#### 识别结果格式
```python
@dataclass
class AnalysisResult:
    success: bool
    confidence: float
    elements: list[Element]
    suggestions: list[ActionSuggestion]
    raw_data: dict

@dataclass
class Element:
    name: str
    position: tuple[int, int]
    size: tuple[int, int]
    confidence: float
    element_type: str  # button, text, icon, etc.

@dataclass
class ActionSuggestion:
    action_type: str  # tap, swipe, wait, etc.
    target: Element
    parameters: dict
    priority: int
    description: str
```

#### VLM扩展接口
```python
class VLMProvider:
    def analyze_image(image: np.ndarray, prompt: str) -> VLMResult
    def get_capabilities() -> list[str]
    def get_model_info() -> dict
```

### 3. 执行服务 (Action Service)

#### 功能描述
负责在iPad上执行各种操作，支持自动执行和手动确认模式

#### 执行模式
1. **自动模式**：直接执行操作
2. **确认模式**：显示建议操作，等待用户确认
3. **建议模式**：仅显示建议，不执行操作

#### 核心接口
```python
class ActionService:
    def execute_action(action: Action, mode: ExecutionMode = ExecutionMode.AUTO) -> ExecutionResult
    def execute_actions(actions: list[Action], mode: ExecutionMode = ExecutionMode.AUTO) -> list[ExecutionResult]
    def set_execution_mode(mode: ExecutionMode) -> None
    def get_supported_actions() -> list[str]
```

#### 操作类型
```python
@dataclass
class Action:
    action_type: str  # tap, swipe, long_press, type_text, wait
    target: Element | tuple[int, int]
    parameters: dict
    timeout: float = 5.0
    retry_count: int = 3
    description: str = ""

class ExecutionMode(Enum):
    AUTO = "auto"          # 自动执行
    CONFIRM = "confirm"    # 需要确认
    SUGGEST = "suggest"    # 仅建议
```

#### iOS自动化方案
- **主要方案**：WebDriverAgent + Appium
- **备选方案**：预留其他iOS自动化框架接口
- **优雅降级**：操作失败时的处理策略

## 项目结构重构

### 新的目录结构
```
ipad-automation/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── templates.yaml
├── src/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── vision.py
│   │   └── action.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── task_manager.py
│   │   ├── decision_engine.py
│   │   └── execution_strategy.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── data_types.py
│   │   └── exceptions.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
├── resources/
│   ├── templates/
│   └── screenshots/
├── tests/
│   ├── __init__.py
│   ├── test_connection.py
│   ├── test_vision.py
│   └── test_action.py
├── examples/
│   ├── basic_usage.py
│   └── game_automation.py
└── docs/
    ├── api.md
    ├── configuration.md
    └── troubleshooting.md
```

### 需要移除的文件
- 所有WebDriverAgent相关文件
- AirPlay相关文件
- 网络连接相关文件
- 模拟模式相关文件
- 冗余的测试文件
- 过时的配置文件

### 需要保留的文件
- 核心的pymobiledevice3连接逻辑
- 模板匹配相关代码
- 基础的任务管理逻辑
- 有效的模板资源

## 开发计划

### 第一阶段：架构重构 (1-2天)
1. 创建新的项目结构
2. 重构连接服务，移除多余连接方式
3. 重构视觉服务，统一识别接口
4. 重构执行服务，实现执行模式

### 第二阶段：功能完善 (2-3天)
1. 实现任务管理器
2. 实现决策引擎
3. 完善错误处理和日志系统
4. 编写单元测试

### 第三阶段：文档和示例 (1天)
1. 编写API文档
2. 创建使用示例
3. 编写配置指南
4. 完善README

### 第四阶段：测试和优化 (1-2天)
1. 集成测试
2. 性能优化
3. 稳定性测试
4. 用户体验优化

## 配置管理

### 配置文件结构
```yaml
# config/settings.yaml
connection:
  timeout: 30
  retry_count: 3
  screenshot_format: "png"

vision:
  template_threshold: 0.8
  max_templates: 10
  vlm_enabled: false
  vlm_provider: null

action:
  execution_mode: "auto"  # auto, confirm, suggest
  default_timeout: 5.0
  retry_count: 3
  webdriver_url: "http://localhost:8100"

logging:
  level: "INFO"
  file: "logs/automation.log"
  max_size: "10MB"
  backup_count: 5

game:
  name: "三国志战略版"
  package_id: "com.koei.sangokushi"
  templates_path: "resources/templates"
```

## 质量保证

### 代码质量
- 使用类型注解
- 遵循PEP 8规范
- 单元测试覆盖率 > 80%
- 文档字符串完整

### 性能要求
- 截图获取 < 1秒
- 模板匹配 < 0.5秒
- 操作执行 < 2秒
- 内存使用 < 200MB

### 稳定性要求
- 连接成功率 > 95%
- 操作成功率 > 90%
- 7x24小时稳定运行
- 自动错误恢复

## 风险评估

### 技术风险
1. **pymobiledevice3兼容性**：可能存在iOS版本兼容问题
2. **WebDriverAgent稳定性**：可能出现连接中断
3. **模板匹配准确性**：游戏界面变化可能影响识别

### 缓解措施
1. 充分测试不同iOS版本
2. 实现自动重连机制
3. 提供模板更新工具
4. 预留VLM接口作为备选方案

## 成功标准

### 功能标准
- [x] 支持USB连接iPad
- [x] 支持屏幕截图获取
- [x] 支持模板匹配识别
- [x] 支持基本触控操作
- [x] 支持多种执行模式
- [x] 预留VLM扩展接口

### 性能标准
- [x] 代码行数减少50%以上
- [x] 启动时间 < 10秒
- [x] 响应时间 < 3秒
- [x] 内存占用 < 200MB

### 可维护性标准
- [x] 模块化设计
- [x] 清晰的接口定义
- [x] 完整的文档
- [x] 充分的测试覆盖

---

**文档版本**：v1.0  
**创建日期**：2024年7月24日  
**最后更新**：2024年7月24日  
**负责人**：开发团队