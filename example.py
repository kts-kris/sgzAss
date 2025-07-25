#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
iPad自动化控制系统示例

展示如何使用重构后的系统进行iPad自动化控制
"""

import sys
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import (
    quick_start, ExecutionMode, ConditionType,
    get_logger, PerformanceTimer
)


async def main():
    """主函数 - 演示基本功能"""
    # 设置日志
    logger = get_logger("example")
    logger.info("启动iPad自动化控制系统示例")
    
    try:
        # 快速启动系统
        logger.info("初始化系统...")
        controller, task_manager = quick_start(
            config_file="config.yaml",
            execution_mode=ExecutionMode.SUGGEST  # 使用建议模式，安全演示
        )
        
        # 连接设备
        logger.info("连接iPad设备...")
        with PerformanceTimer("device_connection") as timer:
            success = await controller.connect_device()
            
        if success:
            logger.info(f"设备连接成功，耗时: {timer.duration:.2f}秒")
        else:
            logger.error("设备连接失败")
            return
        
        # 获取设备信息
        device_info = controller.connection_service.device_info
        if device_info:
            logger.info(f"设备信息: {device_info.name} - {device_info.ios_version}")
        
        # 演示截图功能
        logger.info("获取屏幕截图...")
        with PerformanceTimer("screenshot") as timer:
            screenshot = controller.connection_service.get_screenshot()
            
        if screenshot is not None:
            logger.info(f"截图成功，尺寸: {screenshot.shape}, 耗时: {timer.duration:.2f}秒")
        else:
            logger.error("截图失败")
            return
        
        # 演示屏幕分析
        logger.info("分析屏幕内容...")
        with PerformanceTimer("screen_analysis") as timer:
            analysis = await controller.analyze_screen()
            
        if analysis:
            logger.info(f"屏幕分析完成，识别到 {len(analysis.elements)} 个元素，耗时: {timer.duration:.2f}秒")
        else:
            logger.warning("屏幕分析失败")
        
        # 演示元素查找
        logger.info("查找界面元素...")
        # 注意：这里需要实际的模板文件
        # element = controller.find_element("templates/home_button.png")
        # if element:
        #     logger.info(f"找到元素: {element.element_type} at ({element.x}, {element.y})")
        
        # 演示任务创建和执行
        logger.info("创建自动化任务...")
        task = task_manager.create_task("示例任务")
        
        # 添加任务步骤
        from src.models.data_types import Action, ActionType
        click_action = Action(action_type=ActionType.TAP, position=(100, 200), description="点击坐标(100, 200)")
        task_manager.add_action_step(task.name, "click_step", click_action)
        task_manager.add_wait_step(task.name, "wait_step", 2.0)
        
        # 创建条件对象
        condition = task_manager.create_element_exists_condition("templates/success_indicator.png")
        task_manager.add_condition_step(
            task.name, 
            "condition_step",
            condition
        )
        
        # 执行任务（建议模式）
        logger.info("执行任务...")
        with PerformanceTimer("task_execution") as timer:
            result = await task_manager.execute_task(task.name)
            
        if result:
            logger.info(f"任务执行成功，耗时: {timer.duration:.2f}秒")
        else:
            logger.warning(f"任务执行失败")
        
        # 获取系统状态
        status = controller.get_system_status()
        logger.info(f"系统状态: 连接={status.connection_status}, 内存使用={status.memory_usage}MB")
        
        # 演示性能统计
        performance_stats = controller.get_performance_stats()
        logger.info("性能统计:")
        for key, value in performance_stats.items():
            if isinstance(value, (int, float)):
                if key == "average_response_time":
                    logger.info(f"  {key}: {value:.2f}秒")
                else:
                    logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"示例执行出错: {e}", exc_info=True)
    
    finally:
        # 清理资源
        logger.info("清理资源...")
        try:
            await controller.disconnect_device()
            logger.info("设备连接已断开")
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")


async def demo_advanced_features():
    """演示高级功能"""
    logger = get_logger("advanced_demo")
    logger.info("演示高级功能...")
    
    try:
        # 创建控制器（执行模式）
        controller, task_manager = quick_start(
            execution_mode=ExecutionMode.AUTO
        )
        
        # 设置自动化后端
        controller.set_automation_backend("webdriver")
        logger.info("已设置WebDriver自动化后端")
        
        # 启用VLM识别（如果配置了API密钥）
        # controller.enable_vlm()
        # logger.info("已启用VLM大模型识别")
        
        # 连接设备
        success = await controller.connect_device()
        if not success:
            logger.error("设备连接失败")
            return
        
        # 复杂任务示例
        task = task_manager.create_task("复杂自动化任务")
        
        # 添加多个步骤
        steps = [
            ("click_element", {"template": "templates/menu_button.png"}),
            ("wait", {"duration": 1.0}),
            ("swipe", {"start_x": 200, "start_y": 400, "end_x": 200, "end_y": 200}),
            ("condition", {"type": ConditionType.ELEMENT_EXISTS, "template": "templates/target.png"}),
            ("click", {"x": 300, "y": 300}),
        ]
        
        from src.models.data_types import Action, ActionType, TaskCondition, ConditionType
        
        for i, (step_type, params) in enumerate(steps):
            step_name = f"step_{i+1}_{step_type}"
            
            if step_type == "click_element":
                # 使用 add_tap_element_step 方法
                task_manager.add_tap_element_step(task.name, step_name, params["template"])
            elif step_type == "wait":
                task_manager.add_wait_step(task.name, step_name, params["duration"])
            elif step_type == "swipe":
                swipe_action = Action(
                    action_type=ActionType.SWIPE,
                    position=(params["start_x"], params["start_y"]),
                    parameters={"target_position": (params["end_x"], params["end_y"])},
                    description="滑动操作"
                )
                task_manager.add_action_step(task.name, step_name, swipe_action)
            elif step_type == "condition":
                condition = task_manager.create_element_exists_condition(params["template"])
                task_manager.add_condition_step(task.name, step_name, condition)
            elif step_type == "click":
                click_action = Action(
                    action_type=ActionType.TAP,
                    position=(params["x"], params["y"]),
                    description="点击操作"
                )
                task_manager.add_action_step(task.name, step_name, click_action)
        
        # 执行任务
        logger.info("执行复杂任务...")
        result = await task_manager.execute_task(task.name)
        
        if result:
            logger.info("复杂任务执行成功")
        else:
            logger.warning("复杂任务执行失败")
        
        # 获取任务历史
        tasks = task_manager.list_tasks()
        logger.info(f"任务历史: 共 {len(tasks)} 个任务")
        
    except Exception as e:
        logger.error(f"高级功能演示出错: {e}", exc_info=True)
    
    finally:
        try:
            await controller.disconnect_device()
        except:
            pass


if __name__ == "__main__":
    import asyncio
    
    print("iPad自动化控制系统 v2.0 示例")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--advanced":
        asyncio.run(demo_advanced_features())
    else:
        asyncio.run(main())
    
    print("\n示例执行完成")
    print("\n使用说明:")
    print("- 基础示例: python example.py")
    print("- 高级示例: python example.py --advanced")
    print("- 配置文件: config.yaml")
    print("- 日志文件: logs/")