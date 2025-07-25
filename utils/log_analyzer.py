#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志分析器模块

提供基于日志的自我分析和调优功能，用于监控系统性能、识别问题模式、
优化任务参数和提供运行时反馈。
"""

import os
import re
import json
import time
import datetime
from collections import defaultdict, Counter
from loguru import logger
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class LogAnalyzer:
    """日志分析器类，提供基于日志的自我分析和调优功能"""
    
    def __init__(self, log_file, config=None):
        """
        初始化日志分析器
        
        Args:
            log_file: 日志文件路径
            config: 分析器配置
        """
        self.log_file = log_file
        self.config = config or {}
        
        # 分析结果存储
        self.results_dir = self.config.get('results_dir', os.path.join(Path(log_file).parent, 'analysis'))
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 日志解析正则表达式
        self.log_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\|\s+([A-Z]+)\s+\|\s+([^:]+):([^:]+):(\d+)\s+-\s+(.+)'
        )
        
        # 性能指标
        self.performance_metrics = {
            'task_success_rate': {},
            'task_execution_time': {},
            'error_frequency': {},
            'recognition_confidence': [],
        }
        
        # 任务参数优化记录
        self.optimization_history = defaultdict(list)
        
        # 初始化分析数据结构
        self.parsed_logs = []
        self.task_executions = defaultdict(list)
        self.error_patterns = Counter()
        self.recognition_stats = defaultdict(list)
    
    def parse_logs(self):
        """
        解析日志文件，提取结构化数据
        
        Returns:
            bool: 解析是否成功
        """
        try:
            logger.info(f"开始解析日志文件: {self.log_file}")
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    match = self.log_pattern.match(line.strip())
                    if match:
                        timestamp, level, module, function, line_num, message = match.groups()
                        log_entry = {
                            'timestamp': timestamp,
                            'datetime': datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                            'level': level,
                            'module': module.strip(),
                            'function': function.strip(),
                            'line': int(line_num),
                            'message': message
                        }
                        self.parsed_logs.append(log_entry)
                        
                        # 处理特定类型的日志
                        self._process_log_entry(log_entry)
            
            logger.info(f"日志解析完成，共 {len(self.parsed_logs)} 条记录")
            return True
            
        except Exception as e:
            logger.exception(f"解析日志文件时出错: {e}")
            return False
    
    def _process_log_entry(self, log_entry):
        """
        处理单条日志记录，提取关键信息
        
        Args:
            log_entry: 日志记录字典
        """
        message = log_entry['message']
        module = log_entry['module']
        function = log_entry['function']
        level = log_entry['level']
        
        # 任务执行记录
        if '执行任务:' in message:
            task_name = message.split('执行任务:')[1].strip()
            self.task_executions[task_name].append({
                'start_time': log_entry['datetime'],
                'status': 'started',
                'entry': log_entry
            })
        
        # 任务成功记录
        elif '任务' in message and '执行成功' in message:
            task_match = re.search(r'任务\s+([^\s]+)\s+执行成功', message)
            if task_match:
                task_name = task_match.group(1)
                if task_name in self.task_executions and self.task_executions[task_name]:
                    last_execution = self.task_executions[task_name][-1]
                    if last_execution['status'] == 'started':
                        last_execution['status'] = 'success'
                        last_execution['end_time'] = log_entry['datetime']
                        last_execution['duration'] = (last_execution['end_time'] - last_execution['start_time']).total_seconds()
        
        # 任务失败记录
        elif '任务' in message and '执行失败' in message:
            task_match = re.search(r'任务\s+([^\s]+)\s+执行失败', message)
            if task_match:
                task_name = task_match.group(1)
                if task_name in self.task_executions and self.task_executions[task_name]:
                    last_execution = self.task_executions[task_name][-1]
                    if last_execution['status'] == 'started':
                        last_execution['status'] = 'failure'
                        last_execution['end_time'] = log_entry['datetime']
                        last_execution['duration'] = (last_execution['end_time'] - last_execution['start_time']).total_seconds()
        
        # 错误记录
        if level in ['ERROR', 'WARNING']:
            error_key = f"{module}.{function}: {message[:50]}..."
            self.error_patterns[error_key] += 1
        
        # 图像识别记录
        if '找到' in message and '模板' in message and '匹配' in message:
            match = re.search(r'找到\s+(\d+)\s+个模板\s+([^\s]+)\s+的匹配', message)
            if match:
                count = int(match.group(1))
                template = match.group(2)
                self.recognition_stats[template].append(count)
        
        # 匹配度记录
        if '最佳匹配度:' in message:
            match = re.search(r'最佳匹配度:\s+([0-9.]+)', message)
            if match:
                confidence = float(match.group(1))
                self.performance_metrics['recognition_confidence'].append(confidence)
    
    def analyze_performance(self):
        """
        分析系统性能指标
        
        Returns:
            dict: 性能分析结果
        """
        logger.info("开始分析系统性能指标")
        
        # 计算任务成功率
        for task_name, executions in self.task_executions.items():
            if executions:
                success_count = sum(1 for e in executions if e.get('status') == 'success')
                total_count = len(executions)
                success_rate = success_count / total_count if total_count > 0 else 0
                self.performance_metrics['task_success_rate'][task_name] = success_rate
                
                # 计算平均执行时间
                durations = [e.get('duration', 0) for e in executions if 'duration' in e]
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    self.performance_metrics['task_execution_time'][task_name] = avg_duration
        
        # 计算错误频率
        total_logs = len(self.parsed_logs)
        for error, count in self.error_patterns.most_common(10):
            self.performance_metrics['error_frequency'][error] = count / total_logs if total_logs > 0 else 0
        
        logger.info("性能指标分析完成")
        return self.performance_metrics
    
    def identify_bottlenecks(self):
        """
        识别系统瓶颈和问题模式
        
        Returns:
            dict: 瓶颈分析结果
        """
        logger.info("开始识别系统瓶颈和问题模式")
        
        bottlenecks = {
            'slow_tasks': [],
            'frequent_errors': [],
            'recognition_issues': [],
            'resource_constraints': []
        }
        
        # 识别执行时间长的任务
        task_times = [(task, metrics) for task, metrics in 
                     self.performance_metrics['task_execution_time'].items()]
        task_times.sort(key=lambda x: x[1], reverse=True)
        
        for task, duration in task_times[:3]:  # 取最慢的三个任务
            if duration > 10:  # 超过10秒的任务视为慢任务
                bottlenecks['slow_tasks'].append({
                    'task': task,
                    'avg_duration': duration,
                    'suggestion': f"考虑优化 {task} 任务的执行逻辑或参数设置"
                })
        
        # 识别频繁出现的错误
        for error, frequency in self.performance_metrics['error_frequency'].items():
            if frequency > 0.01:  # 错误率超过1%
                bottlenecks['frequent_errors'].append({
                    'error': error,
                    'frequency': frequency,
                    'suggestion': "检查相关模块的错误处理和异常情况"
                })
        
        # 识别图像识别问题
        low_confidence_count = sum(1 for conf in self.performance_metrics['recognition_confidence'] 
                                if conf < 0.7)
        if low_confidence_count > 0:
            bottlenecks['recognition_issues'].append({
                'issue': '低置信度识别',
                'count': low_confidence_count,
                'suggestion': "考虑重新采集模板或调整匹配阈值"
            })
        
        logger.info(f"识别到 {sum(len(v) for v in bottlenecks.values())} 个潜在瓶颈")
        return bottlenecks
    
    def suggest_optimizations(self):
        """
        根据分析结果提出优化建议
        
        Returns:
            dict: 优化建议
        """
        logger.info("生成优化建议")
        
        optimizations = {
            'task_parameters': [],
            'recognition_settings': [],
            'error_handling': [],
            'resource_allocation': []
        }
        
        # 任务参数优化建议
        for task, success_rate in self.performance_metrics['task_success_rate'].items():
            if success_rate < 0.8:  # 成功率低于80%
                if task == 'land_occupation':
                    optimizations['task_parameters'].append({
                        'task': task,
                        'current_success_rate': success_rate,
                        'suggestion': "增加最大搜索距离或降低目标占领数量",
                        'parameters': {
                            'max_distance': '+100',  # 增加100像素
                            'target_count': '-2'    # 减少2个目标
                        }
                    })
                elif task == 'army_movement':
                    optimizations['task_parameters'].append({
                        'task': task,
                        'current_success_rate': success_rate,
                        'suggestion': "调整空闲部队检查间隔",
                        'parameters': {
                            'idle_army_check_interval': '-60'  # 减少60秒
                        }
                    })
        
        # 识别设置优化建议
        avg_confidence = sum(self.performance_metrics['recognition_confidence']) / \
                        len(self.performance_metrics['recognition_confidence']) \
                        if self.performance_metrics['recognition_confidence'] else 0
        
        if avg_confidence < 0.8:
            optimizations['recognition_settings'].append({
                'setting': 'match_threshold',
                'current_value': 'unknown',  # 需要从配置中获取
                'suggestion': "降低匹配阈值以提高识别率",
                'new_value': '-0.05'  # 降低0.05
            })
        
        # 错误处理优化建议
        if self.error_patterns:
            top_error = self.error_patterns.most_common(1)[0][0]
            optimizations['error_handling'].append({
                'error': top_error,
                'suggestion': "增加重试机制或添加额外的错误处理逻辑"
            })
        
        logger.info(f"生成了 {sum(len(v) for v in optimizations.values())} 条优化建议")
        return optimizations
    
    def generate_report(self, output_file=None):
        """
        生成分析报告
        
        Args:
            output_file: 输出文件路径，如果为None则使用默认路径
            
        Returns:
            str: 报告文件路径
        """
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.results_dir, f"analysis_report_{timestamp}.html")
        
        logger.info(f"生成分析报告: {output_file}")
        
        # 确保已经进行了分析
        if not self.parsed_logs:
            self.parse_logs()
        
        performance = self.analyze_performance()
        bottlenecks = self.identify_bottlenecks()
        optimizations = self.suggest_optimizations()
        
        # 创建报告内容
        report = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <title>三国志战略版自动化助手 - 日志分析报告</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; }",
            "        h1, h2, h3 { color: #333; }",
            "        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }",
            "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "        th { background-color: #f2f2f2; }",
            "        .success { color: green; }",
            "        .warning { color: orange; }",
            "        .error { color: red; }",
            "        .chart { margin: 20px 0; max-width: 800px; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <h1>三国志战略版自动化助手 - 日志分析报告</h1>",
            f"    <p>生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>",
            f"    <p>分析日志: {self.log_file}</p>",
            f"    <p>日志条目数: {len(self.parsed_logs)}</p>",
            
            "    <h2>性能指标</h2>",
            "    <h3>任务成功率</h3>",
            "    <table>",
            "        <tr><th>任务</th><th>成功率</th><th>平均执行时间 (秒)</th></tr>"
        ]
        
        # 添加任务成功率表格
        for task, rate in performance['task_success_rate'].items():
            time_value = performance['task_execution_time'].get(task, 0)
            rate_class = 'success' if rate > 0.8 else 'warning' if rate > 0.5 else 'error'
            report.append(f"        <tr><td>{task}</td><td class='{rate_class}'>{rate:.2%}</td><td>{time_value:.2f}</td></tr>")
        
        report.append("    </table>")
        
        # 添加错误频率表格
        report.extend([
            "    <h3>常见错误</h3>",
            "    <table>",
            "        <tr><th>错误</th><th>频率</th></tr>"
        ])
        
        for error, freq in performance['error_frequency'].items():
            freq_class = 'success' if freq < 0.01 else 'warning' if freq < 0.05 else 'error'
            report.append(f"        <tr><td>{error}</td><td class='{freq_class}'>{freq:.2%}</td></tr>")
        
        report.append("    </table>")
        
        # 添加瓶颈分析
        report.extend([
            "    <h2>系统瓶颈</h2>",
        ])
        
        if bottlenecks['slow_tasks']:
            report.extend([
                "    <h3>慢任务</h3>",
                "    <table>",
                "        <tr><th>任务</th><th>平均执行时间 (秒)</th><th>建议</th></tr>"
            ])
            
            for item in bottlenecks['slow_tasks']:
                report.append(f"        <tr><td>{item['task']}</td><td>{item['avg_duration']:.2f}</td><td>{item['suggestion']}</td></tr>")
            
            report.append("    </table>")
        
        if bottlenecks['frequent_errors']:
            report.extend([
                "    <h3>频繁错误</h3>",
                "    <table>",
                "        <tr><th>错误</th><th>频率</th><th>建议</th></tr>"
            ])
            
            for item in bottlenecks['frequent_errors']:
                report.append(f"        <tr><td>{item['error']}</td><td>{item['frequency']:.2%}</td><td>{item['suggestion']}</td></tr>")
            
            report.append("    </table>")
        
        # 添加优化建议
        report.extend([
            "    <h2>优化建议</h2>",
        ])
        
        if optimizations['task_parameters']:
            report.extend([
                "    <h3>任务参数优化</h3>",
                "    <table>",
                "        <tr><th>任务</th><th>当前成功率</th><th>建议</th><th>参数调整</th></tr>"
            ])
            
            for item in optimizations['task_parameters']:
                params = ", ".join([f"{k}: {v}" for k, v in item['parameters'].items()])
                report.append(f"        <tr><td>{item['task']}</td><td>{item['current_success_rate']:.2%}</td><td>{item['suggestion']}</td><td>{params}</td></tr>")
            
            report.append("    </table>")
        
        if optimizations['recognition_settings']:
            report.extend([
                "    <h3>识别设置优化</h3>",
                "    <table>",
                "        <tr><th>设置</th><th>建议</th><th>调整值</th></tr>"
            ])
            
            for item in optimizations['recognition_settings']:
                report.append(f"        <tr><td>{item['setting']}</td><td>{item['suggestion']}</td><td>{item['new_value']}</td></tr>")
            
            report.append("    </table>")
        
        # 结束HTML
        report.extend([
            "    <h2>结论</h2>",
            "    <p>根据日志分析，系统整体运行情况良好，但仍有优化空间。建议关注以上优化建议，特别是任务参数调整和识别设置优化。</p>",
            "</body>",
            "</html>"
        ])
        
        # 写入报告文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        logger.info(f"分析报告已生成: {output_file}")
        return output_file
    
    def visualize_metrics(self, output_dir=None):
        """
        可视化性能指标
        
        Args:
            output_dir: 输出目录，如果为None则使用默认目录
            
        Returns:
            list: 生成的图表文件路径列表
        """
        if output_dir is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(self.results_dir, f"visualizations_{timestamp}")
        
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"生成性能指标可视化: {output_dir}")
        
        chart_files = []
        
        # 确保已经进行了分析
        if not self.parsed_logs:
            self.parse_logs()
            self.analyze_performance()
        
        # 任务成功率饼图
        if self.performance_metrics['task_success_rate']:
            plt.figure(figsize=(10, 6))
            tasks = list(self.performance_metrics['task_success_rate'].keys())
            rates = list(self.performance_metrics['task_success_rate'].values())
            
            plt.bar(tasks, [r * 100 for r in rates])
            plt.xlabel('任务')
            plt.ylabel('成功率 (%)')
            plt.title('任务成功率')
            plt.ylim(0, 100)
            
            for i, v in enumerate(rates):
                plt.text(i, v * 100 + 2, f"{v:.1%}", ha='center')
            
            chart_path = os.path.join(output_dir, 'task_success_rate.png')
            plt.savefig(chart_path)
            plt.close()
            chart_files.append(chart_path)
        
        # 任务执行时间柱状图
        if self.performance_metrics['task_execution_time']:
            plt.figure(figsize=(10, 6))
            tasks = list(self.performance_metrics['task_execution_time'].keys())
            times = list(self.performance_metrics['task_execution_time'].values())
            
            plt.bar(tasks, times)
            plt.xlabel('任务')
            plt.ylabel('平均执行时间 (秒)')
            plt.title('任务平均执行时间')
            
            for i, v in enumerate(times):
                plt.text(i, v + 0.5, f"{v:.1f}s", ha='center')
            
            chart_path = os.path.join(output_dir, 'task_execution_time.png')
            plt.savefig(chart_path)
            plt.close()
            chart_files.append(chart_path)
        
        # 错误频率饼图
        if self.performance_metrics['error_frequency']:
            plt.figure(figsize=(12, 8))
            errors = list(self.performance_metrics['error_frequency'].keys())
            freqs = list(self.performance_metrics['error_frequency'].values())
            
            # 简化错误名称以适应图表
            short_errors = [e.split(':')[0] + '...' if len(e) > 30 else e for e in errors]
            
            plt.pie(freqs, labels=short_errors, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.title('错误频率分布')
            
            chart_path = os.path.join(output_dir, 'error_frequency.png')
            plt.savefig(chart_path)
            plt.close()
            chart_files.append(chart_path)
        
        # 识别置信度直方图
        if self.performance_metrics['recognition_confidence']:
            plt.figure(figsize=(10, 6))
            
            plt.hist(self.performance_metrics['recognition_confidence'], bins=20, range=(0, 1))
            plt.xlabel('置信度')
            plt.ylabel('频次')
            plt.title('图像识别置信度分布')
            
            chart_path = os.path.join(output_dir, 'recognition_confidence.png')
            plt.savefig(chart_path)
            plt.close()
            chart_files.append(chart_path)
        
        logger.info(f"已生成 {len(chart_files)} 个可视化图表")
        return chart_files
    
    def apply_optimizations(self, config_file, optimizations=None):
        """
        应用优化建议到配置文件
        
        Args:
            config_file: 配置文件路径
            optimizations: 要应用的优化建议，如果为None则使用自动生成的建议
            
        Returns:
            bool: 应用是否成功
        """
        if optimizations is None:
            # 确保已经进行了分析
            if not self.parsed_logs:
                self.parse_logs()
            
            optimizations = self.suggest_optimizations()
        
        logger.info(f"尝试应用优化建议到配置文件: {config_file}")
        
        try:
            # 读取当前配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # 应用任务参数优化
            for task_opt in optimizations.get('task_parameters', []):
                task_name = task_opt['task']
                for param, change in task_opt['parameters'].items():
                    # 构建正则表达式来查找和替换参数
                    pattern = rf'"{param}":\s*(\d+)'  # 数字参数
                    
                    if change.startswith('+'):
                        # 增加参数值
                        def replace_func(match):
                            current = int(match.group(1))
                            new_value = current + int(change[1:])
                            return f'"{param}": {new_value}'
                    elif change.startswith('-'):
                        # 减少参数值
                        def replace_func(match):
                            current = int(match.group(1))
                            new_value = max(0, current - int(change[1:]))
                            return f'"{param}": {new_value}'
                    else:
                        # 直接设置参数值
                        def replace_func(match):
                            return f'"{param}": {change}'
                    
                    config_content = re.sub(pattern, replace_func, config_content)
            
            # 应用识别设置优化
            for recog_opt in optimizations.get('recognition_settings', []):
                setting = recog_opt['setting']
                change = recog_opt['new_value']
                
                # 构建正则表达式来查找和替换设置
                pattern = rf'"{setting}":\s*([0-9.]+)'  # 浮点数参数
                
                if change.startswith('+'):
                    # 增加参数值
                    def replace_func(match):
                        current = float(match.group(1))
                        new_value = min(1.0, current + float(change[1:]))
                        return f'"{setting}": {new_value:.2f}'
                elif change.startswith('-'):
                    # 减少参数值
                    def replace_func(match):
                        current = float(match.group(1))
                        new_value = max(0.0, current - float(change[1:]))
                        return f'"{setting}": {new_value:.2f}'
                else:
                    # 直接设置参数值
                    def replace_func(match):
                        return f'"{setting}": {float(change):.2f}'
                
                config_content = re.sub(pattern, replace_func, config_content)
            
            # 写入更新后的配置
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            logger.info(f"已成功应用优化建议到配置文件")
            return True
            
        except Exception as e:
            logger.exception(f"应用优化建议时出错: {e}")
            return False
    
    def monitor_real_time(self, interval=60, callback=None):
        """
        实时监控日志并分析
        
        Args:
            interval: 监控间隔（秒）
            callback: 回调函数，接收分析结果作为参数
            
        Note:
            此方法会阻塞当前线程，应在单独的线程中运行
        """
        logger.info(f"开始实时监控日志: {self.log_file}，间隔: {interval}秒")
        
        last_size = 0
        last_analysis_time = 0
        
        try:
            while True:
                current_time = time.time()
                
                # 检查文件大小是否变化
                current_size = os.path.getsize(self.log_file)
                
                if current_size > last_size or current_time - last_analysis_time >= 3600:  # 文件有更新或已过1小时
                    logger.debug(f"检测到日志文件更新，重新分析")
                    
                    # 重新解析日志
                    self.parsed_logs = []
                    self.task_executions = defaultdict(list)
                    self.error_patterns = Counter()
                    self.recognition_stats = defaultdict(list)
                    self.parse_logs()
                    
                    # 分析性能
                    performance = self.analyze_performance()
                    bottlenecks = self.identify_bottlenecks()
                    optimizations = self.suggest_optimizations()
                    
                    # 调用回调函数
                    if callback:
                        callback({
                            'performance': performance,
                            'bottlenecks': bottlenecks,
                            'optimizations': optimizations
                        })
                    
                    last_size = current_size
                    last_analysis_time = current_time
                
                # 等待下一次检查
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("实时监控已停止")
        except Exception as e:
            logger.exception(f"实时监控时出错: {e}")


def main():
    """主函数，用于命令行调用"""
    import argparse
    
    parser = argparse.ArgumentParser(description="日志分析器")
    parser.add_argument("log_file", help="日志文件路径")
    parser.add_argument("--report", action="store_true", help="生成分析报告")
    parser.add_argument("--visualize", action="store_true", help="生成可视化图表")
    parser.add_argument("--optimize", help="应用优化建议到指定配置文件")
    parser.add_argument("--monitor", action="store_true", help="实时监控日志")
    parser.add_argument("--interval", type=int, default=60, help="监控间隔（秒）")
    
    args = parser.parse_args()
    
    # 初始化日志分析器
    analyzer = LogAnalyzer(args.log_file)
    
    # 解析日志
    if not analyzer.parse_logs():
        logger.error("日志解析失败，程序退出")
        return 1
    
    # 生成报告
    if args.report:
        report_file = analyzer.generate_report()
        logger.info(f"分析报告已生成: {report_file}")
    
    # 生成可视化图表
    if args.visualize:
        chart_files = analyzer.visualize_metrics()
        logger.info(f"可视化图表已生成: {', '.join(chart_files)}")
    
    # 应用优化建议
    if args.optimize:
        if analyzer.apply_optimizations(args.optimize):
            logger.info(f"已成功应用优化建议到配置文件: {args.optimize}")
        else:
            logger.error(f"应用优化建议失败")
    
    # 实时监控
    if args.monitor:
        def monitor_callback(results):
            logger.info(f"检测到 {len(results['bottlenecks'].get('slow_tasks', []))} 个慢任务")
            logger.info(f"检测到 {len(results['bottlenecks'].get('frequent_errors', []))} 个频繁错误")
            logger.info(f"生成了 {sum(len(v) for v in results['optimizations'].values())} 条优化建议")
        
        logger.info(f"开始实时监控日志: {args.log_file}，按Ctrl+C停止")
        analyzer.monitor_real_time(args.interval, monitor_callback)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())