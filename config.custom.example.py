#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""自定义配置示例

此文件展示了如何创建自定义配置来覆盖默认设置，包括新增的日志分析功能。
复制此文件为 config.custom.py 并根据需要修改配置项。
只需要包含您想要覆盖的配置项，不需要包含所有设置。
自定义配置示例

此文件展示了如何创建自定义配置来覆盖默认设置。
复制此文件为 config.custom.py 并根据需要修改配置项。
只需要包含您想要覆盖的配置项，不需要包含所有设置。
"""

# 游戏设置 - 覆盖部分配置
GAME_SETTINGS = {
    # 提高匹配阈值，使识别更精确
    "match_threshold": 0.85,
    
    # 增加操作延迟，使操作更像人类
    "action_delay_min": 0.8,
    "action_delay_max": 2.0,
}

# 设备连接设置 - 使用USB连接
DEVICE_SETTINGS = {
    "connection_type": "usb",
}

# 任务设置 - 自定义任务参数
TASK_SETTINGS = {
    # 只修改土地占领任务
    "land_occupation": {
        # 增加目标占领数量
        "target_count": 20,
        # 减小搜索距离
        "max_distance": 300,
    },
    
    # 禁用资源收集任务
    "resource_collection": {
        "enabled": False,
    },
}

# 自定义日志设置
LOG_SETTINGS = {
    # 使用调试级别的日志
    "level": "DEBUG",
    
    # 启用日志分析功能
    "analysis": {
        "enabled": True,
        # 自动分析间隔（秒）
        "interval": 3600,  # 每小时分析一次
        # 是否自动应用优化建议
        "auto_optimize": False,
        # 是否生成性能报告
        "generate_report": True,
        # 是否生成可视化图表
        "visualize": True,
        # 分析结果存储目录（相对于日志目录）
        "results_dir": "analysis",
    }
}