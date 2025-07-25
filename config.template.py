#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件模板：用于创建自定义配置

复制此文件为 config.custom.py 并根据需要修改配置项。
自定义配置文件不会被版本控制系统跟踪，可以安全地存储个人设置。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.absolute()

# 资源目录
RESOURCE_DIR = os.path.join(BASE_DIR, "resources")
TEMPLATE_DIR = os.path.join(RESOURCE_DIR, "templates")
SCREENSHOT_DIR = os.path.join(RESOURCE_DIR, "screenshots")

# 确保目录存在
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 游戏设置
GAME_SETTINGS = {
    # 匹配阈值：图像识别的匹配度阈值，值越高要求越精确
    "match_threshold": 0.8,
    
    # 操作延迟：模拟人类操作的随机延迟范围（秒）
    "action_delay_min": 0.5,
    "action_delay_max": 1.5,
    
    # 截图间隔：连续截图的时间间隔（秒）
    "screenshot_interval": 1.0,
    
    # 重试设置
    "max_retries": 3,
    "retry_delay": 2.0,
    
    # 安全设置
    "enable_safe_mode": True,  # 安全模式：启用额外的检查和确认
    "max_continuous_actions": 50,  # 最大连续操作次数，超过后暂停
    "pause_duration": 30,  # 暂停时长（秒）
}

# 设备连接设置
DEVICE_SETTINGS = {
    # iPad连接方式：'usb'、'network'或'simulation'
    "connection_type": os.getenv("CONNECTION_TYPE", "network"),
    
    # 网络连接设置（当connection_type为'network'时使用）
    "device_ip": os.getenv("DEVICE_IP", ""),
    "device_port": int(os.getenv("DEVICE_PORT", "5555")),
    
    # 屏幕分辨率
    "screen_width": int(os.getenv("SCREEN_WIDTH", "2732")),  # iPad Pro 默认宽度
    "screen_height": int(os.getenv("SCREEN_HEIGHT", "2048")),  # iPad Pro 默认高度
}

# 日志设置
LOG_SETTINGS = {
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "log_file": os.path.join(BASE_DIR, "logs", "sgz_assistant.log"),
    "rotation": "500 MB",  # 日志文件大小达到500MB时轮转
}

# 确保日志目录存在
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# 游戏元素模板配置
# 这些是需要识别的游戏UI元素及其对应的模板图像文件名
GAME_TEMPLATES = {
    # 主界面元素
    "main_menu": "main_menu.png",
    "world_map": "world_map.png",
    
    # 地图操作元素
    "empty_land": "empty_land.png",
    "occupied_land": "occupied_land.png",
    "enemy_land": "enemy_land.png",
    "ally_land": "ally_land.png",
    "resource_point": "resource_point.png",
    
    # 部队操作元素
    "army_idle": "army_idle.png",
    "army_marching": "army_marching.png",
    "army_select": "army_select.png",
    "army_attack": "army_attack.png",
    "army_occupy": "army_occupy.png",
    
    # 按钮和交互元素
    "confirm_button": "confirm_button.png",
    "cancel_button": "cancel_button.png",
    "close_button": "close_button.png",
    "back_button": "back_button.png",
}

# 自动化任务配置
TASK_SETTINGS = {
    # 土地占领任务
    "land_occupation": {
        "enabled": True,
        "target_count": 10,  # 目标占领数量
        "prefer_resources": True,  # 优先占领资源点
        "max_distance": 500,  # 最大搜索距离（像素）
    },
    
    # 部队移动任务
    "army_movement": {
        "enabled": True,
        "idle_army_check_interval": 300,  # 检查空闲部队的间隔（秒）
        "movement_strategy": "nearest",  # 移动策略：nearest, resources, enemy
    },
    
    # 资源收集任务
    "resource_collection": {
        "enabled": True,
        "collection_interval": 3600,  # 收集间隔（秒）
    },
}