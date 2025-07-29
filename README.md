# 三国志战略版 iPad 自动化助手

基于 USB 连接的 iPad 自动化控制系统，专为三国志战略版游戏设计，通过截图分析和模板匹配实现智能操作建议和自动化执行。

## 🎮 项目简介

本项目通过 USB 与 iPad 连接，实现对三国志战略版的智能分析和自动化操作。系统采用先进的视觉识别技术，能够准确识别游戏界面元素，为玩家提供智能化的游戏辅助。

## ✨ 核心特性

### 🔌 稳定连接
- 基于 pymobiledevice3 的高稳定性 USB 连接
- 自动重连机制，保证长时间稳定运行
- 低延迟的设备通信

### 📸 智能分析
- 实时截图获取和游戏界面识别
- 基于 Ollama 的本地视觉大模型分析
- 精确的游戏元素定位和状态识别

### 🧠 智能决策
- 基于当前游戏状态提供操作建议
- 支持完全自动化的游戏操作执行
- 深度分析游戏局面，提供战略级建议

### 🎯 游戏功能
- 地图导航和城池管理
- 资源收集和建设优化
- 战斗辅助和策略分析
- 任务自动化执行

## 🏗️ 系统架构

```
📁 sgzAss/
├── 🔧 src/                    # 核心源代码
│   ├── 📊 models/             # 数据模型
│   │   ├── data_types.py      # 游戏数据类型
│   │   └── exceptions.py      # 异常处理
│   ├── 🛠️ services/           # 核心服务
│   │   ├── connection.py      # iPad 连接服务
│   │   ├── vision.py          # 视觉识别服务
│   │   ├── ollama_vlm.py      # Ollama 视觉模型
│   │   ├── automation.py      # 自动化执行
│   │   └── template_matcher.py # 模板匹配
│   ├── 🎮 core/               # 游戏逻辑
│   │   ├── controller.py      # 主控制器
│   │   └── task_manager.py    # 任务管理
│   ├── 💻 cli/                # 命令行界面
│   │   └── game_cli.py        # 交互式CLI
│   ├── 🎯 controllers/        # 游戏控制器
│   │   └── game_assistant.py  # 游戏助手
│   └── 🔨 utils/              # 工具函数
│       ├── config.py          # 配置管理
│       ├── logger.py          # 日志系统
│       └── screenshot.py      # 截图管理
├── 📋 config.yaml             # 主配置文件
├── 🎯 prompts.yaml            # 提示词配置
├── 📁 resources/              # 资源文件
│   ├── templates/             # 模板图片
│   └── screenshots/           # 截图存储
├── 🛠️ tools/                  # 开发工具
│   ├── template_maker.py      # 模板制作
│   ├── config_editor.py       # 配置编辑
│   └── analyze_logs.py        # 日志分析
├── 📝 logs/                   # 日志文件
└── 📖 docs/                   # 文档目录
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- macOS (推荐) 或 Linux
- iPad 设备 (iOS 14+)
- USB 数据线
- Ollama (本地视觉模型)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd sgzAss
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装 Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # 启动 Ollama 服务
   ollama serve
   
   # 安装视觉模型
   ollama pull llava:13b
   ```

4. **配置设备**
   - 连接 iPad 到电脑 USB 端口
   - 在 iPad 上信任此电脑
   - 确保 iPad 已安装三国志战略版

5. **配置系统**
   ```bash
   # 编辑配置文件
   cp config.yaml.example config.yaml
   # 根据需要修改配置
   ```

### 运行程序

```bash
# 启动游戏助手
python run_game_assistant.py

# 或使用交互式CLI
python -m src.cli.game_cli
```

## 🎮 使用指南

### 基本操作

1. **连接设备**: 程序启动后会自动检测并连接 iPad
2. **截图分析**: 实时获取游戏画面并进行智能分析
3. **操作建议**: 根据当前游戏状态提供最优操作建议
4. **自动执行**: 可选择自动执行推荐的操作

### CLI 命令

- `1` - 单次分析当前游戏画面
- `2` - 执行推荐的操作
- `3` - 查找特定游戏元素
- `4` - 查看系统统计信息
- `5` - 优化系统性能
- `6` - 启动持续运行模式
- `7` - 查看系统配置
- `8` - 设置日志等级
- `9` - 显示帮助信息
- `0` - 退出程序

### 配置说明

主要配置项在 `config.yaml` 中：

```yaml
# 设备连接
device:
  connection_timeout: 30
  retry_attempts: 3

# 视觉识别
vlm:
  model: "llava:13b"
  base_url: "http://localhost:11434"
  timeout: 30

# 自动化设置
automation:
  auto_execute: false
  execution_delay: 1.0
  safety_checks: true

# 日志配置
logging:
  level: "DEBUG"
  console_level: "INFO"
  file_path: "logs/ipad_automation.log"
```

## 🛠️ 开发工具

### 模板制作
```bash
# 制作游戏界面模板
python tools/template_maker.py
```

### 配置编辑
```bash
# 图形化配置编辑器
python tools/config_editor.py
```

### 日志分析
```bash
# 分析系统日志
python tools/analyze_logs.py
```

## 📊 性能优化

- **截图缓存**: 避免重复截图，提升响应速度
- **模板匹配**: 高效的图像识别算法
- **异步处理**: 并行处理多个任务
- **智能重试**: 自动恢复连接和操作失败

## 🔧 故障排除

### 常见问题

1. **设备连接失败**
   - 检查 USB 连接
   - 确认 iPad 已信任电脑
   - 重启 tunneld 服务

2. **视觉识别错误**
   - 检查 Ollama 服务状态
   - 确认模型已正确安装
   - 调整识别参数

3. **操作执行失败**
   - 检查游戏界面状态
   - 调整执行延迟
   - 启用安全检查

### 日志查看

```bash
# 查看实时日志
tail -f logs/ipad_automation.log

# 分析错误日志
python tools/analyze_logs.py --errors
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

本工具仅供学习和研究使用，请遵守游戏服务条款和相关法律法规。使用本工具产生的任何后果由用户自行承担。

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 加入讨论群

---

**享受智能化的游戏体验！** 🎮✨