# 三国志战略版自动化助手

这个项目旨在通过视觉识别技术，自动化完成《三国志战略版》中的重复性操作，提高游戏效率。

## 功能特点

- 自动识别游戏界面元素
- 自动执行占领土地操作
- 自动指挥队伍移动
- 智能判断游戏状态
- 安全机制确保游戏体验不受影响

## 技术栈

- Python 3.8+
- OpenCV (视觉识别)
- PyAutoGUI (屏幕操作)
- NumPy (数据处理)
- Pillow (图像处理)

## 安装说明

1. 确保已安装Python 3.8或更高版本
2. 安装所需依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

1. 初始化项目：

```bash
python init_project.py
```

2. 配置环境变量：

```bash
python tools/generate_env.py
```

3. 采集游戏界面模板：

```bash
python tools/template_collector.py
```

4. 在iPad上运行三国志战略版游戏
5. 确保iPad与电脑在同一网络下，或通过有线方式连接
6. 运行主程序：

```bash
python main.py
```

7. 根据提示进行操作

## 配置管理

本项目提供了多种配置管理方式，您可以根据需要选择最适合的方式：

### 1. 环境变量配置

使用环境变量配置基本连接参数：

```bash
python tools/generate_env.py
```

这将创建一个`.env`文件，包含设备连接、屏幕分辨率等基本设置。

### 2. 交互式配置编辑器

使用交互式配置编辑器修改任何配置项：

```bash
python tools/config_editor.py -i
```

或者使用命令行参数直接修改：

```bash
# 列出所有配置
python tools/config_editor.py list

# 列出特定部分的配置
python tools/config_editor.py list GAME_SETTINGS

# 修改配置项
python tools/config_editor.py set GAME_SETTINGS.match_threshold 0.85
```

### 3. 自定义配置文件

创建自定义配置文件以覆盖默认设置：

1. 复制模板文件：`cp config.template.py config.custom.py`
2. 编辑`config.custom.py`，只包含您想要修改的配置项
3. 系统将自动加载自定义配置并覆盖默认设置

## 注意事项

- 本工具仅用于减少重复性操作，提高游戏体验
- 使用本工具时，请确保不违反游戏用户协议
- 建议在非高峰期使用，以避免影响游戏服务器
- 首次使用前，请确保完成模板采集，以提高识别准确率

## 免责声明

本项目仅供学习和研究目的使用。使用者应自行承担使用本工具的风险和责任。开发者不对因使用本工具而导致的任何问题负责。