# 三国志战略版 iPad 自动化助手

基于 USB 连接的 iPad 自动化控制系统，专为三国志战略版游戏设计，通过截图分析和模板匹配实现智能操作建议和自动化执行。

## 🎮 项目简介

本项目的核心是通过 USB 与 iPad 连接，实现对 iPad 上运行的三国志战略版进行截图，并分析当前用户操作，给出操作建议或者自动化操作。系统采用先进的视觉识别技术，能够准确识别游戏界面元素，为玩家提供智能化的游戏辅助。

## ✨ 核心特性

### 🔌 USB 连接技术
- **稳定连接**: 基于 pymobiledevice3 和 tunneld 实现的高稳定性 USB 连接
- **实时通信**: 低延迟的设备通信，确保操作响应及时
- **自动重连**: 智能的连接恢复机制，保证长时间稳定运行

### 📸 智能截图分析
- **高效截图**: 实时获取 iPad 屏幕内容，支持高分辨率显示
- **游戏识别**: 专门针对三国志战略版界面优化的识别算法
- **元素定位**: 精确识别按钮、菜单、地图等游戏元素

### 🧠 智能决策系统
- **操作建议**: 基于当前游戏状态提供最优操作建议
- **自动执行**: 支持完全自动化的游戏操作执行
- **策略分析**: 深度分析游戏局面，提供战略级建议

### 🎯 游戏专用功能
- **地图导航**: 智能的世界地图和城池导航
- **资源管理**: 自动化的资源收集和管理
- **战斗辅助**: 战斗界面的智能操作建议
- **建设优化**: 城池建设的最优化建议

## 🏗️ 系统架构

```
📁 sgzAss/
├── 🔧 src/                    # 核心源代码
│   ├── 📊 models/             # 数据模型定义
│   │   ├── data_types.py      # 游戏数据类型
│   │   ├── exceptions.py      # 异常处理
│   │   └── __init__.py
│   ├── 🛠️ services/           # 核心服务层
│   │   ├── connection.py      # iPad 连接服务
│   │   ├── vision.py          # 视觉识别服务
│   │   ├── automation.py      # 自动化执行服务
│   │   └── __init__.py
│   ├── 🎮 core/               # 游戏逻辑层
│   │   ├── controller.py      # 主控制器
│   │   ├── task_manager.py    # 任务管理器
│   │   └── __init__.py
│   └── 🔨 utils/              # 工具函数
│       ├── config.py          # 配置管理
│       ├── logger.py          # 日志系统
│       ├── helpers.py         # 辅助函数
│       └── __init__.py
├── 🖼️ resources/              # 游戏资源
│   ├── templates/             # 模板图片库
│   │   ├── attack_button.png  # 攻击按钮
│   │   ├── back_button.png    # 返回按钮
│   │   ├── confirm_button.png # 确认按钮
│   │   ├── main_menu.png      # 主菜单
│   │   ├── world_map.png      # 世界地图
│   │   └── ...
│   └── screenshots/           # 自动截图存储
├── 🛠️ tools/                  # 开发工具
│   ├── template_maker.py      # 模板制作工具
│   ├── config_editor.py       # 配置编辑器
│   ├── analyze_logs.py        # 日志分析工具
│   └── ...
├── 📝 logs/                   # 日志文件
├── ⚙️ config.yaml             # 主配置文件
└── 📖 README.md               # 项目文档
```

## 🚀 快速开始

### 环境要求

- **操作系统**: macOS 10.15+ 或 Linux
- **Python**: 3.8 或更高版本
- **设备**: iPad (iOS 12+)
- **连接**: USB 数据线
- **游戏**: 三国志战略版 App

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd sgzAss
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **设备准备**
   - 在 iPad 上安装三国志战略版
   - 启用 iPad 开发者模式
   - 使用 USB 连接 iPad 到电脑
   - 在 iPad 上信任此电脑

### 基础使用

```python
from src import quick_start, ExecutionMode

# 启动系统
controller, task_manager = quick_start(
    execution_mode=ExecutionMode.SUGGEST_ONLY  # 建议模式
)

# 连接 iPad
print("正在连接 iPad...")
controller.connect()
print("连接成功！")

# 获取游戏截图
screenshot = controller.get_screenshot()
print(f"截图获取成功: {screenshot.size}")

# 分析当前游戏界面
analysis = controller.analyze_screen(screenshot)
print(f"识别到 {len(analysis.elements)} 个游戏元素")

# 查找特定按钮
attack_button = controller.find_element("attack_button.png")
if attack_button:
    print(f"发现攻击按钮: {attack_button.location}")
    # 获取操作建议
    suggestion = controller.get_action_suggestion(attack_button)
    print(f"建议操作: {suggestion.description}")

# 断开连接
controller.disconnect()
```

