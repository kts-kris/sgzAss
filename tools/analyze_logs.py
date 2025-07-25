#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志分析工具

用于分析游戏自动化助手的日志，提供性能分析、问题诊断和优化建议。
可以生成HTML报告、可视化图表，并支持自动应用优化建议到配置文件。
"""

import os
import sys
import argparse
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.log_analyzer import LogAnalyzer
from utils.logger import setup_logger
from config import LOG_SETTINGS


def main():
    """主函数，处理命令行参数并执行相应的分析任务"""
    parser = argparse.ArgumentParser(description="三国志战略版自动化助手日志分析工具")
    parser.add_argument("--log", help="日志文件路径，默认使用配置中的日志文件", default=None)
    parser.add_argument("--report", action="store_true", help="生成分析报告")
    parser.add_argument("--visualize", action="store_true", help="生成可视化图表")
    parser.add_argument("--optimize", action="store_true", help="生成优化建议并应用到自定义配置文件")
    parser.add_argument("--monitor", action="store_true", help="实时监控日志并分析")
    parser.add_argument("--interval", type=int, default=60, help="监控间隔（秒）")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = "DEBUG" if args.debug else LOG_SETTINGS.get("level", "INFO")
    setup_logger(level=log_level)
    
    # 确定日志文件路径
    log_file = args.log
    if log_file is None:
        log_file = LOG_SETTINGS.get("file_path")
        if not log_file:
            print("错误: 未指定日志文件路径，请使用--log参数或在配置中设置LOG_SETTINGS.file_path")
            return 1
    
    # 检查日志文件是否存在
    if not os.path.exists(log_file):
        print(f"错误: 日志文件不存在: {log_file}")
        return 1
    
    print(f"分析日志文件: {log_file}")
    
    # 初始化日志分析器
    analyzer = LogAnalyzer(log_file)
    
    # 解析日志
    print("正在解析日志...")
    if not analyzer.parse_logs():
        print("错误: 日志解析失败")
        return 1
    
    # 分析性能
    print("正在分析性能指标...")
    performance = analyzer.analyze_performance()
    
    # 识别瓶颈
    print("正在识别系统瓶颈...")
    bottlenecks = analyzer.identify_bottlenecks()
    
    # 生成优化建议
    print("正在生成优化建议...")
    optimizations = analyzer.suggest_optimizations()
    
    # 输出简要分析结果
    print("\n===== 分析结果摘要 =====")
    
    # 任务成功率
    print("\n任务成功率:")
    for task, rate in performance['task_success_rate'].items():
        status = "✓" if rate > 0.8 else "!" if rate > 0.5 else "✗"
        print(f"  {status} {task}: {rate:.1%}")
    
    # 瓶颈
    if any(bottlenecks.values()):
        print("\n检测到的瓶颈:")
        for category, items in bottlenecks.items():
            if items:
                for item in items:
                    if category == 'slow_tasks':
                        print(f"  - 慢任务: {item['task']} ({item['avg_duration']:.1f}秒)")
                    elif category == 'frequent_errors':
                        print(f"  - 频繁错误: {item['error'][:50]}...")
                    elif category == 'recognition_issues':
                        print(f"  - 识别问题: {item['issue']} ({item['count']}次)")
    else:
        print("\n未检测到明显瓶颈")
    
    # 优化建议
    if any(optimizations.values()):
        print("\n优化建议:")
        for category, items in optimizations.items():
            if items:
                for item in items:
                    if category == 'task_parameters':
                        params = ", ".join([f"{k}: {v}" for k, v in item['parameters'].items()])
                        print(f"  - 任务参数: {item['task']} ({params})")
                    elif category == 'recognition_settings':
                        print(f"  - 识别设置: {item['setting']} ({item['new_value']})")
                    elif category == 'error_handling':
                        print(f"  - 错误处理: {item['suggestion']}")
    else:
        print("\n未生成优化建议")
    
    # 生成报告
    if args.report:
        print("\n正在生成分析报告...")
        report_file = analyzer.generate_report()
        print(f"分析报告已生成: {report_file}")
    
    # 生成可视化图表
    if args.visualize:
        print("\n正在生成可视化图表...")
        chart_files = analyzer.visualize_metrics()
        print(f"已生成 {len(chart_files)} 个可视化图表")
        for chart in chart_files:
            print(f"  - {chart}")
    
    # 应用优化建议
    if args.optimize:
        print("\n正在应用优化建议...")
        
        # 确定配置文件路径
        config_file = os.path.join(Path(__file__).parent.parent, "config.custom.py")
        
        # 检查配置文件是否存在，如果不存在则创建
        if not os.path.exists(config_file):
            print(f"配置文件不存在，将创建新文件: {config_file}")
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自定义配置文件

此文件由日志分析工具自动生成，包含基于日志分析的优化建议。
您可以手动修改此文件以进一步调整配置。
"""

# 游戏设置
GAME_SETTINGS = {
    # 将在此处添加优化后的游戏设置
}

# 设备设置
DEVICE_SETTINGS = {
    # 将在此处添加优化后的设备设置
}

# 日志设置
LOG_SETTINGS = {
    # 将在此处添加优化后的日志设置
}

# 任务设置
TASK_SETTINGS = {
    # 将在此处添加优化后的任务设置
}
""")
        
        # 应用优化建议
        if analyzer.apply_optimizations(config_file):
            print(f"已成功应用优化建议到配置文件: {config_file}")
        else:
            print(f"应用优化建议失败")
    
    # 实时监控
    if args.monitor:
        print(f"\n开始实时监控日志: {log_file}")
        print(f"监控间隔: {args.interval}秒")
        print("按Ctrl+C停止监控")
        
        def monitor_callback(results):
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] 日志分析更新:")
            
            # 输出任务成功率变化
            print("  任务成功率:")
            for task, rate in results['performance']['task_success_rate'].items():
                status = "✓" if rate > 0.8 else "!" if rate > 0.5 else "✗"
                print(f"    {status} {task}: {rate:.1%}")
            
            # 输出检测到的瓶颈
            bottlenecks = results['bottlenecks']
            if any(bottlenecks.values()):
                print("  检测到的瓶颈:")
                for category, items in bottlenecks.items():
                    if items:
                        for item in items:
                            if category == 'slow_tasks':
                                print(f"    - 慢任务: {item['task']} ({item['avg_duration']:.1f}秒)")
                            elif category == 'frequent_errors':
                                print(f"    - 频繁错误: {item['error'][:50]}...")
            
            # 输出新的优化建议
            optimizations = results['optimizations']
            if any(optimizations.values()):
                print("  新的优化建议:")
                for category, items in optimizations.items():
                    if items:
                        for item in items:
                            if category == 'task_parameters':
                                params = ", ".join([f"{k}: {v}" for k, v in item['parameters'].items()])
                                print(f"    - 任务参数: {item['task']} ({params})")
                            elif category == 'recognition_settings':
                                print(f"    - 识别设置: {item['setting']} ({item['new_value']})")
        
        try:
            analyzer.monitor_real_time(args.interval, monitor_callback)
        except KeyboardInterrupt:
            print("\n监控已停止")
    
    print("\n分析完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())