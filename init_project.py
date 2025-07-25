#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目初始化脚本

用于创建必要的目录结构和空文件，确保项目可以正常运行。
"""

import os
import sys
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.absolute()

# 需要创建的目录
DIRECTORIES = [
    "core",
    "utils",
    "tasks",
    "resources/templates",
    "resources/screenshots",
    "logs",
    "client",
    "tools",
]

# 需要创建的空文件（用于包导入）
EMPTY_FILES = [
    "core/__init__.py",
    "utils/__init__.py",
    "tasks/__init__.py",
    "resources/__init__.py",
]


def create_directories():
    """创建目录结构"""
    print("创建目录结构...")
    
    for directory in DIRECTORIES:
        dir_path = os.path.join(BASE_DIR, directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"  创建目录: {directory}")


def create_empty_files():
    """创建空文件"""
    print("创建空文件...")
    
    for file in EMPTY_FILES:
        file_path = os.path.join(BASE_DIR, file)
        
        # 如果文件不存在，创建空文件
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                pass
            print(f"  创建文件: {file}")


def main():
    """主函数"""
    print(f"初始化项目: {BASE_DIR}")
    
    # 创建目录结构
    create_directories()
    
    # 创建空文件
    create_empty_files()
    
    print("项目初始化完成！")
    print("\n接下来的步骤:")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 运行模板采集工具: python tools/template_collector.py")
    print("3. 运行主程序: python main.py")


if __name__ == "__main__":
    main()