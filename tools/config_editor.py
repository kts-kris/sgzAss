#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置编辑工具

提供一种优雅的方式来编辑项目配置，支持命令行参数和交互式界面。
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

# 确保可以导入项目模块
sys.path.append(str(Path(__file__).parent.parent.absolute()))

# 导入配置模块
import config


class ConfigEditor:
    """配置编辑工具类"""
    
    def __init__(self):
        """初始化配置编辑器"""
        self.config_file = os.path.join(Path(__file__).parent.parent, "config.py")
        self.env_file = os.path.join(Path(__file__).parent.parent, ".env")
        
        # 读取当前配置
        self.current_config = self._read_current_config()
        
        # 读取当前环境变量
        self.current_env = self._read_env_file()
    
    def _read_current_config(self) -> Dict[str, Any]:
        """读取当前配置
        
        Returns:
            Dict[str, Any]: 当前配置的字典表示
        """
        return {
            "GAME_SETTINGS": config.GAME_SETTINGS,
            "DEVICE_SETTINGS": config.DEVICE_SETTINGS,
            "LOG_SETTINGS": config.LOG_SETTINGS,
            "TASK_SETTINGS": config.TASK_SETTINGS,
        }
    
    def _read_env_file(self) -> Dict[str, str]:
        """读取.env文件
        
        Returns:
            Dict[str, str]: 环境变量字典
        """
        env_vars = {}
        
        if os.path.exists(self.env_file):
            with open(self.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        
        return env_vars
    
    def _write_env_file(self, env_vars: Dict[str, str]) -> None:
        """写入.env文件
        
        Args:
            env_vars: 环境变量字典
        """
        with open(self.env_file, "w", encoding="utf-8") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
    
    def _update_config_in_file(self, section: str, key: str, value: Any) -> bool:
        """在配置文件中更新特定配置项
        
        Args:
            section: 配置部分（如GAME_SETTINGS）
            key: 配置键
            value: 新值
            
        Returns:
            bool: 是否成功更新
        """
        # 读取配置文件内容
        with open(self.config_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 构建正则表达式模式
        if isinstance(value, str):
            # 字符串值需要加引号
            value_str = f'"{value}"'
        elif isinstance(value, bool):
            # 布尔值转为True/False
            value_str = str(value)
        else:
            # 其他类型直接转字符串
            value_str = str(value)
        
        # 尝试匹配并替换简单键值对
        pattern = fr'("{key}"\s*:\s*)[^,}}]+'
        if section == "DEVICE_SETTINGS" and key in ["device_ip", "device_port", "screen_width", "screen_height"]:
            # 环境变量配置项有特殊格式，不直接修改
            return False
        
        # 在指定部分中查找并替换
        section_start = content.find(f"{section} = {")
        if section_start == -1:
            return False
        
        section_end = content.find("}", section_start)
        if section_end == -1:
            return False
        
        section_content = content[section_start:section_end+1]
        
        # 在部分内容中查找键
        match = re.search(pattern, section_content)
        if not match:
            return False
        
        # 替换值
        new_section_content = re.sub(pattern, f'\g<1>{value_str}', section_content)
        new_content = content.replace(section_content, new_section_content)
        
        # 写回文件
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        return True
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """更新配置
        
        Args:
            section: 配置部分（如GAME_SETTINGS）
            key: 配置键
            value: 新值
            
        Returns:
            bool: 是否成功更新
        """
        # 检查部分是否存在
        if section not in self.current_config:
            print(f"错误：配置部分 '{section}' 不存在")
            return False
        
        # 检查键是否存在
        if key not in self.current_config[section]:
            print(f"错误：配置键 '{key}' 在 '{section}' 中不存在")
            return False
        
        # 检查值类型
        current_value = self.current_config[section][key]
        try:
            # 尝试转换类型
            if isinstance(current_value, bool):
                if isinstance(value, str):
                    if value.lower() in ["true", "yes", "1"]:
                        value = True
                    elif value.lower() in ["false", "no", "0"]:
                        value = False
                    else:
                        raise ValueError(f"无法将 '{value}' 转换为布尔值")
            elif isinstance(current_value, int):
                value = int(value)
            elif isinstance(current_value, float):
                value = float(value)
        except ValueError as e:
            print(f"错误：{e}")
            return False
        
        # 更新内存中的配置
        self.current_config[section][key] = value
        
        # 特殊处理：如果是DEVICE_SETTINGS中的某些键，更新环境变量
        if section == "DEVICE_SETTINGS":
            if key == "connection_type":
                self.current_env["CONNECTION_TYPE"] = value
            elif key == "device_ip":
                self.current_env["DEVICE_IP"] = value
            elif key == "device_port":
                self.current_env["DEVICE_PORT"] = str(value)
            elif key == "screen_width":
                self.current_env["SCREEN_WIDTH"] = str(value)
            elif key == "screen_height":
                self.current_env["SCREEN_HEIGHT"] = str(value)
            
            # 写入环境变量文件
            self._write_env_file(self.current_env)
        
        # 更新配置文件
        return self._update_config_in_file(section, key, value)
    
    def list_config(self, section: Optional[str] = None) -> None:
        """列出当前配置
        
        Args:
            section: 可选，指定要列出的配置部分
        """
        if section:
            if section not in self.current_config:
                print(f"错误：配置部分 '{section}' 不存在")
                return
            
            print(f"\n{section}:")
            for key, value in self.current_config[section].items():
                print(f"  {key}: {value}")
        else:
            for section, config in self.current_config.items():
                print(f"\n{section}:")
                for key, value in config.items():
                    print(f"  {key}: {value}")
    
    def interactive_mode(self) -> None:
        """交互式编辑模式"""
        print("欢迎使用配置编辑工具！")
        print("输入 'help' 查看帮助，输入 'exit' 退出。")
        
        while True:
            command = input("\n> ").strip()
            
            if command.lower() in ["exit", "quit", "q"]:
                break
            elif command.lower() in ["help", "h", "?"]:
                self._print_help()
            elif command.lower() in ["list", "ls", "l"]:
                self.list_config()
            elif command.lower().startswith("list "):
                section = command[5:].strip()
                self.list_config(section)
            elif command.lower().startswith("set "):
                # 解析设置命令：set SECTION.KEY=VALUE
                try:
                    parts = command[4:].strip().split("=", 1)
                    if len(parts) != 2:
                        print("错误：格式应为 'set SECTION.KEY=VALUE'")
                        continue
                    
                    path, value = parts
                    path_parts = path.strip().split(".")
                    
                    if len(path_parts) != 2:
                        print("错误：路径应为 'SECTION.KEY'")
                        continue
                    
                    section, key = path_parts
                    success = self.update_config(section, key, value.strip())
                    
                    if success:
                        print(f"已更新 {section}.{key} = {value.strip()}")
                    else:
                        print(f"更新 {section}.{key} 失败")
                
                except Exception as e:
                    print(f"错误：{e}")
            else:
                print(f"未知命令：{command}")
                print("输入 'help' 查看帮助。")
    
    def _print_help(self) -> None:
        """打印帮助信息"""
        print("\n配置编辑工具帮助：")
        print("  help, h, ?       - 显示此帮助信息")
        print("  list, ls, l      - 列出所有配置")
        print("  list SECTION     - 列出指定部分的配置")
        print("  set SECTION.KEY=VALUE - 设置配置值")
        print("  exit, quit, q    - 退出程序")
        print("\n示例：")
        print("  set GAME_SETTINGS.match_threshold=0.85")
        print("  set DEVICE_SETTINGS.connection_type=usb")
        print("  set TASK_SETTINGS.land_occupation.enabled=false")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="三国志战略版自动化助手配置编辑工具")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # list命令
    list_parser = subparsers.add_parser("list", help="列出配置")
    list_parser.add_argument("section", nargs="?", help="配置部分")
    
    # set命令
    set_parser = subparsers.add_parser("set", help="设置配置")
    set_parser.add_argument("path", help="配置路径，格式为SECTION.KEY")
    set_parser.add_argument("value", help="配置值")
    
    # 交互模式
    parser.add_argument("--interactive", "-i", action="store_true", help="启用交互模式")
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    editor = ConfigEditor()
    
    if args.interactive:
        editor.interactive_mode()
    elif args.command == "list":
        editor.list_config(args.section)
    elif args.command == "set":
        try:
            section, key = args.path.split(".")
            success = editor.update_config(section, key, args.value)
            
            if success:
                print(f"已更新 {section}.{key} = {args.value}")
            else:
                print(f"更新 {section}.{key} 失败")
        
        except ValueError:
            print("错误：路径格式应为 'SECTION.KEY'")
    else:
        # 如果没有提供命令，默认进入交互模式
        editor.interactive_mode()


if __name__ == "__main__":
    main()