#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
三国志战略版自动化助手主程序

这个脚本是程序的入口点，负责初始化各个模块并协调它们的工作。
"""

import sys
import time
import argparse
from pathlib import Path

# 确保可以导入自定义模块
sys.path.append(str(Path(__file__).parent.absolute()))

# 导入项目模块
from config import GAME_SETTINGS, DEVICE_SETTINGS, LOG_SETTINGS, TASK_SETTINGS
from utils.logger import setup_logger
from utils.log_analyzer import LogAnalyzer
from core.device_connector import DeviceConnector
from core.vision import VisionSystem
from core.controller import GameController
from tasks.task_manager import TaskManager


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="三国志战略版自动化助手")
    parser.add_argument(
        "--config", 
        type=str, 
        help="指定配置文件路径"
    )
    parser.add_argument(
        "--task", 
        type=str, 
        choices=["land", "army", "resource", "all"], 
        default="all",
        help="指定要执行的任务类型"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="启用调试模式"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="仅识别不执行操作"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=0,
        help="运行持续时间（分钟），0表示持续运行直到手动停止"
    )
    parser.add_argument(
        "--analyze-logs", 
        action="store_true", 
        help="启用日志分析功能"
    )
    parser.add_argument(
        "--generate-report", 
        action="store_true", 
        help="生成日志分析报告"
    )
    parser.add_argument(
        "--optimize", 
        action="store_true", 
        help="根据日志分析结果优化配置"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志
    logger = setup_logger(LOG_SETTINGS, debug=args.debug)
    logger.info("启动三国志战略版自动化助手")
    
    # 如果启用了日志分析功能，则初始化日志分析器
    log_analyzer = None
    if args.analyze_logs or args.generate_report or args.optimize:
        log_file = LOG_SETTINGS.get("file_path")
        if log_file:
            logger.info("初始化日志分析器")
            log_analyzer = LogAnalyzer(log_file)
            
            # 解析日志
            if not log_analyzer.parse_logs():
                logger.error("日志解析失败")
            else:
                logger.info("日志解析成功")
                
                # 分析性能
                performance = log_analyzer.analyze_performance()
                
                # 生成报告
                if args.generate_report:
                    report_file = log_analyzer.generate_report()
                    logger.info(f"分析报告已生成: {report_file}")
                
                # 应用优化建议
                if args.optimize:
                    config_file = "config.custom.py"
                    if log_analyzer.apply_optimizations(config_file):
                        logger.info(f"已成功应用优化建议到配置文件: {config_file}")
                    else:
                        logger.error(f"应用优化建议失败")
        else:
            logger.error("未找到日志文件路径，无法进行日志分析")
    
    try:
        # 连接设备
        logger.info(f"正在连接设备，连接方式: {DEVICE_SETTINGS['connection_type']}")
        device = DeviceConnector(DEVICE_SETTINGS)
        if not device.connect():
            logger.error("设备连接失败，请检查设备连接设置")
            return 1
        logger.info("设备连接成功")
        
        # 初始化视觉系统
        vision = VisionSystem(GAME_SETTINGS)
        
        # 初始化游戏控制器
        controller = GameController(device, vision, GAME_SETTINGS, dry_run=args.dry_run)
        
        # 初始化任务管理器
        task_manager = TaskManager(controller, TASK_SETTINGS)
        
        # 根据参数选择要执行的任务
        if args.task == "land":
            task_manager.enable_only(["land_occupation"])
        elif args.task == "army":
            task_manager.enable_only(["army_movement"])
        elif args.task == "resource":
            task_manager.enable_only(["resource_collection"])
        # "all"选项默认启用所有任务
        
        # 计算结束时间（如果设置了持续时间）
        end_time = None
        if args.duration > 0:
            end_time = time.time() + args.duration * 60
            logger.info(f"助手将运行 {args.duration} 分钟")
        else:
            logger.info("助手将持续运行直到手动停止")
        
        # 主循环
        try:
            while True:
                # 检查是否达到结束时间
                if end_time and time.time() >= end_time:
                    logger.info("达到设定的运行时间，程序结束")
                    break
                
                # 执行任务循环
                task_manager.run_cycle()
                
                # 短暂休息，避免CPU占用过高
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("接收到终止信号，正在停止...")
        
        # 断开设备连接
        device.disconnect()
        logger.info("设备已断开连接")
        
        # 如果启用了日志分析功能，在程序结束时进行分析
        if log_analyzer and args.analyze_logs and not (args.generate_report or args.optimize):
            logger.info("程序结束，开始分析日志...")
            performance = log_analyzer.analyze_performance()
            bottlenecks = log_analyzer.identify_bottlenecks()
            optimizations = log_analyzer.suggest_optimizations()
            
            # 输出简要分析结果
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
        
        return 0
        
    except Exception as e:
        logger.exception(f"程序运行出错: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())