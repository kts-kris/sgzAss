#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件：存储项目的全局配置和参数

此文件定义了默认配置。如果存在 config.custom.py 文件，
将从该文件加载自定义配置来覆盖默认设置。
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
    # iPad连接方式：'usb'或'network'
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

# 加载自定义配置（如果存在）
CUSTOM_CONFIG_PATH = os.path.join(BASE_DIR, "config.custom.py")
if os.path.exists(CUSTOM_CONFIG_PATH):
    try:
        import importlib.util
        import sys
        
        # 动态加载自定义配置模块
        spec = importlib.util.spec_from_file_location("config_custom", CUSTOM_CONFIG_PATH)
        custom_config = importlib.util.module_from_spec(spec)
        sys.modules["config_custom"] = custom_config
        spec.loader.exec_module(custom_config)
        
        # 更新配置
        if hasattr(custom_config, "GAME_SETTINGS"):
            GAME_SETTINGS.update(custom_config.GAME_SETTINGS)
        
        if hasattr(custom_config, "DEVICE_SETTINGS"):
            DEVICE_SETTINGS.update(custom_config.DEVICE_SETTINGS)
        
        if hasattr(custom_config, "LOG_SETTINGS"):
            LOG_SETTINGS.update(custom_config.LOG_SETTINGS)
        
        if hasattr(custom_config, "TASK_SETTINGS"):
            # 递归更新嵌套字典
            def update_nested_dict(d, u):
                for k, v in u.items():
                    if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                        update_nested_dict(d[k], v)
                    else:
                        d[k] = v
            
            update_nested_dict(TASK_SETTINGS, custom_config.TASK_SETTINGS)
        
        if hasattr(custom_config, "GAME_TEMPLATES"):
            GAME_TEMPLATES.update(custom_config.GAME_TEMPLATES)
        
        print("已加载自定义配置：", CUSTOM_CONFIG_PATH)
    
    except Exception as e:
        print(f"加载自定义配置时出错：{e}")
        print("将使用默认配置")