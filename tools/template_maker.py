#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板制作工具

从iPad游戏截图中提取和制作各种游戏界面元素的模板
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TemplateMaker:
    """模板制作器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("iPad游戏模板制作工具")
        self.root.geometry("1400x900")
        
        # 当前截图和选择区域
        self.current_image = None
        self.current_image_path = None
        self.selection_start = None
        self.selection_end = None
        self.selection_rect = None
        
        # 图片拖拽相关
        self.drag_start = None
        self.is_dragging = False
        
        # 模板信息
        self.templates = []
        self.current_template_name = ""
        
        # 项目路径
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.screenshots_dir = os.path.join(self.project_root, "resources", "screenshots")
        self.templates_dir = os.path.join(self.project_root, "resources", "templates")
        
        self.setup_ui()
        self.load_latest_screenshot()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # 右侧图像显示区域
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 设置控制面板
        self.setup_control_panel(control_frame)
        
        # 设置图像显示区域
        self.setup_image_panel(image_frame)
    
    def setup_control_panel(self, parent):
        """设置控制面板"""
        # 截图选择
        screenshot_frame = ttk.LabelFrame(parent, text="截图选择")
        screenshot_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(screenshot_frame, text="选择截图文件", 
                  command=self.select_screenshot).pack(fill=tk.X, pady=5)
        
        ttk.Button(screenshot_frame, text="加载最新截图", 
                  command=self.load_latest_screenshot).pack(fill=tk.X, pady=5)
        
        self.screenshot_label = ttk.Label(screenshot_frame, text="未选择截图")
        self.screenshot_label.pack(fill=tk.X, pady=5)
        
        # 模板制作
        template_frame = ttk.LabelFrame(parent, text="模板制作")
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(template_frame, text="模板名称:").pack(anchor=tk.W)
        self.template_name_var = tk.StringVar()
        
        # 预定义的模板名称选项
        template_names = [
            # 基础界面
            "main_menu", "world_map", "battle_interface", "city_view", "alliance_interface",
            
            # 按钮类
            "attack_button", "move_button", "collect_button", "build_button", "upgrade_button",
            "back_button", "confirm_button", "cancel_button", "close_button", "help_button",
            "settings_button", "shop_button", "inventory_button", "research_button",
            
            # 队伍相关
            "troop_icon", "cavalry_icon", "infantry_icon", "archer_icon", "siege_icon",
            "troop_count", "troop_health", "troop_formation", "march_button", "recall_button",
            
            # 地块相关
            "empty_land", "occupied_land", "resource_land", "city_land", "fortress_land",
            "farm_land", "mine_land", "lumber_land", "stone_land", "gold_land",
            
            # 资源相关
            "food_icon", "wood_icon", "stone_icon", "gold_icon", "gem_icon",
            "resource_count", "resource_bar", "storage_full", "resource_node",
            
            # 建筑相关
            "castle_icon", "barracks_icon", "stable_icon", "archery_icon", "workshop_icon",
            "farm_icon", "mine_icon", "lumber_mill_icon", "quarry_icon", "warehouse_icon",
            
            # 状态指示器
            "health_bar", "energy_bar", "progress_bar", "timer_icon", "level_indicator",
            "shield_icon", "buff_icon", "debuff_icon", "notification_icon",
            
            # 对话框和弹窗
            "dialog_box", "popup_window", "alert_dialog", "reward_popup", "error_dialog",
            "loading_screen", "tutorial_popup", "achievement_popup",
            
            # 地图元素
            "player_marker", "enemy_marker", "ally_marker", "neutral_marker",
            "flag_icon", "banner_icon", "territory_border", "path_indicator",
            
            # 其他常用
            "search_button", "filter_button", "sort_button", "refresh_button",
            "next_button", "previous_button", "play_button", "pause_button",
            "custom_template"  # 自定义选项
        ]
        
        self.template_name_combo = ttk.Combobox(template_frame, textvariable=self.template_name_var,
                                              values=template_names, state="readonly")
        self.template_name_combo.pack(fill=tk.X, pady=(0, 5))
        
        # 自定义名称输入框（当选择custom_template时显示）
        self.custom_name_var = tk.StringVar()
        self.custom_name_frame = ttk.Frame(template_frame)
        ttk.Label(self.custom_name_frame, text="自定义名称:").pack(anchor=tk.W)
        self.custom_name_entry = ttk.Entry(self.custom_name_frame, textvariable=self.custom_name_var)
        self.custom_name_entry.pack(fill=tk.X)
        
        # 绑定选择事件
        self.template_name_combo.bind("<<ComboboxSelected>>", self.on_template_name_changed)
        
        ttk.Label(template_frame, text="模板类型:").pack(anchor=tk.W)
        self.template_type_var = tk.StringVar(value="button")
        template_type_combo = ttk.Combobox(template_frame, textvariable=self.template_type_var,
                                         values=["button", "icon", "menu", "dialog", "text", "other"])
        template_type_combo.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(template_frame, text="描述:").pack(anchor=tk.W)
        self.template_desc_var = tk.StringVar()
        ttk.Entry(template_frame, textvariable=self.template_desc_var).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(template_frame, text="保存当前选择为模板", 
                  command=self.save_template).pack(fill=tk.X, pady=5)
        
        # 选择信息
        selection_frame = ttk.LabelFrame(parent, text="选择信息")
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.selection_info = ttk.Label(selection_frame, text="未选择区域")
        self.selection_info.pack(fill=tk.X, pady=5)
        
        # 已制作的模板列表
        templates_frame = ttk.LabelFrame(parent, text="已制作模板")
        templates_frame.pack(fill=tk.BOTH, expand=True)
        
        # 模板列表
        self.templates_tree = ttk.Treeview(templates_frame, columns=("type", "size"), show="tree headings")
        self.templates_tree.heading("#0", text="名称")
        self.templates_tree.heading("type", text="类型")
        self.templates_tree.heading("size", text="尺寸")
        self.templates_tree.column("#0", width=120)
        self.templates_tree.column("type", width=60)
        self.templates_tree.column("size", width=80)
        
        scrollbar = ttk.Scrollbar(templates_frame, orient=tk.VERTICAL, command=self.templates_tree.yview)
        self.templates_tree.configure(yscrollcommand=scrollbar.set)
        
        self.templates_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="导出模板信息", 
                  command=self.export_templates).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="清除所有选择", 
                  command=self.clear_selection).pack(fill=tk.X, pady=2)
    
    def setup_image_panel(self, parent):
        """设置图像显示面板"""
        # 创建画布
        self.canvas = tk.Canvas(parent, bg="white")
        
        # 添加滚动条
        h_scrollbar = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # 布局
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # 绑定右键拖拽事件
        self.canvas.bind("<Button-2>", self.on_right_mouse_press)  # macOS 右键
        self.canvas.bind("<Button-3>", self.on_right_mouse_press)  # Windows/Linux 右键
        self.canvas.bind("<B2-Motion>", self.on_right_mouse_drag)
        self.canvas.bind("<B3-Motion>", self.on_right_mouse_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_right_mouse_release)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_mouse_release)
        
        # 绑定鼠标滚轮缩放事件
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux 向上滚动
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux 向下滚动
    
    def select_screenshot(self):
        """选择截图文件"""
        file_path = filedialog.askopenfilename(
            title="选择截图文件",
            initialdir=self.screenshots_dir,
            filetypes=[("PNG files", "*.png"), ("JPG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_screenshot(file_path)
    
    def load_latest_screenshot(self):
        """加载最新的截图"""
        try:
            if not os.path.exists(self.screenshots_dir):
                messagebox.showerror("错误", "截图目录不存在")
                return
            
            # 获取最新的截图文件
            screenshot_files = [f for f in os.listdir(self.screenshots_dir) 
                              if f.endswith(('.png', '.jpg', '.jpeg'))]
            
            if not screenshot_files:
                messagebox.showwarning("警告", "截图目录中没有找到图片文件")
                return
            
            # 按修改时间排序，获取最新的
            screenshot_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.screenshots_dir, x)), reverse=True)
            latest_file = os.path.join(self.screenshots_dir, screenshot_files[0])
            
            self.load_screenshot(latest_file)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载最新截图失败: {e}")
    
    def load_screenshot(self, file_path):
        """加载截图"""
        try:
            # 加载图像
            self.current_image = Image.open(file_path)
            self.current_image_path = file_path
            
            # 更新标签
            filename = os.path.basename(file_path)
            self.screenshot_label.config(text=f"当前: {filename}")
            
            # 显示图像
            self.display_image()
            
            # 清除之前的选择
            self.clear_selection()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载截图失败: {e}")
    
    def display_image(self):
        """显示图像到画布"""
        if not self.current_image:
            return
        
        # 转换为Tkinter可显示的格式
        self.photo = ImageTk.PhotoImage(self.current_image)
        
        # 清除画布
        self.canvas.delete("all")
        
        # 显示图像
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # 更新画布滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_mouse_press(self, event):
        """鼠标按下事件"""
        # 转换画布坐标
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        self.selection_start = (x, y)
        
        # 清除之前的选择矩形
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
    
    def on_mouse_drag(self, event):
        """鼠标拖拽事件"""
        if not self.selection_start:
            return
        
        # 转换画布坐标
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # 清除之前的选择矩形
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        
        # 绘制新的选择矩形
        self.selection_rect = self.canvas.create_rectangle(
            self.selection_start[0], self.selection_start[1], x, y,
            outline="red", width=2
        )
    
    def on_mouse_release(self, event):
        """鼠标释放事件"""
        if not self.selection_start:
            return
        
        # 转换画布坐标
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        self.selection_end = (x, y)
        
        # 更新选择信息
        self.update_selection_info()
    
    def on_right_mouse_press(self, event):
        """右键按下事件 - 开始拖拽图片"""
        self.canvas.scan_mark(event.x, event.y)
        self.is_dragging = True
        self.canvas.config(cursor="fleur")  # 改变鼠标指针为移动样式
    
    def on_right_mouse_drag(self, event):
        """右键拖拽事件 - 移动图片"""
        if not self.is_dragging:
            return
        
        # 使用scan_dragto方法移动画布视图
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def on_right_mouse_release(self, event):
        """右键释放事件 - 结束拖拽"""
        self.is_dragging = False
        self.canvas.config(cursor="")  # 恢复默认鼠标指针
    
    def on_mouse_wheel(self, event):
        """鼠标滚轮事件 - 缩放图片"""
        if not self.current_image:
            return
        
        # 获取滚轮方向
        if event.delta:
            # Windows
            delta = event.delta
        elif event.num == 4:
            # Linux 向上滚动
            delta = 120
        elif event.num == 5:
            # Linux 向下滚动
            delta = -120
        else:
            return
        
        # 计算缩放因子
        scale_factor = 1.1 if delta > 0 else 0.9
        
        # 获取鼠标在画布上的位置
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # 缩放画布内容
        self.canvas.scale("all", x, y, scale_factor, scale_factor)
        
        # 更新滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def update_selection_info(self):
        """更新选择信息显示"""
        if not self.selection_start or not self.selection_end:
            self.selection_info.config(text="未选择区域")
            return
        
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # 确保坐标顺序正确
        left = int(min(x1, x2))
        top = int(min(y1, y2))
        right = int(max(x1, x2))
        bottom = int(max(y1, y2))
        
        width = right - left
        height = bottom - top
        
        info_text = f"区域: ({left}, {top}) - ({right}, {bottom})\n尺寸: {width} x {height}"
        self.selection_info.config(text=info_text)
    
    def on_template_name_changed(self, event=None):
        """模板名称选择改变事件"""
        selected_name = self.template_name_var.get()
        if selected_name == "custom_template":
            self.custom_name_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.custom_name_frame.pack_forget()
    
    def save_template(self):
        """保存当前选择为模板"""
        if not self.current_image or not self.selection_start or not self.selection_end:
            messagebox.showwarning("警告", "请先选择一个区域")
            return
        
        template_name = self.template_name_var.get().strip()
        if not template_name:
            messagebox.showwarning("警告", "请选择模板名称")
            return
        
        # 如果选择了自定义模板，使用自定义名称
        if template_name == "custom_template":
            custom_name = self.custom_name_var.get().strip()
            if not custom_name:
                messagebox.showwarning("警告", "请输入自定义模板名称")
                return
            template_name = custom_name
        
        try:
            x1, y1 = self.selection_start
            x2, y2 = self.selection_end
            
            # 确保坐标顺序正确
            left = int(min(x1, x2))
            top = int(min(y1, y2))
            right = int(max(x1, x2))
            bottom = int(max(y1, y2))
            
            # 检查区域大小
            if right - left < 10 or bottom - top < 10:
                messagebox.showwarning("警告", "选择区域太小，请选择更大的区域")
                return
            
            # 裁剪图像
            template_image = self.current_image.crop((left, top, right, bottom))
            
            # 保存模板文件
            template_filename = f"{template_name}.png"
            template_path = os.path.join(self.templates_dir, template_filename)
            
            # 确保模板目录存在
            os.makedirs(self.templates_dir, exist_ok=True)
            
            template_image.save(template_path)
            
            # 记录模板信息
            template_info = {
                "name": template_name,
                "type": self.template_type_var.get(),
                "description": self.template_desc_var.get(),
                "filename": template_filename,
                "size": f"{right - left}x{bottom - top}",
                "coordinates": {
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom
                },
                "source_screenshot": os.path.basename(self.current_image_path),
                "created_time": datetime.now().isoformat()
            }
            
            self.templates.append(template_info)
            
            # 更新模板列表显示
            self.update_templates_list()
            
            # 清空输入框
            self.template_name_var.set("")
            self.template_desc_var.set("")
            self.custom_name_var.set("")
            self.custom_name_frame.pack_forget()
            
            messagebox.showinfo("成功", f"模板 '{template_name}' 已保存到 {template_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存模板失败: {e}")
    
    def update_templates_list(self):
        """更新模板列表显示"""
        # 清空列表
        for item in self.templates_tree.get_children():
            self.templates_tree.delete(item)
        
        # 添加模板项
        for template in self.templates:
            self.templates_tree.insert("", tk.END, 
                                     text=template["name"],
                                     values=(template["type"], template["size"]))
    
    def export_templates(self):
        """导出模板信息"""
        if not self.templates:
            messagebox.showwarning("警告", "没有模板可导出")
            return
        
        try:
            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                title="导出模板信息",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.templates, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"模板信息已导出到 {file_path}")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")
    
    def clear_selection(self):
        """清除选择"""
        self.selection_start = None
        self.selection_end = None
        
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        
        self.update_selection_info()
    
    def run(self):
        """运行应用"""
        self.root.mainloop()

def main():
    """主函数"""
    app = TemplateMaker()
    app.run()

if __name__ == "__main__":
    main()