## 🎮 游戏功能

### 界面识别

系统能够识别三国志战略版的各种界面元素：

```python
# 主界面识别
main_menu = controller.find_element("main_menu.png")
if main_menu:
    print("当前在主界面")

# 世界地图识别
world_map = controller.find_element("world_map.png")
if world_map:
    print("当前在世界地图")
    # 分析地图上的可操作元素
    map_elements = controller.analyze_map_elements()
    for element in map_elements:
        print(f"发现: {element.type} - {element.description}")
```

### 自动化任务

```python
# 创建资源收集任务
task = task_manager.create_task("资源收集")

# 添加任务步骤
task_manager.add_step(task.id, "点击主城")
task_manager.add_step(task.id, "进入资源建筑")
task_manager.add_step(task.id, "收集资源")
task_manager.add_step(task.id, "返回主界面")

# 执行任务
result = task_manager.execute_task(task.id)
if result.success:
    print(f"任务完成! 收集了 {result.resources_collected} 资源")
```

### 战斗辅助

```python
# 战斗界面分析
battle_analysis = controller.analyze_battle_screen()
print(f"我方兵力: {battle_analysis.our_troops}")
print(f"敌方兵力: {battle_analysis.enemy_troops}")
print(f"胜率预测: {battle_analysis.win_probability:.1%}")

# 获取战斗建议
battle_suggestion = controller.get_battle_suggestion(battle_analysis)
print(f"建议策略: {battle_suggestion.strategy}")
print(f"推荐操作: {battle_suggestion.recommended_actions}")
```

## ⚙️ 配置说明

### 主配置文件 (config.yaml)

```yaml
# iPad 连接配置
connection:
  timeout: 30              # 连接超时时间(秒)
  retry_count: 3           # 重试次数
  tunneld_port: 5000       # tunneld 端口

# 视觉识别配置
vision:
  template_threshold: 0.8   # 模板匹配阈值
  enable_vlm: false        # 启用大模型识别
  template_dir: "resources/templates"
  screenshot_dir: "resources/screenshots"

# 自动化配置
automation:
  backend: "webdriver"     # 自动化后端
  execution_mode: "suggest" # 执行模式: execute/suggest
  action_delay: 0.5        # 操作间隔(秒)
  click_duration: 0.1      # 点击持续时间(秒)

# 游戏特定配置
game:
  auto_screenshot: true    # 自动截图
  screenshot_interval: 5   # 截图间隔(秒)
  save_analysis_results: true  # 保存分析结果

# 日志配置
logging:
  level: "INFO"
  file_enabled: true
  console_enabled: true
  performance_monitoring: true
```

## 🛠️ 开发工具

### 模板制作工具

```bash
# 启动模板制作工具
python tools/template_maker.py
```

这个工具帮助你：
- 从游戏截图中提取界面元素
- 创建高质量的模板图片
- 测试模板匹配效果
- 批量处理模板文件

### 配置编辑器

```bash
# 启动配置编辑器
python tools/config_editor.py
```

提供图形化界面来：
- 修改系统配置
- 测试连接设置
- 调整识别参数
- 导入/导出配置

### 日志分析工具

```bash
# 分析系统日志
python tools/analyze_logs.py --date 2024-01-20
```

功能包括：
- 性能统计分析
- 错误日志汇总
- 操作成功率统计
- 生成分析报告

## 🔍 故障排除

### 常见问题

**Q: iPad 连接失败**
```bash
# 检查设备连接
python tools/test_ipad_connection.py

# 重启 tunneld 服务
sudo pkill tunneld
python -m pymobiledevice3 remote tunneld
```

**Q: 模板识别不准确**
```python
# 调整识别阈值
config.vision.template_threshold = 0.9  # 提高精度

# 重新制作模板
python tools/template_maker.py --retrain
```

**Q: 操作延迟过高**
```yaml
# 优化配置
automation:
  action_delay: 0.2      # 减少延迟
  enable_fast_mode: true # 启用快速模式
```

### 调试模式

```python
# 启用详细日志
import logging
logging.getLogger().setLevel(logging.DEBUG)

# 启用性能监控
controller.enable_performance_monitoring()

# 保存调试截图
controller.enable_debug_screenshots()
```

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. **Fork 项目**
2. **创建功能分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **创建 Pull Request**

### 开发规范

- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明

本项目仅用于学习和研究目的。使用本软件时请：

- 遵守游戏服务条款
- 不要用于商业用途
- 尊重游戏公平性
- 承担使用风险

## 📞 支持与反馈

如果你遇到问题或有建议：

1. 📖 查看[文档](docs/)
2. 🔍 搜索[已知问题](issues)
3. 💬 创建[新问题](issues/new)
4. 📧 联系开发者

---

**让我们一起打造最智能的三国志战略版助手！** 🎮✨