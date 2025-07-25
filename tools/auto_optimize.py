#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动日志分析和调优工具

此工具可以定期运行，分析日志并自动应用优化建议。
可以通过定时任务（如cron）或手动运行。
"""

import os
import sys
import time
import argparse
import schedule
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.log_analyzer import LogAnalyzer
from utils.logger import setup_logger
from config import LOG_SETTINGS


def analyze_and_optimize(log_file, config_file, generate_report=True, apply_optimizations=True):
    """
    分析日志并应用优化建议
    
    Args:
        log_file: 日志文件路径
        config_file: 配置文件路径
        generate_report: 是否生成报告
        apply_optimizations: 是否应用优化建议
        
    Returns:
        bool: 是否成功
    """
    logger.info(f"开始分析日志: {log_file}")
    
    # 初始化日志分析器
    analyzer = LogAnalyzer(log_file)
    
    # 解析日志
    if not analyzer.parse_logs():
        logger.error("日志解析失败")
        return False
    
    # 分析性能
    performance = analyzer.analyze_performance()
    
    # 识别瓶颈
    bottlenecks = analyzer.identify_bottlenecks()
    
    # 生成优化建议
    optimizations = analyzer.suggest_optimizations()
    
    # 输出分析结果摘要
    logger.info("===== 日志分析结果摘要 =====")
    
    # 任务成功率
    for task, rate in performance['task_success_rate'].items():
        status = "✓" if rate > 0.8 else "!" if rate > 0.5 else "✗"
        logger.info(f"任务成功率: {status} {task}: {rate:.1%}")
    
    # 瓶颈
    if any(bottlenecks.values()):
        logger.info("检测到的瓶颈:")
        for category, items in bottlenecks.items():
            if items:
                for item in items:
                    if category == 'slow_tasks':
                        logger.info(f"慢任务: {item['task']} ({item['avg_duration']:.1f}秒)")
                    elif category == 'frequent_errors':
                        logger.info(f"频繁错误: {item['error'][:50]}...")
    
    # 优化建议
    if any(optimizations.values()):
        logger.info("优化建议:")
        for category, items in optimizations.items():
            if items:
                for item in items:
                    if category == 'task_parameters':
                        params = ", ".join([f"{k}: {v}" for k, v in item['parameters'].items()])
                        logger.info(f"任务参数: {item['task']} ({params})")
                    elif category == 'recognition_settings':
                        logger.info(f"识别设置: {item['setting']} ({item['new_value']})")
    
    # 生成报告
    if generate_report:
        report_file = analyzer.generate_report()
        logger.info(f"分析报告已生成: {report_file}")
    
    # 应用优化建议
    if apply_optimizations and any(optimizations.values()):
        if analyzer.apply_optimizations(config_file):
            logger.info(f"已成功应用优化建议到配置文件: {config_file}")
        else:
            logger.error(f"应用优化建议失败")
            return False
    
    return True


def scheduled_job(log_file, config_file, generate_report, apply_optimizations):
    """
    定时任务，分析日志并应用优化建议
    
    Args:
        log_file: 日志文件路径
        config_file: 配置文件路径
        generate_report: 是否生成报告
        apply_optimizations: 是否应用优化建议
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{timestamp}] 执行定时分析任务")
    
    try:
        analyze_and_optimize(log_file, config_file, generate_report, apply_optimizations)
    except Exception as e:
        logger.exception(f"定时任务执行出错: {e}")


def main():
    """主函数，处理命令行参数并执行相应的任务"""
    parser = argparse.ArgumentParser(description="三国志战略版自动化助手日志分析和调优工具")
    parser.add_argument("--log", help="日志文件路径，默认使用配置中的日志文件", default=None)
    parser.add_argument("--config", help="配置文件路径，默认为项目根目录下的config.custom.py", default=None)
    parser.add_argument("--no-report", action="store_true", help="不生成分析报告")
    parser.add_argument("--no-optimize", action="store_true", help="不应用优化建议")
    parser.add_argument("--schedule", action="store_true", help="启用定时任务模式")
    parser.add_argument("--interval", type=int, default=24, help="定时任务间隔（小时），默认为24小时")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 设置日志
    global logger
    log_level = "DEBUG" if args.debug else LOG_SETTINGS.get("level", "INFO")
    logger = setup_logger(level=log_level)
    
    # 确定日志文件路径
    log_file = args.log
    if log_file is None:
        log_file = LOG_SETTINGS.get("file_path")
        if not log_file:
            logger.error("未指定日志文件路径，请使用--log参数或在配置中设置LOG_SETTINGS.file_path")
            return 1
    
    # 检查日志文件是否存在
    if not os.path.exists(log_file):
        logger.error(f"日志文件不存在: {log_file}")
        return 1
    
    # 确定配置文件路径
    config_file = args.config
    if config_file is None:
        config_file = os.path.join(Path(__file__).parent.parent, "config.custom.py")
    
    # 检查配置文件是否存在，如果不存在则创建
    if not os.path.exists(config_file):
        logger.info(f"配置文件不存在，将创建新文件: {config_file}")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自定义配置文件

此文件由自动优化工具生成，包含基于日志分析的优化建议。
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
    
    # 是否生成报告和应用优化建议
    generate_report = not args.no_report
    apply_optimizations = not args.no_optimize
    
    # 定时任务模式
    if args.schedule:
        logger.info(f"启动定时任务模式，间隔: {args.interval}小时")
        
        # 设置定时任务
        schedule.every(args.interval).hours.do(
            scheduled_job, log_file, config_file, generate_report, apply_optimizations
        )
        
        logger.info("定时任务已设置，按Ctrl+C停止")
        
        try:
            # 立即执行一次
            scheduled_job(log_file, config_file, generate_report, apply_optimizations)
            
            # 定时任务循环
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
        except KeyboardInterrupt:
            logger.info("接收到终止信号，正在停止...")
        
    else:
        # 单次执行模式
        logger.info("执行单次分析任务")
        if analyze_and_optimize(log_file, config_file, generate_report, apply_optimizations):
            logger.info("分析任务完成")
            return 0
        else:
            logger.error("分析任务失败")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())