#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
开发者磁盘镜像挂载工具

帮助挂载iOS开发者磁盘镜像以启用截图等服务
"""

import os
import subprocess
import sys
from pathlib import Path
from loguru import logger

def find_developer_disk_image():
    """查找开发者磁盘镜像文件"""
    # 常见的开发者磁盘镜像路径
    possible_paths = [
        "/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/DeviceSupport",
        "/Library/Developer/CommandLineTools/Platforms/iPhoneOS.platform/DeviceSupport",
        "~/Library/Developer/Xcode/iOS DeviceSupport"
    ]
    
    logger.info("正在查找开发者磁盘镜像...")
    
    for base_path in possible_paths:
        expanded_path = os.path.expanduser(base_path)
        if os.path.exists(expanded_path):
            logger.info(f"找到开发者支持目录: {expanded_path}")
            
            # 列出可用的iOS版本
            try:
                versions = os.listdir(expanded_path)
                versions = [v for v in versions if os.path.isdir(os.path.join(expanded_path, v))]
                versions.sort(reverse=True)  # 按版本号降序排列
                
                logger.info(f"可用的iOS版本: {versions[:5]}...")  # 显示前5个版本
                
                # 尝试找到最新版本的镜像文件
                for version in versions:
                    version_path = os.path.join(expanded_path, version)
                    dmg_file = os.path.join(version_path, "DeveloperDiskImage.dmg")
                    signature_file = os.path.join(version_path, "DeveloperDiskImage.dmg.signature")
                    
                    if os.path.exists(dmg_file) and os.path.exists(signature_file):
                        logger.success(f"找到开发者磁盘镜像: {dmg_file}")
                        return dmg_file, signature_file
                        
            except Exception as e:
                logger.warning(f"扫描目录 {expanded_path} 时出错: {e}")
                continue
    
    logger.error("未找到开发者磁盘镜像文件")
    return None, None

def mount_developer_image():
    """挂载开发者磁盘镜像"""
    logger.info("=== 开发者磁盘镜像挂载工具 ===")
    
    # 检查设备连接
    logger.info("检查设备连接...")
    result = subprocess.run(['ideviceinfo'], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("未检测到USB连接的iOS设备")
        return False
    
    # 获取设备信息
    device_info = result.stdout
    if 'ProductVersion:' in device_info:
        ios_version = [line.split(':', 1)[1].strip() for line in device_info.split('\n') if line.startswith('ProductVersion:')][0]
        logger.info(f"检测到iOS版本: {ios_version}")
    
    # 检查当前挂载状态
    logger.info("检查当前挂载状态...")
    mount_result = subprocess.run(['ideviceimagemounter', '-l'], capture_output=True, text=True)
    if mount_result.returncode == 0:
        if 'Status: Complete' in mount_result.stdout:
            logger.success("开发者磁盘镜像已挂载")
            return True
        else:
            logger.info("开发者磁盘镜像未挂载")
    
    # 查找开发者磁盘镜像
    dmg_file, signature_file = find_developer_disk_image()
    if not dmg_file:
        logger.error("无法找到开发者磁盘镜像文件")
        logger.info("请确保已安装Xcode或Xcode Command Line Tools")
        return False
    
    # 尝试挂载
    logger.info(f"正在挂载开发者磁盘镜像: {dmg_file}")
    try:
        result = subprocess.run([
            'ideviceimagemounter',
            dmg_file,
            signature_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.success("开发者磁盘镜像挂载成功！")
            return True
        else:
            logger.error(f"挂载失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("挂载操作超时")
        return False
    except Exception as e:
        logger.exception(f"挂载过程中出错: {e}")
        return False

def test_screenshot_service():
    """测试截图服务"""
    logger.info("测试截图服务...")
    try:
        result = subprocess.run(['idevicescreenshot', 'test_mount_screenshot.tiff'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            logger.success("截图服务工作正常！")
            if os.path.exists('test_mount_screenshot.tiff'):
                logger.info("测试截图已保存: test_mount_screenshot.tiff")
                # 删除测试文件
                os.remove('test_mount_screenshot.tiff')
            return True
        else:
            logger.error(f"截图服务不可用: {result.stderr}")
            return False
            
    except Exception as e:
        logger.exception(f"测试截图服务时出错: {e}")
        return False

def main():
    """主函数"""
    if mount_developer_image():
        test_screenshot_service()
    else:
        logger.error("开发者磁盘镜像挂载失败")
        logger.info("\n解决方案:")
        logger.info("1. 确保已安装Xcode或Xcode Command Line Tools")
        logger.info("2. 确保iPad已信任此电脑")
        logger.info("3. 尝试重新连接iPad")
        logger.info("4. 检查iPad的iOS版本是否受支持")

if __name__ == "__main__":
    main()