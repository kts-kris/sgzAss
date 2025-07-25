#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
环境变量配置生成工具

用于生成.env文件，配置环境变量。
"""

import os
import sys
from pathlib import Path

# 确保可以导入项目模块
sys.path.append(str(Path(__file__).parent.parent.absolute()))

# 项目根目录
BASE_DIR = Path(__file__).parent.parent.absolute()

# 环境变量文件路径
ENV_FILE = os.path.join(BASE_DIR, ".env")

# 默认环境变量
DEFAULT_ENV = {
    "CONNECTION_TYPE": "network",  # 连接方式：usb, network, simulation
    "DEVICE_IP": "",  # 设备IP地址
    "DEVICE_PORT": "5555",  # 设备端口
    "SCREEN_WIDTH": "2732",  # 屏幕宽度
    "SCREEN_HEIGHT": "2048",  # 屏幕高度
    "LOG_LEVEL": "INFO",  # 日志级别：DEBUG, INFO, WARNING, ERROR
}


def read_env_file():
    """读取现有的.env文件
    
    Returns:
        dict: 环境变量字典
    """
    env_vars = {}
    
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars


def write_env_file(env_vars):
    """写入.env文件
    
    Args:
        env_vars: 环境变量字典
    """
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write("# 三国志战略版自动化助手环境变量配置\n")
        f.write("# 此文件由 tools/generate_env.py 生成\n\n")
        
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


def interactive_config():
    """交互式配置环境变量"""
    print("欢迎使用环境变量配置工具！")
    print("此工具将帮助您配置三国志战略版自动化助手的环境变量。")
    print("按回车键使用默认值或当前值。\n")
    
    # 读取现有配置
    current_env = read_env_file()
    
    # 合并默认配置和现有配置
    env_vars = DEFAULT_ENV.copy()
    env_vars.update(current_env)
    
    # 交互式配置
    print("设备连接配置:")
    connection_type = input(f"连接方式 [usb/network/simulation] (当前: {env_vars['CONNECTION_TYPE']}): ").strip()
    if connection_type:
        if connection_type.lower() in ["usb", "network", "simulation"]:
            env_vars["CONNECTION_TYPE"] = connection_type.lower()
        else:
            print(f"无效的连接方式: {connection_type}，将使用当前值: {env_vars['CONNECTION_TYPE']}")
    
    if env_vars["CONNECTION_TYPE"] == "network":
        device_ip = input(f"设备IP地址 (当前: {env_vars['DEVICE_IP'] or '未设置'}): ").strip()
        if device_ip:
            env_vars["DEVICE_IP"] = device_ip
        
        device_port = input(f"设备端口 (当前: {env_vars['DEVICE_PORT']}): ").strip()
        if device_port and device_port.isdigit():
            env_vars["DEVICE_PORT"] = device_port
    
    print("\n屏幕分辨率配置:")
    screen_width = input(f"屏幕宽度 (当前: {env_vars['SCREEN_WIDTH']}): ").strip()
    if screen_width and screen_width.isdigit():
        env_vars["SCREEN_WIDTH"] = screen_width
    
    screen_height = input(f"屏幕高度 (当前: {env_vars['SCREEN_HEIGHT']}): ").strip()
    if screen_height and screen_height.isdigit():
        env_vars["SCREEN_HEIGHT"] = screen_height
    
    print("\n日志配置:")
    log_level = input(f"日志级别 [DEBUG/INFO/WARNING/ERROR] (当前: {env_vars['LOG_LEVEL']}): ").strip()
    if log_level and log_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        env_vars["LOG_LEVEL"] = log_level.upper()
    
    # 写入配置
    write_env_file(env_vars)
    print(f"\n环境变量配置已保存到: {ENV_FILE}")


def main():
    """主函数"""
    interactive_config()


if __name__ == "__main__":
    main()