#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置监控和自动调整模块

此模块负责监控配置文件的变化，并根据实际运行情况自动调整配置参数。
它可以跟踪配置参数的历史变化，评估每次变化对性能的影响，并推荐最优配置。
"""

import os
import json
import time
import importlib
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class ConfigMonitor:
    """配置监控和自动调整类"""
    
    def __init__(self, config_file: str, history_file: Optional[str] = None):
        """
        初始化配置监控器
        
        Args:
            config_file: 配置文件路径
            history_file: 配置历史记录文件路径，默认为config_history.json
        """
        self.config_file = config_file
        self.history_file = history_file or os.path.join(
            Path(config_file).parent, "config_history.json"
        )
        self.current_config = {}
        self.config_history = []
        self.performance_metrics = {}
        
        # 加载当前配置
        self._load_current_config()
        
        # 加载配置历史
        self._load_config_history()
    
    def _load_current_config(self) -> None:
        """
        加载当前配置文件
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        
        # 动态导入配置模块
        spec = importlib.util.spec_from_file_location("config_module", self.config_file)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        # 提取配置项
        self.current_config = {
            "GAME_SETTINGS": getattr(config_module, "GAME_SETTINGS", {}),
            "DEVICE_SETTINGS": getattr(config_module, "DEVICE_SETTINGS", {}),
            "LOG_SETTINGS": getattr(config_module, "LOG_SETTINGS", {}),
            "TASK_SETTINGS": getattr(config_module, "TASK_SETTINGS", {}),
        }
    
    def _load_config_history(self) -> None:
        """
        加载配置历史记录
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.config_history = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载配置历史记录失败: {e}")
                # 创建新的历史记录
                self.config_history = []
        
        # 如果历史记录为空，添加当前配置作为第一条记录
        if not self.config_history:
            self._add_config_to_history(self.current_config, "初始配置")
    
    def _add_config_to_history(self, config: Dict[str, Any], reason: str, 
                              performance: Optional[Dict[str, Any]] = None) -> None:
        """
        将配置添加到历史记录
        
        Args:
            config: 配置字典
            reason: 配置变更原因
            performance: 性能指标
        """
        # 创建配置记录
        config_record = {
            "timestamp": datetime.now().isoformat(),
            "config": config,
            "reason": reason,
            "performance": performance or {}
        }
        
        # 添加到历史记录
        self.config_history.append(config_record)
        
        # 保存历史记录
        self._save_config_history()
    
    def _save_config_history(self) -> None:
        """
        保存配置历史记录
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存配置历史记录失败: {e}")
    
    def update_config(self, new_config: Dict[str, Any], reason: str, 
                     performance: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新配置文件
        
        Args:
            new_config: 新配置字典
            reason: 配置变更原因
            performance: 性能指标
            
        Returns:
            bool: 是否成功更新
        """
        # 合并配置
        updated_config = self._merge_configs(self.current_config, new_config)
        
        # 生成配置文件内容
        config_content = self._generate_config_content(updated_config, reason)
        
        try:
            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # 更新当前配置
            self.current_config = updated_config
            
            # 添加到历史记录
            self._add_config_to_history(updated_config, reason, performance)
            
            return True
        except IOError as e:
            print(f"更新配置文件失败: {e}")
            return False
    
    def _merge_configs(self, base_config: Dict[str, Any], 
                      new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并配置字典
        
        Args:
            base_config: 基础配置
            new_config: 新配置
            
        Returns:
            Dict: 合并后的配置
        """
        result = base_config.copy()
        
        # 遍历新配置的每个部分
        for section, section_data in new_config.items():
            if section not in result:
                result[section] = section_data
            elif isinstance(section_data, dict) and isinstance(result[section], dict):
                # 递归合并字典
                for key, value in section_data.items():
                    result[section][key] = value
            else:
                # 直接替换
                result[section] = section_data
        
        return result
    
    def _generate_config_content(self, config: Dict[str, Any], reason: str) -> str:
        """
        生成配置文件内容
        
        Args:
            config: 配置字典
            reason: 配置变更原因
            
        Returns:
            str: 配置文件内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动生成的配置文件

生成时间: {timestamp}
变更原因: {reason}

此文件由配置监控器自动生成，包含基于性能分析的优化配置。
您可以手动修改此文件，但请注意自动优化可能会覆盖您的更改。
"""

# 游戏设置
GAME_SETTINGS = {
    # 添加游戏设置项
}

# 设备设置
DEVICE_SETTINGS = {
    # 添加设备设置项
}

# 日志设置
LOG_SETTINGS = {
    # 添加日志设置项
}

# 任务设置
TASK_SETTINGS = {
    # 添加任务设置项
}
"""

        # 添加配置项
        for section, section_data in config.items():
            if section_data and isinstance(section_data, dict):
                content += f"\n# {section}\n{section} = {{
"
                for key, value in section_data.items():
                    if isinstance(value, str):
                        content += f"    '{key}': '{value}',\n"
                    else:
                        content += f"    '{key}': {value},\n"
                content += "}\n"
        
        return content
    
    def track_performance(self, metrics: Dict[str, Any]) -> None:
        """
        记录性能指标
        
        Args:
            metrics: 性能指标字典，包含任务成功率、执行时间等
        """
        timestamp = datetime.now().isoformat()
        self.performance_metrics[timestamp] = metrics
        
        # 更新最新配置记录的性能指标
        if self.config_history:
            self.config_history[-1]["performance"] = metrics
            self._save_config_history()
    
    def get_best_config(self, metric_key: str = "task_success_rate") -> Dict[str, Any]:
        """
        获取基于指定性能指标的最佳配置
        
        Args:
            metric_key: 性能指标键名，默认为任务成功率
            
        Returns:
            Dict: 最佳配置
        """
        if not self.config_history:
            return self.current_config
        
        # 筛选有性能指标的配置记录
        valid_configs = [
            config for config in self.config_history 
            if config.get("performance") and metric_key in config.get("performance", {})
        ]
        
        if not valid_configs:
            return self.current_config
        
        # 按性能指标排序
        sorted_configs = sorted(
            valid_configs, 
            key=lambda x: x["performance"][metric_key], 
            reverse=True
        )
        
        return sorted_configs[0]["config"]
    
    def recommend_optimizations(self, current_performance: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于历史配置和性能指标推荐优化配置
        
        Args:
            current_performance: 当前性能指标
            
        Returns:
            Dict: 推荐的优化配置
        """
        # 获取最佳配置
        best_config = self.get_best_config()
        
        # 如果当前配置就是最佳配置，则不需要优化
        if best_config == self.current_config:
            return {}
        
        # 比较当前配置和最佳配置，找出差异
        optimizations = {}
        
        for section, section_data in best_config.items():
            if section not in self.current_config:
                optimizations[section] = section_data
            elif isinstance(section_data, dict) and isinstance(self.current_config[section], dict):
                section_diff = {}
                for key, value in section_data.items():
                    if key not in self.current_config[section] or self.current_config[section][key] != value:
                        section_diff[key] = value
                
                if section_diff:
                    optimizations[section] = section_diff
        
        return optimizations
    
    def apply_recommended_optimizations(self) -> bool:
        """
        应用推荐的优化配置
        
        Returns:
            bool: 是否成功应用优化
        """
        # 获取当前性能指标
        current_performance = self.performance_metrics.get(
            max(self.performance_metrics.keys()) if self.performance_metrics else None,
            {}
        )
        
        # 获取推荐的优化配置
        optimizations = self.recommend_optimizations(current_performance)
        
        if not optimizations:
            print("当前配置已是最优，无需优化")
            return False
        
        # 应用优化配置
        return self.update_config(
            optimizations,
            "基于历史性能自动优化",
            current_performance
        )
    
    def rollback_to_best_config(self) -> bool:
        """
        回滚到历史最佳配置
        
        Returns:
            bool: 是否成功回滚
        """
        # 获取最佳配置
        best_config = self.get_best_config()
        
        # 回滚到最佳配置
        return self.update_config(
            best_config,
            "回滚到历史最佳配置",
            self.performance_metrics.get(max(self.performance_metrics.keys()) if self.performance_metrics else None, {})
        )
    
    def get_config_history_summary(self) -> List[Dict[str, Any]]:
        """
        获取配置历史摘要
        
        Returns:
            List: 配置历史摘要列表
        """
        summary = []
        
        for config in self.config_history:
            # 提取关键信息
            config_summary = {
                "timestamp": config["timestamp"],
                "reason": config["reason"],
                "performance": {}
            }
            
            # 提取性能指标
            if "performance" in config and config["performance"]:
                for key, value in config["performance"].items():
                    if isinstance(value, dict):
                        # 如果是嵌套字典，只取平均值或总值
                        if "average" in value:
                            config_summary["performance"][key] = value["average"]
                        elif "total" in value:
                            config_summary["performance"][key] = value["total"]
                    else:
                        config_summary["performance"][key] = value
            
            summary.append(config_summary)
        
        return summary
    
    def export_config_history(self, output_file: Optional[str] = None) -> str:
        """
        导出配置历史到文件
        
        Args:
            output_file: 输出文件路径，默认为config_history_export.json
            
        Returns:
            str: 输出文件路径
        """
        if output_file is None:
            output_file = os.path.join(
                Path(self.config_file).parent, "config_history_export.json"
            )
        
        # 获取配置历史摘要
        summary = self.get_config_history_summary()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            return output_file
        except IOError as e:
            print(f"导出配置历史失败: {e}")
            return ""


if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python config_monitor.py <配置文件路径>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        # 初始化配置监控器
        monitor = ConfigMonitor(config_file)
        
        # 打印当前配置
        print("当前配置:")
        for section, section_data in monitor.current_config.items():
            print(f"  {section}:")
            for key, value in section_data.items():
                print(f"    {key}: {value}")
        
        # 打印配置历史摘要
        print("\n配置历史摘要:")
        for i, config in enumerate(monitor.get_config_history_summary()):
            print(f"  {i+1}. {config['timestamp']} - {config['reason']}")
            if config['performance']:
                print(f"     性能指标: {config['performance']}")
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""

"""