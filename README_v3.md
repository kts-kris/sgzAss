# 《三国志战略版》游戏助手 v3.0

🎮 **全新升级！** 支持本地Ollama VLM、异步分析和智能提示词优化

## ✨ v3.0 新功能

### 🤖 本地Ollama VLM支持
- **完全本地化**: 无需依赖外部API，保护隐私
- **高性能**: 支持llava等先进视觉语言模型
- **实时分析**: 快速识别游戏界面元素和状态
- **智能建议**: 基于屏幕内容生成操作建议

### ⚡ 异步分析系统
- **并发处理**: 支持多任务同时分析
- **实时输出**: 分析结果即时显示
- **历史记录**: 保存分析历史供参考
- **性能监控**: 实时统计分析效率

### 🧠 智能提示词优化
- **自动学习**: 根据历史结果优化提示词
- **动态调整**: 实时改进分析准确性
- **个性化**: 适应不同用户的使用习惯
- **效果追踪**: 监控优化效果

## 🚀 快速开始

### 1. 环境准备

#### 安装Ollama
```bash
# macOS
brew install ollama
# 或访问 https://ollama.ai 下载安装包

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# 访问 https://ollama.ai 下载安装包
```

#### 启动Ollama服务
```bash
ollama serve
```

#### 安装视觉模型
```bash
# 推荐使用llava模型
ollama pull llava:latest

# 或其他视觉模型
ollama pull llava:13b
ollama pull bakllava:latest
```

### 2. 项目设置

#### 自动设置（推荐）
```bash
# 运行自动设置脚本
python setup_v3.py
```

#### 手动设置
```bash
# 1. 安装Python依赖
pip install -r requirements.txt

# 2. 检查配置文件
# 确保config.yaml中的ollama_config配置正确

# 3. 创建必要目录
mkdir -p resources/templates resources/screenshots logs data temp
```

### 3. 启动游戏助手

```bash
# 使用启动脚本（推荐）
python run_game_assistant.py

# 或直接运行CLI
python -m src.cli.game_cli
```

## 📋 功能详解

### 命令行界面

启动后，您可以使用以下命令：

- `analyze` - 分析当前屏幕
- `suggest` - 获取操作建议
- `find <元素名称>` - 查找特定游戏元素
- `auto start` - 开始自动分析
- `auto stop` - 停止自动分析
- `stats` - 查看分析统计
- `optimize` - 优化提示词
- `config` - 查看当前配置
- `help` - 显示帮助信息
- `quit` - 退出程序

### 配置说明

#### Ollama配置 (`config.yaml`)
```yaml
vision:
  ollama_config:
    host: "localhost"          # Ollama服务地址
    port: 11434               # Ollama服务端口
    model: "llava:latest"     # 使用的视觉模型
    timeout: 30               # 请求超时时间
    max_retries: 3            # 最大重试次数
    image_max_size: 1024      # 图片最大尺寸
    image_quality: 85         # 图片质量
```

#### 异步分析配置
```yaml
async_analysis:
  enabled: true               # 启用异步分析
  max_concurrent_tasks: 3     # 最大并发任务数
  history_limit: 100          # 历史记录限制
  auto_analysis:
    enabled: false            # 自动分析
    interval: 5               # 分析间隔（秒）
    priority: "medium"        # 任务优先级
  prompt_optimization:
    enabled: true             # 启用提示词优化
    min_history_count: 10     # 最少历史记录数
    optimization_interval: 50 # 优化间隔
    auto_optimize: true       # 自动优化
```

## 🔧 高级功能

### 自定义提示词

您可以通过修改配置或代码来自定义分析提示词：

```python
# 在 src/services/ollama_vlm.py 中
def _generate_optimized_prompt(self, task_type: str, context: Dict) -> str:
    # 自定义您的提示词逻辑
    pass
```

### 扩展分析功能

```python
# 继承 AsyncAnalysisManager 添加自定义分析
class CustomAnalysisManager(AsyncAnalysisManager):
    async def custom_analysis(self, image_data: bytes) -> Dict:
        # 您的自定义分析逻辑
        pass
```

### 集成到其他项目

```python
from src.controllers.game_assistant import GameAssistant

# 创建游戏助手实例
assistant = GameAssistant()

# 启动服务
await assistant.start()

# 分析屏幕
result = await assistant.analyze_current_screen()

# 获取操作建议
suggestions = await assistant.get_action_suggestions()
```

## 📊 性能优化

### 模型选择建议

| 模型 | 大小 | 速度 | 准确性 | 推荐场景 |
|------|------|------|--------|----------|
| llava:7b | 4.5GB | 快 | 良好 | 日常使用 |
| llava:13b | 7.3GB | 中等 | 优秀 | 高精度需求 |
| llava:34b | 19GB | 慢 | 极佳 | 专业分析 |

### 性能调优

1. **并发任务数**: 根据硬件性能调整 `max_concurrent_tasks`
2. **图片质量**: 平衡 `image_quality` 和处理速度
3. **历史记录**: 适当设置 `history_limit` 避免内存占用过高
4. **模型缓存**: Ollama会自动缓存模型，首次加载较慢

## 🐛 故障排除

### 常见问题

#### 1. Ollama连接失败
```bash
# 检查Ollama服务状态
curl http://localhost:11434/api/tags

# 重启Ollama服务
ollama serve
```

#### 2. 模型加载失败
```bash
# 检查已安装模型
ollama list

# 重新拉取模型
ollama pull llava:latest
```

#### 3. iPad连接问题
```bash
# 检查设备连接
idevice_id -l

# 重启WDA服务
# 在Xcode中重新运行WebDriverAgent
```

#### 4. 依赖安装问题
```bash
# 升级pip
pip install --upgrade pip

# 清理缓存重新安装
pip cache purge
pip install -r requirements.txt --force-reinstall
```

### 日志分析

日志文件位置：`logs/game_assistant.log`

```bash
# 查看最新日志
tail -f logs/game_assistant.log

# 搜索错误信息
grep "ERROR" logs/game_assistant.log
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd sgzAss

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果有的话

# 运行测试
python -m pytest tests/
```

### 代码规范

- 使用Python 3.8+
- 遵循PEP 8代码风格
- 添加类型注解
- 编写单元测试
- 更新文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Ollama](https://ollama.ai) - 提供优秀的本地LLM运行环境
- [LLaVA](https://llava-vl.github.io/) - 强大的视觉语言模型
- [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) - iOS设备通信
- [facebook-wda](https://github.com/openatx/facebook-wda) - WebDriverAgent客户端

---

**🎮 祝您游戏愉快！如有问题，请提交Issue或联系开发者。**