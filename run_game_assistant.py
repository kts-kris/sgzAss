#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
《三国志战略版》游戏助手 v3.0 启动脚本

快速启动游戏助手，支持本地Ollama VLM和异步分析功能。
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.game_cli import main

if __name__ == "__main__":
    print("🎮 《三国志战略版》游戏助手 v3.0")
    print("=" * 50)
    print("✨ 新功能:")
    print("  🤖 本地Ollama VLM支持")
    print("  ⚡ 异步截图分析")
    print("  🧠 智能提示词优化")
    print("  📊 实时分析结果输出")
    print("=" * 50)
    print("\n🚀 正在启动...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n💡 故障排除建议:")
        print("  1. 确保已安装Ollama并启动服务")
        print("  2. 确保iPad已通过USB连接")
        print("  3. 检查config.yaml配置文件")
        print("  4. 运行 'pip install -r requirements.txt' 安装依赖")
        sys.exit(1)