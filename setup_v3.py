#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
《三国志战略版》游戏助手 v3.0 安装设置脚本

自动检查和配置运行环境，包括Ollama安装、依赖检查等。
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple


class SetupManager:
    """安装设置管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.config_file = self.project_root / "config.yaml"
        
    def run_setup(self):
        """运行完整的设置流程"""
        print("🎮 《三国志战略版》游戏助手 v3.0 设置向导")
        print("=" * 60)
        
        try:
            # 1. 检查Python版本
            self._check_python_version()
            
            # 2. 安装Python依赖
            self._install_python_dependencies()
            
            # 3. 检查Ollama安装
            self._check_ollama_installation()
            
            # 4. 配置Ollama模型
            self._setup_ollama_models()
            
            # 5. 验证配置文件
            self._validate_config()
            
            # 6. 创建必要目录
            self._create_directories()
            
            # 7. 运行系统测试
            self._run_system_tests()
            
            print("\n✅ 设置完成！")
            print("\n🚀 现在可以运行游戏助手:")
            print("   python run_game_assistant.py")
            
        except Exception as e:
            print(f"\n❌ 设置失败: {e}")
            print("\n💡 请查看错误信息并手动解决问题")
            sys.exit(1)
    
    def _check_python_version(self):
        """检查Python版本"""
        print("\n1️⃣ 检查Python版本...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            raise RuntimeError(f"需要Python 3.8+，当前版本: {version.major}.{version.minor}")
        
        print(f"   ✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    
    def _install_python_dependencies(self):
        """安装Python依赖"""
        print("\n2️⃣ 安装Python依赖...")
        
        if not self.requirements_file.exists():
            raise FileNotFoundError("requirements.txt文件不存在")
        
        try:
            # 升级pip
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # 安装依赖
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)],
                check=True, capture_output=True, text=True
            )
            
            print("   ✅ Python依赖安装完成")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 依赖安装失败: {e.stderr}")
            raise
    
    def _check_ollama_installation(self):
        """检查Ollama安装"""
        print("\n3️⃣ 检查Ollama安装...")
        
        # 检查ollama命令是否可用
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True, check=True)
            print(f"   ✅ Ollama已安装: {result.stdout.strip()}")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   ❌ Ollama未安装")
            print("\n💡 请按照以下步骤安装Ollama:")
            
            if sys.platform == "darwin":  # macOS
                print("   macOS: 访问 https://ollama.ai 下载安装包")
                print("   或使用Homebrew: brew install ollama")
            elif sys.platform == "linux":
                print("   Linux: curl -fsSL https://ollama.ai/install.sh | sh")
            elif sys.platform == "win32":
                print("   Windows: 访问 https://ollama.ai 下载安装包")
            
            raise RuntimeError("请先安装Ollama")
        
        # 检查Ollama服务是否运行
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("   ✅ Ollama服务正在运行")
            else:
                print("   ⚠️ Ollama服务响应异常")
        except requests.RequestException:
            print("   ⚠️ Ollama服务未运行，请启动: ollama serve")
    
    def _setup_ollama_models(self):
        """设置Ollama模型"""
        print("\n4️⃣ 配置Ollama模型...")
        
        # 检查已安装的模型
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                print(f"   📋 已安装模型: {len(model_names)}个")
                for name in model_names:
                    print(f"      - {name}")
                
                # 检查是否有视觉模型
                vision_models = [name for name in model_names if "llava" in name.lower()]
                
                if vision_models:
                    print(f"   ✅ 找到视觉模型: {vision_models[0]}")
                else:
                    print("   ⚠️ 未找到视觉模型")
                    print("   💡 建议安装llava模型: ollama pull llava:latest")
                    
                    # 询问是否自动安装
                    install = input("   🤔 是否现在安装llava模型? (y/n): ").strip().lower()
                    if install in ['y', 'yes']:
                        self._install_ollama_model("llava:latest")
            
        except requests.RequestException as e:
            print(f"   ❌ 无法连接Ollama服务: {e}")
            print("   💡 请确保Ollama服务正在运行: ollama serve")
    
    def _install_ollama_model(self, model_name: str):
        """安装Ollama模型"""
        print(f"   📥 正在安装模型: {model_name}")
        print("   ⏳ 这可能需要几分钟时间...")
        
        try:
            result = subprocess.run(
                ["ollama", "pull", model_name],
                check=True, capture_output=True, text=True
            )
            print(f"   ✅ 模型安装完成: {model_name}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 模型安装失败: {e.stderr}")
            print("   💡 请手动安装: ollama pull llava:latest")
    
    def _validate_config(self):
        """验证配置文件"""
        print("\n5️⃣ 验证配置文件...")
        
        if not self.config_file.exists():
            print("   ❌ config.yaml文件不存在")
            raise FileNotFoundError("配置文件不存在")
        
        try:
            import yaml
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查关键配置项
            required_sections = ['vision', 'async_analysis', 'logging']
            for section in required_sections:
                if section not in config:
                    raise ValueError(f"配置文件缺少 {section} 部分")
            
            # 检查Ollama配置
            if 'ollama_config' in config.get('vision', {}):
                ollama_config = config['vision']['ollama_config']
                print(f"   📋 Ollama配置: {ollama_config.get('host')}:{ollama_config.get('port')}")
                print(f"   🤖 默认模型: {ollama_config.get('model')}")
            
            print("   ✅ 配置文件验证通过")
            
        except Exception as e:
            print(f"   ❌ 配置文件验证失败: {e}")
            raise
    
    def _create_directories(self):
        """创建必要目录"""
        print("\n6️⃣ 创建必要目录...")
        
        directories = [
            "resources/templates",
            "resources/screenshots", 
            "logs",
            "data",
            "temp"
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"   📁 {dir_path}")
        
        print("   ✅ 目录创建完成")
    
    def _run_system_tests(self):
        """运行系统测试"""
        print("\n7️⃣ 运行系统测试...")
        
        tests = [
            ("导入核心模块", self._test_imports),
            ("配置加载", self._test_config_loading),
            ("Ollama连接", self._test_ollama_connection),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
                print(f"   ✅ {test_name}")
            except Exception as e:
                print(f"   ❌ {test_name}: {e}")
                raise
        
        print("   ✅ 系统测试通过")
    
    def _test_imports(self):
        """测试模块导入"""
        try:
            from src.controllers.game_assistant import GameAssistant
            from src.services.ollama_vlm import OllamaVLMService
            from src.services.async_analysis_manager import AsyncAnalysisManager
        except ImportError as e:
            raise ImportError(f"模块导入失败: {e}")
    
    def _test_config_loading(self):
        """测试配置加载"""
        try:
            from src.utils.config import get_config
            config = get_config()
            if not config:
                raise ValueError("配置加载失败")
        except Exception as e:
            raise Exception(f"配置加载测试失败: {e}")
    
    def _test_ollama_connection(self):
        """测试Ollama连接"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama服务响应错误: {response.status_code}")
        except requests.RequestException as e:
            raise ConnectionError(f"无法连接Ollama服务: {e}")


def main():
    """主函数"""
    setup_manager = SetupManager()
    setup_manager.run_setup()


if __name__ == "__main__":
    main()