#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能监控和可视化模块

此模块负责实时监控游戏自动化助手的性能指标，并生成可视化报告。
它可以跟踪任务执行时间、成功率、资源使用情况等指标，并提供实时和历史数据的可视化。
"""

import os
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

# 尝试导入可视化相关的库
try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    print("警告: 未安装matplotlib或numpy，可视化功能将被禁用")


class PerformanceMonitor:
    """性能监控和可视化类"""
    
    def __init__(self, log_file: str, output_dir: Optional[str] = None, 
                 update_interval: int = 60, history_length: int = 24):
        """
        初始化性能监控器
        
        Args:
            log_file: 日志文件路径
            output_dir: 输出目录，默认为日志文件所在目录下的performance_reports
            update_interval: 更新间隔（秒），默认为60秒
            history_length: 历史数据保留时长（小时），默认为24小时
        """
        self.log_file = log_file
        self.output_dir = output_dir or os.path.join(
            Path(log_file).parent, "performance_reports"
        )
        self.update_interval = update_interval
        self.history_length = history_length
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化性能指标
        self.metrics = {
            "task_execution": {},  # 任务执行指标
            "resource_usage": {},  # 资源使用指标
            "recognition_quality": {},  # 识别质量指标
            "error_rates": {},  # 错误率指标
        }
        
        # 初始化历史数据
        self.history = {
            "timestamps": [],
            "task_execution": {},
            "resource_usage": {},
            "recognition_quality": {},
            "error_rates": {},
        }
        
        # 初始化监控线程
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # 设置日志
        self.logger = logging.getLogger("PerformanceMonitor")
    
    def start_monitoring(self) -> None:
        """
        启动性能监控
        """
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.logger.warning("监控线程已在运行")
            return
        
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(f"性能监控已启动，更新间隔: {self.update_interval}秒")
    
    def stop_monitoring(self) -> None:
        """
        停止性能监控
        """
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self.logger.warning("监控线程未运行")
            return
        
        self.stop_event.set()
        self.monitor_thread.join(timeout=5.0)
        if self.monitor_thread.is_alive():
            self.logger.warning("监控线程未能正常停止")
        else:
            self.logger.info("性能监控已停止")
    
    def _monitoring_loop(self) -> None:
        """
        监控循环
        """
        last_position = 0
        
        while not self.stop_event.is_set():
            try:
                # 解析日志文件
                new_position = os.path.getsize(self.log_file)
                if new_position > last_position:
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        f.seek(last_position)
                        new_lines = f.readlines()
                    
                    # 更新指标
                    self._update_metrics(new_lines)
                    last_position = new_position
                
                # 更新历史数据
                self._update_history()
                
                # 生成报告
                self._generate_report()
                
                # 清理过期历史数据
                self._cleanup_history()
                
            except Exception as e:
                self.logger.error(f"监控循环出错: {e}")
            
            # 等待下一次更新
            self.stop_event.wait(self.update_interval)
    
    def _update_metrics(self, log_lines: List[str]) -> None:
        """
        根据日志更新性能指标
        
        Args:
            log_lines: 新的日志行
        """
        for line in log_lines:
            try:
                # 解析日志行
                if "任务执行" in line and "耗时" in line:
                    # 解析任务执行时间
                    self._parse_task_execution(line)
                elif "识别" in line and "置信度" in line:
                    # 解析识别质量
                    self._parse_recognition_quality(line)
                elif "错误" in line or "失败" in line or "异常" in line:
                    # 解析错误
                    self._parse_error(line)
            except Exception as e:
                self.logger.error(f"解析日志行出错: {e}, 行: {line}")
    
    def _parse_task_execution(self, log_line: str) -> None:
        """
        解析任务执行日志
        
        Args:
            log_line: 日志行
        """
        # 示例日志格式: "[INFO] 2023-01-01 12:00:00 - 任务执行: LandOccupationTask 成功, 耗时: 2.5秒"
        try:
            # 提取任务名称
            task_name = log_line.split("任务执行:")[1].split("成功")[0].strip()
            
            # 提取执行时间
            execution_time = float(log_line.split("耗时:")[1].split("秒")[0].strip())
            
            # 更新任务执行指标
            if task_name not in self.metrics["task_execution"]:
                self.metrics["task_execution"][task_name] = {
                    "count": 0,
                    "success_count": 0,
                    "total_time": 0.0,
                    "min_time": float('inf'),
                    "max_time": 0.0,
                }
            
            self.metrics["task_execution"][task_name]["count"] += 1
            
            if "成功" in log_line:
                self.metrics["task_execution"][task_name]["success_count"] += 1
            
            self.metrics["task_execution"][task_name]["total_time"] += execution_time
            self.metrics["task_execution"][task_name]["min_time"] = min(
                self.metrics["task_execution"][task_name]["min_time"], execution_time
            )
            self.metrics["task_execution"][task_name]["max_time"] = max(
                self.metrics["task_execution"][task_name]["max_time"], execution_time
            )
        except Exception as e:
            self.logger.error(f"解析任务执行日志出错: {e}, 行: {log_line}")
    
    def _parse_recognition_quality(self, log_line: str) -> None:
        """
        解析识别质量日志
        
        Args:
            log_line: 日志行
        """
        # 示例日志格式: "[INFO] 2023-01-01 12:00:00 - 识别元素: button_confirm, 置信度: 0.85"
        try:
            # 提取元素类型
            element_type = log_line.split("识别元素:")[1].split(",")[0].strip()
            
            # 提取置信度
            confidence = float(log_line.split("置信度:")[1].strip())
            
            # 更新识别质量指标
            if element_type not in self.metrics["recognition_quality"]:
                self.metrics["recognition_quality"][element_type] = {
                    "count": 0,
                    "total_confidence": 0.0,
                    "min_confidence": 1.0,
                    "max_confidence": 0.0,
                }
            
            self.metrics["recognition_quality"][element_type]["count"] += 1
            self.metrics["recognition_quality"][element_type]["total_confidence"] += confidence
            self.metrics["recognition_quality"][element_type]["min_confidence"] = min(
                self.metrics["recognition_quality"][element_type]["min_confidence"], confidence
            )
            self.metrics["recognition_quality"][element_type]["max_confidence"] = max(
                self.metrics["recognition_quality"][element_type]["max_confidence"], confidence
            )
        except Exception as e:
            self.logger.error(f"解析识别质量日志出错: {e}, 行: {log_line}")
    
    def _parse_error(self, log_line: str) -> None:
        """
        解析错误日志
        
        Args:
            log_line: 日志行
        """
        # 示例日志格式: "[ERROR] 2023-01-01 12:00:00 - 任务执行失败: LandOccupationTask, 错误: 未找到目标元素"
        try:
            # 提取错误类型
            if "错误:" in log_line:
                error_type = log_line.split("错误:")[1].strip()
            elif "失败:" in log_line:
                error_type = log_line.split("失败:")[1].strip()
            elif "异常:" in log_line:
                error_type = log_line.split("异常:")[1].strip()
            else:
                error_type = "未知错误"
            
            # 提取任务名称（如果有）
            task_name = "未知任务"
            if "任务执行失败:" in log_line:
                task_name = log_line.split("任务执行失败:")[1].split(",")[0].strip()
            
            # 更新错误率指标
            error_key = f"{task_name}: {error_type}"
            if error_key not in self.metrics["error_rates"]:
                self.metrics["error_rates"][error_key] = {
                    "count": 0,
                    "last_occurrence": None,
                }
            
            self.metrics["error_rates"][error_key]["count"] += 1
            self.metrics["error_rates"][error_key]["last_occurrence"] = datetime.now().isoformat()
        except Exception as e:
            self.logger.error(f"解析错误日志出错: {e}, 行: {log_line}")
    
    def _update_history(self) -> None:
        """
        更新历史数据
        """
        timestamp = datetime.now().isoformat()
        self.history["timestamps"].append(timestamp)
        
        # 更新任务执行历史
        for task_name, metrics in self.metrics["task_execution"].items():
            if task_name not in self.history["task_execution"]:
                self.history["task_execution"][task_name] = {
                    "success_rate": [],
                    "avg_time": [],
                }
            
            # 计算成功率
            success_rate = metrics["success_count"] / metrics["count"] if metrics["count"] > 0 else 0
            self.history["task_execution"][task_name]["success_rate"].append(success_rate)
            
            # 计算平均执行时间
            avg_time = metrics["total_time"] / metrics["count"] if metrics["count"] > 0 else 0
            self.history["task_execution"][task_name]["avg_time"].append(avg_time)
        
        # 更新识别质量历史
        for element_type, metrics in self.metrics["recognition_quality"].items():
            if element_type not in self.history["recognition_quality"]:
                self.history["recognition_quality"][element_type] = {
                    "avg_confidence": [],
                }
            
            # 计算平均置信度
            avg_confidence = metrics["total_confidence"] / metrics["count"] if metrics["count"] > 0 else 0
            self.history["recognition_quality"][element_type]["avg_confidence"].append(avg_confidence)
        
        # 更新错误率历史
        for error_key, metrics in self.metrics["error_rates"].items():
            if error_key not in self.history["error_rates"]:
                self.history["error_rates"][error_key] = {
                    "count": [],
                }
            
            self.history["error_rates"][error_key]["count"].append(metrics["count"])
    
    def _cleanup_history(self) -> None:
        """
        清理过期的历史数据
        """
        if not self.history["timestamps"]:
            return
        
        # 计算过期时间
        expiry_time = datetime.now() - timedelta(hours=self.history_length)
        expiry_time_str = expiry_time.isoformat()
        
        # 找到过期数据的索引
        expired_indices = []
        for i, timestamp in enumerate(self.history["timestamps"]):
            if timestamp < expiry_time_str:
                expired_indices.append(i)
        
        if not expired_indices:
            return
        
        # 删除过期数据
        self.history["timestamps"] = [ts for i, ts in enumerate(self.history["timestamps"]) if i not in expired_indices]
        
        # 清理任务执行历史
        for task_name in self.history["task_execution"]:
            for metric in self.history["task_execution"][task_name]:
                self.history["task_execution"][task_name][metric] = [
                    val for i, val in enumerate(self.history["task_execution"][task_name][metric])
                    if i not in expired_indices
                ]
        
        # 清理识别质量历史
        for element_type in self.history["recognition_quality"]:
            for metric in self.history["recognition_quality"][element_type]:
                self.history["recognition_quality"][element_type][metric] = [
                    val for i, val in enumerate(self.history["recognition_quality"][element_type][metric])
                    if i not in expired_indices
                ]
        
        # 清理错误率历史
        for error_key in self.history["error_rates"]:
            for metric in self.history["error_rates"][error_key]:
                self.history["error_rates"][error_key][metric] = [
                    val for i, val in enumerate(self.history["error_rates"][error_key][metric])
                    if i not in expired_indices
                ]
    
    def _generate_report(self) -> None:
        """
        生成性能报告
        """
        # 生成HTML报告
        self._generate_html_report()
        
        # 生成JSON报告
        self._generate_json_report()
        
        # 生成可视化图表
        if HAS_VISUALIZATION:
            self._generate_visualizations()
    
    def _generate_html_report(self) -> None:
        """
        生成HTML格式的性能报告
        """
        report_file = os.path.join(self.output_dir, "performance_report.html")
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能监控报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 30px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        .chart-container { margin-top: 20px; margin-bottom: 40px; }
    </style>
</head>
<body>
    <h1>性能监控报告</h1>
    <p>生成时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    
    <h2>任务执行指标</h2>
    <table>
        <tr>
            <th>任务名称</th>
            <th>执行次数</th>
            <th>成功次数</th>
            <th>成功率</th>
            <th>平均执行时间</th>
            <th>最短执行时间</th>
            <th>最长执行时间</th>
        </tr>
""")
                
                # 添加任务执行指标
                for task_name, metrics in self.metrics["task_execution"].items():
                    success_rate = metrics["success_count"] / metrics["count"] if metrics["count"] > 0 else 0
                    avg_time = metrics["total_time"] / metrics["count"] if metrics["count"] > 0 else 0
                    
                    # 根据成功率设置样式
                    rate_class = "success" if success_rate >= 0.8 else "warning" if success_rate >= 0.5 else "error"
                    
                    f.write(f"""        <tr>
            <td>{task_name}</td>
            <td>{metrics['count']}</td>
            <td>{metrics['success_count']}</td>
            <td class="{rate_class}">{success_rate:.1%}</td>
            <td>{avg_time:.2f}秒</td>
            <td>{metrics['min_time'] if metrics['min_time'] != float('inf') else 0:.2f}秒</td>
            <td>{metrics['max_time']:.2f}秒</td>
        </tr>
""")
                
                f.write("""    </table>
    
    <h2>识别质量指标</h2>
    <table>
        <tr>
            <th>元素类型</th>
            <th>识别次数</th>
            <th>平均置信度</th>
            <th>最低置信度</th>
            <th>最高置信度</th>
        </tr>
""")
                
                # 添加识别质量指标
                for element_type, metrics in self.metrics["recognition_quality"].items():
                    avg_confidence = metrics["total_confidence"] / metrics["count"] if metrics["count"] > 0 else 0
                    
                    # 根据置信度设置样式
                    confidence_class = "success" if avg_confidence >= 0.8 else "warning" if avg_confidence >= 0.6 else "error"
                    
                    f.write(f"""        <tr>
            <td>{element_type}</td>
            <td>{metrics['count']}</td>
            <td class="{confidence_class}">{avg_confidence:.2f}</td>
            <td>{metrics['min_confidence']:.2f}</td>
            <td>{metrics['max_confidence']:.2f}</td>
        </tr>
""")
                
                f.write("""    </table>
    
    <h2>错误统计</h2>
    <table>
        <tr>
            <th>错误类型</th>
            <th>发生次数</th>
            <th>最后发生时间</th>
        </tr>
""")
                
                # 添加错误统计
                for error_key, metrics in self.metrics["error_rates"].items():
                    last_occurrence = metrics["last_occurrence"] or ""
                    if last_occurrence:
                        last_occurrence = datetime.fromisoformat(last_occurrence).strftime("%Y-%m-%d %H:%M:%S")
                    
                    f.write(f"""        <tr>
            <td>{error_key}</td>
            <td>{metrics['count']}</td>
            <td>{last_occurrence}</td>
        </tr>
""")
                
                f.write("""    </table>
    
    <h2>性能趋势</h2>
    <p>查看图表目录: <a href="charts/">性能趋势图表</a></p>
    
</body>
</html>
""")
            
            self.logger.info(f"已生成HTML报告: {report_file}")
        except Exception as e:
            self.logger.error(f"生成HTML报告失败: {e}")
    
    def _generate_json_report(self) -> None:
        """
        生成JSON格式的性能报告
        """
        report_file = os.path.join(self.output_dir, "performance_data.json")
        
        try:
            # 准备报告数据
            report_data = {
                "generated_at": datetime.now().isoformat(),
                "metrics": self.metrics,
                "history": {
                    "timestamps": self.history["timestamps"][-100:],  # 只保留最近100个时间点
                }
            }
            
            # 添加任务执行历史
            report_data["history"]["task_execution"] = {}
            for task_name, metrics in self.history["task_execution"].items():
                report_data["history"]["task_execution"][task_name] = {
                    "success_rate": metrics["success_rate"][-100:],
                    "avg_time": metrics["avg_time"][-100:],
                }
            
            # 添加识别质量历史
            report_data["history"]["recognition_quality"] = {}
            for element_type, metrics in self.history["recognition_quality"].items():
                report_data["history"]["recognition_quality"][element_type] = {
                    "avg_confidence": metrics["avg_confidence"][-100:],
                }
            
            # 添加错误率历史
            report_data["history"]["error_rates"] = {}
            for error_key, metrics in self.history["error_rates"].items():
                report_data["history"]["error_rates"][error_key] = {
                    "count": metrics["count"][-100:],
                }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"已生成JSON报告: {report_file}")
        except Exception as e:
            self.logger.error(f"生成JSON报告失败: {e}")
    
    def _generate_visualizations(self) -> None:
        """
        生成可视化图表
        """
        if not HAS_VISUALIZATION:
            self.logger.warning("未安装matplotlib或numpy，无法生成可视化图表")
            return
        
        charts_dir = os.path.join(self.output_dir, "charts")
        os.makedirs(charts_dir, exist_ok=True)
        
        try:
            # 生成任务成功率趋势图
            self._generate_task_success_rate_chart(charts_dir)
            
            # 生成任务执行时间趋势图
            self._generate_task_execution_time_chart(charts_dir)
            
            # 生成识别质量趋势图
            self._generate_recognition_quality_chart(charts_dir)
            
            # 生成错误率趋势图
            self._generate_error_rate_chart(charts_dir)
            
            self.logger.info(f"已生成可视化图表: {charts_dir}")
        except Exception as e:
            self.logger.error(f"生成可视化图表失败: {e}")
    
    def _generate_task_success_rate_chart(self, charts_dir: str) -> None:
        """
        生成任务成功率趋势图
        
        Args:
            charts_dir: 图表输出目录
        """
        if not self.history["timestamps"] or not self.history["task_execution"]:
            return
        
        plt.figure(figsize=(12, 6))
        
        # 转换时间戳为datetime对象
        timestamps = [datetime.fromisoformat(ts) for ts in self.history["timestamps"]]
        
        # 绘制每个任务的成功率趋势
        for task_name, metrics in self.history["task_execution"].items():
            if len(metrics["success_rate"]) == len(timestamps):
                plt.plot(timestamps, metrics["success_rate"], label=task_name, marker='o', markersize=3)
        
        plt.title("任务成功率趋势")
        plt.xlabel("时间")
        plt.ylabel("成功率")
        plt.ylim(0, 1.1)  # 成功率范围为0-1
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # 设置x轴日期格式
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.gcf().autofmt_xdate()
        
        # 保存图表
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "task_success_rate.png"), dpi=100)
        plt.close()
    
    def _generate_task_execution_time_chart(self, charts_dir: str) -> None:
        """
        生成任务执行时间趋势图
        
        Args:
            charts_dir: 图表输出目录
        """
        if not self.history["timestamps"] or not self.history["task_execution"]:
            return
        
        plt.figure(figsize=(12, 6))
        
        # 转换时间戳为datetime对象
        timestamps = [datetime.fromisoformat(ts) for ts in self.history["timestamps"]]
        
        # 绘制每个任务的执行时间趋势
        for task_name, metrics in self.history["task_execution"].items():
            if len(metrics["avg_time"]) == len(timestamps):
                plt.plot(timestamps, metrics["avg_time"], label=task_name, marker='o', markersize=3)
        
        plt.title("任务执行时间趋势")
        plt.xlabel("时间")
        plt.ylabel("执行时间 (秒)")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # 设置x轴日期格式
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.gcf().autofmt_xdate()
        
        # 保存图表
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "task_execution_time.png"), dpi=100)
        plt.close()
    
    def _generate_recognition_quality_chart(self, charts_dir: str) -> None:
        """
        生成识别质量趋势图
        
        Args:
            charts_dir: 图表输出目录
        """
        if not self.history["timestamps"] or not self.history["recognition_quality"]:
            return
        
        plt.figure(figsize=(12, 6))
        
        # 转换时间戳为datetime对象
        timestamps = [datetime.fromisoformat(ts) for ts in self.history["timestamps"]]
        
        # 绘制每个元素类型的置信度趋势
        for element_type, metrics in self.history["recognition_quality"].items():
            if len(metrics["avg_confidence"]) == len(timestamps):
                plt.plot(timestamps, metrics["avg_confidence"], label=element_type, marker='o', markersize=3)
        
        plt.title("识别质量趋势")
        plt.xlabel("时间")
        plt.ylabel("平均置信度")
        plt.ylim(0, 1.1)  # 置信度范围为0-1
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # 设置x轴日期格式
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.gcf().autofmt_xdate()
        
        # 保存图表
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "recognition_quality.png"), dpi=100)
        plt.close()
    
    def _generate_error_rate_chart(self, charts_dir: str) -> None:
        """
        生成错误率趋势图
        
        Args:
            charts_dir: 图表输出目录
        """
        if not self.history["timestamps"] or not self.history["error_rates"]:
            return
        
        plt.figure(figsize=(12, 6))
        
        # 转换时间戳为datetime对象
        timestamps = [datetime.fromisoformat(ts) for ts in self.history["timestamps"]]
        
        # 绘制每种错误类型的发生次数趋势
        for error_key, metrics in self.history["error_rates"].items():
            if len(metrics["count"]) == len(timestamps):
                # 计算累计错误数
                cumulative_counts = np.cumsum(metrics["count"])
                plt.plot(timestamps, cumulative_counts, label=error_key, marker='o', markersize=3)
        
        plt.title("错误累计趋势")
        plt.xlabel("时间")
        plt.ylabel("累计错误数")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # 设置x轴日期格式
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.gcf().autofmt_xdate()
        
        # 保存图表
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "error_rate.png"), dpi=100)
        plt.close()
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        获取当前性能指标
        
        Returns:
            Dict: 当前性能指标
        """
        return self.metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            Dict: 性能摘要
        """
        summary = {
            "task_success_rate": {},
            "avg_execution_time": {},
            "avg_recognition_quality": {},
            "top_errors": [],
        }
        
        # 计算任务成功率
        for task_name, metrics in self.metrics["task_execution"].items():
            success_rate = metrics["success_count"] / metrics["count"] if metrics["count"] > 0 else 0
            summary["task_success_rate"][task_name] = success_rate
            
            avg_time = metrics["total_time"] / metrics["count"] if metrics["count"] > 0 else 0
            summary["avg_execution_time"][task_name] = avg_time
        
        # 计算平均识别质量
        for element_type, metrics in self.metrics["recognition_quality"].items():
            avg_confidence = metrics["total_confidence"] / metrics["count"] if metrics["count"] > 0 else 0
            summary["avg_recognition_quality"][element_type] = avg_confidence
        
        # 获取前5个最常见错误
        sorted_errors = sorted(
            self.metrics["error_rates"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:5]
        
        for error_key, metrics in sorted_errors:
            summary["top_errors"].append({
                "error": error_key,
                "count": metrics["count"],
                "last_occurrence": metrics["last_occurrence"],
            })
        
        return summary


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="性能监控和可视化工具")
    parser.add_argument("--log", required=True, help="日志文件路径")
    parser.add_argument("--output", help="输出目录路径")
    parser.add_argument("--interval", type=int, default=60, help="更新间隔（秒），默认为60秒")
    parser.add_argument("--history", type=int, default=24, help="历史数据保留时长（小时），默认为24小时")
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 初始化性能监控器
    monitor = PerformanceMonitor(
        log_file=args.log,
        output_dir=args.output,
        update_interval=args.interval,
        history_length=args.history
    )
    
    try:
        # 启动监控
        monitor.start_monitoring()
        print(f"性能监控已启动，按Ctrl+C停止")
        
        # 等待中断信号
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("接收到终止信号，正在停止...")
    finally:
        # 停止监控
        monitor.stop_monitoring()
        
        # 生成最终报告
        print("生成最终报告...")
        monitor._generate_report()
        
        # 输出性能摘要
        summary = monitor.get_performance_summary()
        print("\n性能摘要:")
        
        print("\n任务成功率:")
        for task, rate in summary["task_success_rate"].items():
            print(f"  {task}: {rate:.1%}")
        
        print("\n平均执行时间:")
        for task, time_val in summary["avg_execution_time"].items():
            print(f"  {task}: {time_val:.2f}秒")
        
        print("\n平均识别质量:")
        for element, confidence in summary["avg_recognition_quality"].items():
            print(f"  {element}: {confidence:.2f}")
        
        print("\n常见错误:")
        for error in summary["top_errors"]:
            print(f"  {error['error']}: {error['count']}次")
        
        print(f"\n详细报告已保存到: {monitor.output_dir}")