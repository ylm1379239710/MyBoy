import sys
import tkinter as tk
from tkinter import ttk, messagebox,colorchooser
from PIL import Image, ImageTk
import threading
import time
import random
from datetime import datetime, timedelta
import calendar  # 用于计算每月天数
import json
from pystray import MenuItem as item, Menu, Icon
import os


class MyBoy:
    def __init__(self, root):
        # 窗口基础设置（全透明背景）
        self.root = root
        self.root.iconbitmap('images/icon.ico')  # 添加窗口图标
        self.root.title("MyBoy")
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes("-topmost", True)  # 置顶
        self.root.wm_attributes("-transparentcolor", "#000000")  # 黑色透明
        self.root.configure(bg="#000000")
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 初始位置设置为屏幕中央
        window_width = 200  # 估计窗口宽度
        window_height = 250  # 估计窗口高度
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"+{x_position}+{y_position}")

        # 核心配置参数
        self.dialog_width = 150
        self.dialog_height = 100
        self.scale_factor = 0.25  # 缩放比例（0.2=20%原尺寸）
        self.countdown_interval = 1  # 倒计时切换秒数（改为1秒）
        self.cartoon_font = ("Comic Sans MS", 8)  # 卡通字体
        self.colors = {
            "bg_light": "#FFF0F3",  # 浅粉背景
            "accent": "#FF9AA2",  # 强调粉
            "text": "#6B4226",  # 文字
            "text_light": "#F86D84"  # 浅色文字
        }
        # 添加托盘图标功能
        self.tray_icon = None
        self.setup_tray_icon()  # 替换为你的图标路径
        self.root.protocol('WM_DELETE_WINDOW', self.quit_app)

        # 新增人生模拟器属性 - 改为六维属性
        self.character_name = "小男孩"  # 角色姓名
        self.strength = 0  # 力量
        self.dexterity = 0  # 敏捷
        self.constitution = 0  # 体质
        self.intelligence = 0  # 智力
        self.wisdom = 0  # 感知
        self.charisma = 0  # 魅力
        self.life_stage = "学龄前"  # 人生阶段
        self.previous_life_stage = "学龄前"  # 上一人生阶段（用于检测变化）
        self.current_career = "无"  # 当前职业
        self.attr_descriptions = {
            'strength': '力量',
            'dexterity': '敏捷',
            'constitution': '体质',
            'intelligence': '智力',
            'wisdom': '感知',
            'charisma': '魅力'
        }

        # 男孩状态
        self.mood = 100  # 心情值(0-100)
        self.energy = 100  # 能量值(0-100)
        self.hunger = 100  # 饱腹度(0-100)
        self.thirst = 100  # 饥渴度(0-100)

        # 新增等级养成系统属性
        self.level = 1  # 等级
        self.img_level = 1  # 当前形态等级（对应图片）
        self.exp = 0  # 当前经验值
        self.exp_to_next = 150  # 升级所需经验
        self.money = 100  # 初始金钱
        self.current_career = "无"  # 当前职业

        # 初始化道具系统
        self.items = {}
        # 加载配置文件
        self.career_config = None
        self.items_config = None
        self.study_config = None
        self.work_config = None
        self.exercise_config = None
        self.load_career_config()
        self.load_items_config()
        self.load_study_config()
        self.load_work_config()
        self.load_exercise_config()
        self.load_play_config()

        self.is_moving = False  # 移动模式
        self.countdowns = []  # 倒计时列表
        self.animation_speed = 50
        self.dialog_visible = False  # 添加对话框状态标记

        # 添加变量以发工资
        self.last_salary_time = None # 记录上次发工资的时间
        # 设置工资定时器
        self.setup_career_salary_timer()

        # 加载图像（替换为你的图片路径）
        self.images = self.load_images()
        self.current_frame = 0  # 当前动画帧

        # 创建界面
        self.create_widgets()

        # 绑定事件
        self.bind_events()

        # 新增配置属性
        self.custom_settings = {
            'colors': self.colors.copy(),
            'font': self.cartoon_font,
            'countdowns': []
        }

        # 检查是否首次启动，如果是则显示出生窗口
        is_first_time = not os.path.exists('configs/settings.json')
        if is_first_time:
            # 隐藏主窗口直到出生设置完成
            # self.root.withdraw()
            self.show_birth_window()
            # 出生设置完成后，启动后台线程
            self.start_background_threads()
        else:
            # 加载保存的设置
            self.load_settings()
            # 启动后台线程
            self.start_background_threads()
        self.setup()

    def setup(self):
        # 新增：程序启动时自动开始倒计时更新
        if self.countdowns:
            self.root.after(self.countdown_interval * 1000, self.update_countdowns)

    def load_settings(self):
        """加载保存的设置"""
        try:
            with open('configs/settings.json', 'r', encoding='utf-8') as f:
                saved = json.load(f)
                if 'last_salary_time' in saved and saved['last_salary_time'] is not None:
                    self.last_salary_time = datetime.strptime(saved['last_salary_time'], '%Y-%m-%d %H:%M:%S')
                else:
                    self.last_salary_time = None
                if 'colors' in saved:
                    self.colors.update(saved['colors'])
                # 恢复字体设置
                self.cartoon_font = tuple(saved.get('font', self.cartoon_font))
                # 完全重建倒计时对象
                self.countdowns = []
                for cd in saved.get('countdowns', []):
                    try:
                        new_cd = {
                            'name': cd['name'],
                            'end_time': datetime.strptime(cd['end_time'], '%Y-%m-%d %H:%M:%S'),
                            'repeat': cd['repeat'],
                            'active': cd.get('active', True),  # 添加默认值
                            'set_time': datetime.strptime(cd.get('set_time', cd['end_time']), '%Y-%m-%d %H:%M:%S')
                        }
                        # 自动激活未过期的倒计时
                        if new_cd['end_time'] > datetime.now() or new_cd['repeat'] != "不重复":
                            self.countdowns.append(new_cd)
                    except KeyError as e:
                        print(f"加载倒计时出错：缺失字段 {e}")

                # 加载养成系统数据
                if 'pet_data' in saved:
                    pet_data = saved['pet_data']
                    self.level = pet_data.get('level', 1)
                    self.exp = pet_data.get('exp', 0)
                    self.exp_to_next = pet_data.get('exp_to_next', 100)
                    self.money = pet_data.get('money', 100)
                    self.items = pet_data.get('items', {})
                    self.mood = pet_data.get('mood', 100)
                    self.energy = pet_data.get('energy', 100)
                    self.img_level = pet_data.get('img_level', 1)
                    self.hunger = pet_data.get('hunger', 100)
                    self.thirst = pet_data.get('thirst', 100)

                # 加载角色属性数据
                if 'character_data' in saved:
                    char_data = saved['character_data']
                    self.character_name = char_data.get('character_name', '小男孩')
                    self.strength = char_data.get('strength', 5)
                    self.dexterity = char_data.get('dexterity', 5)
                    self.constitution = char_data.get('constitution', 5)
                    self.intelligence = char_data.get('intelligence', 5)
                    self.wisdom = char_data.get('wisdom', 5)
                    self.charisma = char_data.get('charisma', 5)
                    self.life_stage = char_data.get('life_stage', '童年')
                    self.current_career = char_data.get('current_career', '无')

                self.update_ui_style()
        except FileNotFoundError:
            pass

    def load_images(self):
        """加载并缩放男孩图像"""
        image_files = [
            "images/1.gif",  # 娃娃
            "images/2.gif",  # 儿童
            "images/3.gif",  # 小学生
            "images/4.gif",  # 少年
            "images/5.gif"  # 成年
        ]

        # 创建一个字典，按等级存储图片帧
        images_by_level = {}
        for level, file in enumerate(image_files, start=1):
            frames = []
            try:
                img = Image.open(file)
                # 获取原始尺寸并应用缩放因子
                width, height = img.size
                new_width = int(width * self.scale_factor)
                new_height = int(height * self.scale_factor)

                while True:
                    # 复制当前帧并应用缩放
                    frame = img.copy()
                    frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    tk_frame = ImageTk.PhotoImage(frame)
                    frames.append(tk_frame)
                    try:
                        img.seek(len(frames))  # 跳到下一帧
                    except EOFError:
                        break
            except Exception as e:
                print(f"加载图片{file}出错: {e}")
            images_by_level[level] = frames

        return images_by_level

    def create_widgets(self):
        """创建卡通风格界面元素"""
        # 主容器（透明背景）
        self.main_frame = tk.Frame(self.root, bg="#000000")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        # 配置网格权重，使单元格能够扩展
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        # 对话框背景（调整尺寸为男孩图片的80%宽度）
        self.dialog_canvas = tk.Canvas(
            self.main_frame,
            width=self.dialog_width,
            height=75,  # 固定高度
            bg="#000000",
            highlightthickness=0
        )

        # 加载并缩放对话框图片（保持宽高比）
        dialog_img = Image.open("images/dialog.png").convert("RGBA")
        dialog_img = dialog_img.resize((self.dialog_width, self.dialog_height), Image.Resampling.LANCZOS)
        self.dialog_img = ImageTk.PhotoImage(dialog_img)
        self.dialog_canvas.create_image(0, 0, anchor=tk.NW, image=self.dialog_img)
        self.dialog_canvas.grid(row=0, column=0, sticky="nw")
        # 初始化时将对话框添加到布局，但默认隐藏
        self.dialog_canvas.grid_remove()
        self.dialog_visible = False

        if not self.countdowns:
            countdowns_text = "还没有设置倒计时哦～"
        # 调整文字位置到对话框中央
        self.countdown_text = self.dialog_canvas.create_text(
            self.dialog_width // 2, 68,  # 水平居中，上移位置
            text=countdowns_text,
            font=(self.cartoon_font[0], self.cartoon_font[1]),  # 缩小字号
            fill=self.colors["text"],
            anchor=tk.CENTER,
        )

        self.status_text = self.dialog_canvas.create_text(
            self.dialog_width // 2, 34,  # 水平居中，下移位置
            text="心情: 100%  能量: 100% \n 饱腹: 100%  饥渴: 100%",
            font=(self.cartoon_font[0], self.cartoon_font[1]),
            fill=self.colors["text_light"],
            anchor=tk.CENTER
        )

        self.level_text = self.dialog_canvas.create_text(
            self.dialog_width // 2, 10,  # 位置在状态文本下方
            text=f"等级: {self.level} 经验: {self.exp}/{self.exp_to_next}",
            font=(self.cartoon_font[0], self.cartoon_font[1]),
            fill=self.colors["text_light"],
            anchor=tk.CENTER
        )

        self.money_text = self.dialog_canvas.create_text(
            self.dialog_width // 2, 55,  #
            text=f"金钱: {self.money}",
            font=(self.cartoon_font[0], self.cartoon_font[1]),
            fill=self.colors["text_light"],
            anchor=tk.CENTER
        )

        self.boy_label = tk.Label(
            self.main_frame,
            image=self.images[self.img_level][self.current_frame],
            bg="#000000"
        )
        # 记录男孩的初始位置
        self.boy_label.grid(row=1, column=0, sticky="nw")

        self.setup_menu()
    def setup_menu(self):
        # 右键卡通菜单（保持原有代码不变）
        self.menu = tk.Menu(
            self.root,
            tearoff=0,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            activebackground=self.colors["accent"]
        )
        self.menu.add_command(label="移动男孩", command=self.toggle_move)
        self.menu.add_command(label="面板", command=self.show_character_window)
        self.menu.add_separator()
        self.menu.add_command(label="工作", command=self.job)
        self.menu.add_command(label="零工", command=self.work)
        self.menu.add_command(label="学习", command=self.study)
        self.menu.add_command(label="运动", command=self.exercise)
        self.menu.add_command(label="玩耍", command=self.play)
        self.menu.add_command(label="休息", command=self.rest)

        self.menu.add_separator()
        self.menu.add_command(label="投喂", command=self.show_items_window)
        self.menu.add_command(label="打开商店", command=self.open_shop)
        self.menu.add_separator()

        self.menu.add_command(label="设置倒计时", command=self.set_countdown)
        self.menu.add_command(label="查看倒计时", command=self.view_countdowns)
        self.menu.add_separator()

        self.menu.add_command(label="个性化设置", command=self.open_settings)
        self.menu.add_command(label="隐藏", command=self.hide_to_tray)
        self.menu.add_command(label="退出", command=self.quit_app)

    def bind_events(self):
        """绑定鼠标交互事件"""
        self.boy_label.bind("<Button-1>", self.on_click)
        self.boy_label.bind("<Button-3>", self.show_menu)
        self.boy_label.bind("<B1-Motion>", self.on_drag)
        self.boy_label.bind("<ButtonRelease-1>", self.on_release)
        self.main_frame.bind("<Enter>", self.show_dialog)  # 添加鼠标进入事件
        self.main_frame.bind("<Leave>", self.hide_dialog)  # 添加鼠标离开事件
        # 拖拽坐标记录
        self.drag_x = 0
        self.drag_y = 0

    def start_background_threads(self):
        """启动后台状态更新线程"""
        self.status_thread = threading.Thread(target=self.update_status, daemon=True)
        self.status_thread.start()
        self.animate()  # 启动动画

    # 交互功能
    def on_click(self, event):
        """左键点击互动"""
        if not self.is_moving:
            self.drag_x = event.x
            self.drag_y = event.y
            self.mood = min(100, self.mood + random.randint(2, 5))
            self.update_status_display()

    def show_menu(self, event):
        """显示右键菜单"""
        self.menu.post(event.x_root, event.y_root)

    def on_drag(self, event):
        """拖拽移动窗口"""
        if self.is_moving:
            x = self.root.winfo_x() + event.x - self.drag_x
            y = self.root.winfo_y() + event.y - self.drag_y
            self.root.geometry(f"+{x}+{y}")

    def on_release(self, event):
        """释放鼠标"""
        pass

    def toggle_move(self):
        """切换移动模式"""
        self.is_moving = not self.is_moving
        # 修改提示文字和菜单项文字
        msg = "可以拖动男孩啦～" if self.is_moving else "男孩不可以拖动了~"
        menu_text = "锁定男孩" if self.is_moving else "移动男孩"
        self.show_cute_message("提示", msg)
        self.root.config(cursor="fleur" if self.is_moving else "")
        # 更新菜单项文字
        self.menu.entryconfig(0, label=menu_text)

    # 倒计时功能（支持重复）
    def set_countdown(self):
        """设置带重复周期的倒计时"""
        name = self.show_cute_input("倒计时名称", "给倒计时起个名字吧～")
        if not name:
            return

        # 创建时间选择窗口
        time_win = tk.Toplevel(self.root)
        time_win.title("设置倒计时")
        time_win.geometry("380x400")
        time_win.configure(bg=self.colors["bg_light"])
        time_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        time_win.transient(self.root)
        time_win.grab_set()
        self.center_window(time_win)
        self.style_window(time_win)

        # 标题
        tk.Label(
            time_win,
            text="⏰ 设置提醒时间 ⏰",
            font=(self.cartoon_font[0], 12, "bold"),
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        ).pack(pady=15)

        frame = tk.Frame(time_win, bg=self.colors["bg_light"])
        frame.pack(padx=20, pady=10)

        # 日期选择框架（可隐藏）
        date_frame = tk.Frame(frame, bg=self.colors["bg_light"])
        date_frame.grid(row=0, column=0, columnspan=4, sticky="w", pady=5)

        now = datetime.now()
        year_var = tk.IntVar(value=now.year)
        month_var = tk.IntVar(value=now.month)
        day_var = tk.IntVar(value=now.day)

        # 日期选择组件
        tk.Label(date_frame, text="日期:", font=self.cartoon_font,
                 bg=self.colors["bg_light"], fg=self.colors["text"]).grid(row=0, column=0, padx=5, sticky="w")

        ttk.Combobox(date_frame, textvariable=year_var, values=[now.year, now.year + 1],
                     width=6, font=self.cartoon_font).grid(row=0, column=1, padx=2)
        ttk.Combobox(date_frame, textvariable=month_var, values=list(range(1, 13)),
                     width=4, font=self.cartoon_font).grid(row=0, column=2, padx=2)
        ttk.Combobox(date_frame, textvariable=day_var, values=list(range(1, 32)),
                     width=4, font=self.cartoon_font).grid(row=0, column=3, padx=2)

        # 时间选择
        tk.Label(frame, text="时间:", font=self.cartoon_font,
                 bg=self.colors["bg_light"], fg=self.colors["text"]).grid(row=1, column=0, pady=5, sticky="w")

        hour_var = tk.IntVar(value=now.hour)
        minute_var = tk.IntVar(value=now.minute)

        ttk.Combobox(frame, textvariable=hour_var, values=list(range(0, 24)),
                     width=4, font=self.cartoon_font).grid(row=1, column=1)
        tk.Label(frame, text=":", bg=self.colors["bg_light"]).grid(row=1, column=2)
        ttk.Combobox(frame, textvariable=minute_var, values=[i for i in range(0, 60) if i % 5 == 0],
                     width=4, font=self.cartoon_font).grid(row=1, column=3)

        # 重复周期设置
        repeat_var = tk.StringVar(value="不重复")
        tk.Label(frame, text="重复:", font=self.cartoon_font,
                 bg=self.colors["bg_light"], fg=self.colors["text"]).grid(row=2, column=0, pady=15, sticky="w")
        ttk.Combobox(frame, textvariable=repeat_var, values=["不重复", "每天", "每周", "每月"],
                     width=10, font=self.cartoon_font).grid(row=2, column=1, columnspan=3, sticky="w")

        # 动态显示日期选择
        def update_date_visibility(*args):
            if repeat_var.get() == "不重复":
                date_frame.grid()
            else:
                date_frame.grid_remove()

        repeat_var.trace("w", update_date_visibility)
        update_date_visibility()  # 初始调用

        # 错误提示
        error_label = tk.Label(
            time_win,
            text="",
            fg="#FF6347",
            bg=self.colors["bg_light"],
            font=self.cartoon_font
        )
        error_label.pack(pady=5)

        # 确认按钮逻辑
        def confirm():
            try:
                repeat = repeat_var.get()
                hour = hour_var.get()
                minute = minute_var.get()

                # 处理不同重复类型
                if repeat == "不重复":
                    year = year_var.get()
                    month = month_var.get()
                    day = day_var.get()
                    target_time = datetime(year, month, day, hour, minute)
                else:
                    # 基于当前时间计算下一次触发
                    now = datetime.now()
                    target_time = datetime(now.year, now.month, now.day, hour, minute)

                    # 如果已经过了当天时间，调整到下一个周期
                    if target_time < now:
                        if repeat == "每天":
                            target_time += timedelta(days=1)
                        elif repeat == "每周":
                            target_time += timedelta(weeks=1)
                        elif repeat == "每月":
                            # 处理跨月逻辑
                            try:
                                target_time = target_time.replace(month=target_time.month + 1)
                            except ValueError:  # 12月+1的情况
                                target_time = target_time.replace(year=target_time.year + 1, month=1)
                            # 确保日期有效
                            while True:
                                try:
                                    target_time.replace(day=day_var.get())
                                    break
                                except ValueError:
                                    target_time -= timedelta(days=1)

                # 验证时间有效性
                if target_time <= datetime.now():
                    raise ValueError("请选择未来的时间哦～")

                # 添加到倒计时列表（新增set_time字段）
                self.countdowns.append({
                    "name": name,
                    "end_time": target_time,
                    "repeat": repeat,
                    "active": True,
                    "set_time": datetime.now()  # 添加设置时间用于进度计算
                })
                self.save_settings()  # 新增保存

                # 启动倒计时更新循环（替换线程启动逻辑）
                self.update_countdowns()

                self.show_cute_message("成功",
                                       f"{name} 设置成功！\n时间: {target_time.strftime('%m-%d %H:%M')}\n重复: {repeat}")
                time_win.destroy()

            except Exception as e:
                error_label.config(text=str(e))

        # 按钮区域
        btn_frame = tk.Frame(time_win, bg=self.colors["bg_light"])
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="确认",
            command=confirm,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"],
            padx=15
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="取消",
            command=time_win.destroy,
            font=self.cartoon_font,
            bg="#B0E2FF",
            fg=self.colors["text"],
            padx=15
        ).pack(side=tk.LEFT, padx=10)

    def view_countdowns(self):
        """查看所有倒计时"""
        if not self.countdowns:
            self.show_cute_message("提示", "还没有设置倒计时哦～")
            return

        # 创建倒计时列表窗口
        cd_win = tk.Toplevel(self.root)
        cd_win.title("我的倒计时")
        cd_win.geometry("450x350")
        cd_win.configure(bg="#FFF8DC")
        cd_win.wm_attributes('-topmost', True)  # 设置窗口置顶

        cd_win.transient(self.root)
        cd_win.grab_set()
        self.center_window(cd_win)  # 居中显示窗口
        self.style_window(cd_win)

        # 标题
        tk.Label(
            cd_win,
            text="📋 倒计时列表",
            font=(self.cartoon_font[0], 12, "bold"),
            bg="#FFF8DC",
            fg=self.colors["text"]
        ).pack(pady=10)

        # 列表框和滚动条
        frame = tk.Frame(cd_win, bg="#FFF8DC")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            width=50,
            height=10,
            font=self.cartoon_font,
            bg="#FFFFF0",
            fg=self.colors["text"],
            selectbackground="#FFE4B5",
            relief=tk.FLAT
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # 填充列表
        for i, cd in enumerate(self.countdowns):
            if cd["active"]:
                remaining = cd["end_time"] - datetime.now()
                days = remaining.days
                hours, rem = divmod(remaining.seconds, 3600)
                mins, secs = divmod(rem, 60)

                time_str = f"{days}天{hours}时{mins}分" if days > 0 else f"{hours}时{mins}分{secs}秒"
                repeat_tag = f"【{cd['repeat']}】" if cd['repeat'] != "不重复" else ""
                listbox.insert(tk.END, f"{i + 1}. {cd['name']} {repeat_tag}: {time_str}")
            else:
                listbox.insert(tk.END, f"{i + 1}. {cd['name']}: 已结束")

        # 按钮区域
        btn_frame = tk.Frame(cd_win, bg="#FFF8DC")
        btn_frame.pack(pady=15)


        def cancel_selected():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                if 0 <= idx < len(self.countdowns):
                    self.countdowns[idx]["active"] = False
                    self.show_cute_message("提示", f"已取消 {self.countdowns[idx]['name']}")
                    cd_win.destroy()

        tk.Button(
            btn_frame,
            text="取消选中项",
            command=cancel_selected,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"],
            padx=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="添加新倒计时",
            command=lambda: [cd_win.destroy(), self.set_countdown()],
            font=self.cartoon_font,
            bg="#B0E2FF",
            fg=self.colors["text"],
            padx=10
        ).pack(side=tk.LEFT, padx=10)

    def update_countdowns(self):
        """更新倒计时并处理重复逻辑（支持轮流显示）"""
        now = datetime.now()
        active_cds = [cd for cd in self.countdowns if cd["active"]]

        # 检查是否有活跃的倒计时
        if not active_cds:
            # 如果没有活跃的倒计时，清空显示并返回
            self.dialog_canvas.itemconfig(self.countdown_text, text="")
            return

        # 初始化索引和显示计数器
        if not hasattr(self, '_current_cd_index') or self._current_cd_index >= len(active_cds):
            self._current_cd_index = 0

        # 添加显示计数器，用于控制每个倒计时显示的时长
        if not hasattr(self, '_cd_display_counter'):
            self._cd_display_counter = 0

        # 每显示5次（约15秒）才切换到下一个倒计时
        if self._cd_display_counter >= 5:
            self._current_cd_index = (self._current_cd_index + 1) % len(active_cds)
            self._cd_display_counter = 0

        current_cd = active_cds[self._current_cd_index]
        remaining = current_cd["end_time"] - now

        # 处理到期逻辑
        if remaining.total_seconds() <= 0:
            self.show_cute_message("时间到啦～", f"{current_cd['name']} 的时间到咯！")

            # 更新重复逻辑（保持原有代码结构）
            if current_cd["repeat"] == "每天":
                current_cd["end_time"] += timedelta(days=1)
                self.save_settings()  # 新增保存
            elif current_cd["repeat"] == "每周":
                current_cd["end_time"] += timedelta(weeks=1)
                self.save_settings()  # 新增保存
            elif current_cd["repeat"] == "每月":
                year = current_cd["end_time"].year
                month = current_cd["end_time"].month
                days_in_month = calendar.monthrange(year, month)[1]
                current_cd["end_time"] += timedelta(days=days_in_month)
                self.save_settings()  # 新增保存
            else:
                current_cd["active"] = False

            # 重置索引防止越界
            self._current_cd_index = 0
            self._cd_display_counter = 0

        # 统一时间显示格式（补零+包含秒数）
        days = remaining.days
        hours, rem = divmod(abs(remaining.seconds), 3600)
        mins, secs = divmod(rem, 60)
        time_str = f"{days}天{hours:02}时{mins:02}分" if days > 0 else \
            f"{hours:02}时{mins:02}分{secs:02}秒"

        # 修改文本更新方式
        countdown_info = f"{self._current_cd_index + 1}/{len(active_cds)} {current_cd['name']}: {time_str}"
        self.dialog_canvas.itemconfig(self.countdown_text, text=countdown_info)

        # 递增显示计数器
        self._cd_display_counter += 1

        # 统一更新间隔为3秒
        self.root.after(3000, self.update_countdowns)

    # 状态更新与动画
    def update_status(self):
        """更新男孩状态（心情/能量）"""
        counter = 0
        while True:
            # 减慢心情和能量降低速度
            self.mood = max(0, self.mood - 0.02)
            self.energy = max(0, self.energy - 0.015)
            # 添加饱腹度和饥渴度的自动下降
            self.hunger = max(0, self.hunger - 0.025)
            self.thirst = max(0, self.thirst - 0.025)

            # 低状态时影响心情
            if self.hunger < 30 and self.thirst < 20:
                self.mood = max(0, self.mood - 0.08)  # 饥饿时心情下降加快
            if self.hunger < 30:
                self.mood = max(0, self.mood - 0.05)  # 饥饿时心情下降加快
            if self.thirst < 20:
                self.mood = max(0, self.mood - 0.05)  # 口渴时心情下降更快

            # 每30秒自动保存一次
            counter += 1
            if counter >= 30:
                self.save_settings()
                counter = 0
            self.update_status_display()
            time.sleep(1)

    def update_status_display(self):
        """更新状态标签显示"""
        self.dialog_canvas.itemconfig(
            self.status_text,
            text=f"心情: {int(self.mood)}   能量：{int(self.energy)}\n饱腹: {int(self.hunger)}   饥渴: {int(self.thirst)}"
        )

        # 更新等级和经验显示
        self.dialog_canvas.itemconfig(
            self.level_text,
            text=f"等级: {self.level}   经验: {self.exp}/{self.exp_to_next}"
        )

        # 更新金钱显示
        self.dialog_canvas.itemconfig(
            self.money_text,
            text=f"金钱: {self.money}"
        )
    # 人物动画更新
    def animate(self):
        current_images = self.images.get(self.img_level, [])
        if current_images and len(current_images) > self.current_frame:
            self.boy_label.config(image=current_images[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(current_images)
        else:
            self.current_frame = 0
        self.root.after(self.animation_speed, self.animate)

    # 辅助功能
    def style_window(self, window):
        """统一设置窗口风格"""
        # 设置窗口图标（可选）
        try:
            window.iconbitmap(default="images/icon.ico")
        except:
            pass
        # 调整按钮风格
        style = ttk.Style()
        style.configure("TCombobox", font=self.cartoon_font)

    def center_window(self, window):
        """将窗口显示在屏幕正中间"""
        window.update_idletasks()  # 确保窗口尺寸已计算
        width = window.winfo_width()
        height = window.winfo_height()

        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # 计算居中位置
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # 设置窗口位置
        window.geometry(f"+{x}+{y}")

    def show_cute_message(self, title, message):
        """卡通风格消息框，显示在屏幕正中间"""
        msg_win = tk.Toplevel(self.root)
        msg_win.title(title)
        msg_win.geometry("250x150")
        msg_win.configure(bg=self.colors["bg_light"])
        msg_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        self.center_window(msg_win)  # 居中显示
        self.style_window(msg_win)

        tk.Label(
            msg_win,
            text=message,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            wraplength=200,
            justify="center"
        ).pack(expand=True, padx=10, pady=10)

        tk.Button(
            msg_win,
            text="好的",
            command=msg_win.destroy,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"],
            padx=10
        ).pack(pady=10)

    def show_cute_input(self, title, prompt):
        """卡通风格输入框，显示在屏幕正中间"""
        input_win = tk.Toplevel(self.root)
        input_win.title(title)
        input_win.geometry("250x150")
        input_win.configure(bg=self.colors["bg_light"])
        input_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        input_win.transient(self.root)
        input_win.grab_set()
        self.center_window(input_win)  # 居中显示
        self.style_window(input_win)

        tk.Label(
            input_win,
            text=prompt,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        ).pack(padx=10, pady=10)

        entry = tk.Entry(
            input_win,
            font=self.cartoon_font,
            width=25,
            bg="white",
            fg=self.colors["text"]
        )
        entry.pack(pady=5)
        entry.focus()

        result = [None]  # 用列表存储结果

        def confirm():
            result[0] = entry.get()
            input_win.destroy()

        btn_frame = tk.Frame(input_win, bg=self.colors["bg_light"])
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="确认",
            command=confirm,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"],
            padx=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="取消",
            command=input_win.destroy,
            font=self.cartoon_font,
            bg="#B0E2FF",
            fg=self.colors["text"],
            padx=10
        ).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(input_win)
        return result[0]

    def quit_app(self):
        """退出程序"""
        self.save_settings()
        if messagebox.askyesno(
                "退出",
                "真的要和男孩说再见吗？",
                icon="question"
        ):
            self.stop_voice_engine()
            self.root.destroy()
            os._exit(0)
    def open_settings(self):
        """打开个性化设置窗口"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("个性化设置")
        settings_win.geometry("300x400")
        settings_win.configure(bg=self.colors["bg_light"])
        settings_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        settings_win.transient(self.root)
        self.center_window(settings_win)

        # 颜色选择部分
        color_labels = {
            "bg_light": "背景颜色",
            "accent": "强调按钮颜色",
            "text": "整体文字颜色",
            "text_light": "状态文字颜色"
        }

        tk.Label(settings_win, text="界面颜色设置", font=(self.cartoon_font[0], 12, "bold"),
                 bg=self.colors["bg_light"]).pack(pady=10)

        # 创建颜色选择项时添加标记
        for color_key in ["bg_light", "accent", "text", "text_light"]:
            frame = tk.Frame(settings_win, bg=self.colors["bg_light"])
            tk.Label(frame, text=color_labels[color_key],
                     font=self.cartoon_font, bg=self.colors["bg_light"]).pack(side=tk.LEFT)
            btn = tk.Button(frame, bg=self.colors[color_key], width=3,
                            command=lambda ck=color_key: self.choose_color(ck))
            btn._is_color_btn = True  # 标记为颜色按钮
            btn._color_name = color_key  # 存储对应的颜色键
            btn.pack(side=tk.RIGHT)
            frame.pack(fill=tk.X, padx=10, pady=2)

        # 字体设置部分
        tk.Label(settings_win, text="字体设置", font=(self.cartoon_font[0], 12, "bold"),
                 bg=self.colors["bg_light"]).pack(pady=10)

        font_frame = tk.Frame(settings_win, bg=self.colors["bg_light"])
        tk.Button(font_frame, text="选择字体样式", command=self.choose_font,
                  font=self.cartoon_font).pack(pady=5)
        tk.Label(font_frame, text=f"当前字体: {self.cartoon_font[0]} {self.cartoon_font[1]}号",
                 bg=self.colors["bg_light"]).pack()
        font_frame.pack()

        # 操作按钮
        btn_frame = tk.Frame(settings_win, bg=self.colors["bg_light"])
        tk.Button(btn_frame, text="❌ 关闭", command=settings_win.destroy,
                  font=self.cartoon_font).pack(pady=5)
        btn_frame.pack(pady=15, fill=tk.X, padx=20)

    def choose_color(self, color_name):
        """选择颜色"""
        new_color = colorchooser.askcolor(title=f"选择{color_name}颜色")[1]
        if new_color:
            self.colors[color_name] = new_color
            self.update_ui_style()

    def choose_color(self, color_name):
        """选择颜色"""
        new_color = colorchooser.askcolor(title=f"选择{color_name}颜色")[1]
        if new_color:
            self.colors[color_name] = new_color
            self.update_ui_style()
            self.save_settings()  # 新增自动保存

    def choose_font(self):
        """选择字体"""
        # 创建字体选择对话框
        font_win = tk.Toplevel(self.root)
        font_win.title("选择字体")
        font_win.configure(bg=self.colors["bg_light"])
        font_win.wm_attributes('-topmost', True)  # 设置窗口置顶

        # 获取所有可用字体
        fonts = list(tk.font.families())
        fonts.sort()

        # 创建字体选择组件
        frame = tk.Frame(font_win, bg=self.colors["bg_light"])
        frame.pack(padx=10, pady=10)

        # 字体家族选择
        tk.Label(frame, text="字体:", bg=self.colors["bg_light"], fg=self.colors["text"]).grid(row=0, column=0)
        family_var = tk.StringVar(value=self.cartoon_font[0])
        family_cb = ttk.Combobox(frame, textvariable=family_var, values=fonts, width=30)
        family_cb.grid(row=0, column=1, padx=5)

        # 字体大小选择
        tk.Label(frame, text="大小:", bg=self.colors["bg_light"], fg=self.colors["text"]).grid(row=1, column=0)
        size_var = tk.IntVar(value=self.cartoon_font[1])
        size_spin = ttk.Spinbox(frame, from_=8, to=24, textvariable=size_var, width=5)
        size_spin.grid(row=1, column=1, padx=5)

        # 添加预览标签
        sample_label = tk.Label(frame, text="预览文字 ABCabc",
                                bg=self.colors["bg_light"],
                                fg=self.colors["text"])
        sample_label.grid(row=2, columnspan=2, pady=10)

        # 实时预览功能
        def preview_font(*args):
            try:
                sample_label.config(font=(family_var.get(), size_var.get()))
            except tk.TclError:
                pass

        family_var.trace("w", preview_font)
        size_var.trace("w", preview_font)

        # 确认按钮逻辑
        def apply_font():
            self.cartoon_font = (family_var.get(), size_var.get())
            self.update_ui_style()
            # 强制刷新所有控件
            self.root.update_idletasks()
            self.save_settings()
            font_win.destroy()

        btn_frame = tk.Frame(font_win, bg=self.colors["bg_light"])
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="应用", command=apply_font).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=font_win.destroy).pack(side=tk.LEFT)

        # 初始预览
        preview_font()
    def save_settings(self, win=None):
        """保存设置到文件"""
        self.custom_settings.update({
            'last_salary_time': self.last_salary_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_salary_time else None,
            'colors': self.colors,
            'font': self.cartoon_font,
            'countdowns': [
                {
                    'name': cd['name'],
                    'end_time': cd['end_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'repeat': cd['repeat'],
                    'active': cd['active'],
                    'set_time': cd['set_time'].strftime('%Y-%m-%d %H:%M:%S')  # 新增set_time保存
                } for cd in self.countdowns
            ],
            # 养成系统数据，包含新增的饱腹度和饥渴度
            'pet_data': {
                'level': self.level,
                'exp': self.exp,
                'exp_to_next': self.exp_to_next,
                'money': self.money,
                'items': self.items,
                'mood': self.mood,
                'energy': self.energy,
                'img_level': self.img_level,
                'hunger': self.hunger,
                'thirst': self.thirst
            },
            # 角色属性数据
            'character_data': {
                'character_name': self.character_name,
                'strength': self.strength,
                'dexterity': self.dexterity,
                'constitution': self.constitution,
                'intelligence': self.intelligence,
                'wisdom': self.wisdom,
                'charisma': self.charisma,
                'life_stage': self.life_stage,
                'current_career': self.current_career,
            }
        })
        with open('configs/settings.json', 'w', encoding='utf-8') as f:
            json.dump(self.custom_settings, f, ensure_ascii=False)
        if win:
            win.destroy()

    def calculate_progress(self, countdown):
        """计算倒计时进度"""
        total = (countdown['end_time'] - datetime.now()).total_seconds()
        if countdown['repeat'] == "不重复":
            initial = (countdown['end_time'] - countdown['set_time']).total_seconds()
            return 1 - (total / initial)
        return 0.5  # 重复任务默认显示50%进度

    def update_ui_style(self):
        """更新界面样式"""
        # 更新主窗口组件
        self.main_frame.config(bg="#000000")
        self.dialog_canvas.itemconfig(self.countdown_text, fill=self.colors["text"])
        self.dialog_canvas.itemconfig(self.status_text, fill=self.colors["text_light"])
        self.dialog_canvas.itemconfig(self.level_text, fill=self.colors["text_light"])
        self.dialog_canvas.itemconfig(self.money_text, fill=self.colors["text_light"])

        # 更新菜单样式
        self.menu.config(
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            activebackground=self.colors["accent"]
        )

        # 更新所有窗口中的设置界面
        for window in self.root.winfo_children():
            if isinstance(window, tk.Toplevel) and window.title() == "个性化设置":
                # 更新设置窗口背景
                window.config(bg=self.colors["bg_light"])
                # 更新所有子组件
                for widget in window.winfo_children():
                    if isinstance(widget, tk.Frame):
                        widget.config(bg=self.colors["bg_light"])
                        # 更新颜色按钮
                        for child in widget.winfo_children():
                            if hasattr(child, '_is_color_btn'):
                                color_name = getattr(child, '_color_name', 'bg_light')
                                child.config(
                                    bg=self.colors[color_name],
                                    fg=self.colors["text"]
                                )
                            elif isinstance(child, tk.Label):
                                child.config(
                                    bg=self.colors["bg_light"],
                                    fg=self.colors["text"]
                                )

    def show_dialog(self, event=None):
        """在男孩正上方显示对话框"""
        if not self.dialog_visible:
            # 显示对话框（使用grid布局时的显示方式）
            self.dialog_canvas.grid(row=0, column=0, sticky="nw")
            # 将对话框置于顶层，确保覆盖在男孩标签上
            self.dialog_visible = True
            # 确保更新状态显示
            self.update_status_display()

    def hide_dialog(self, event=None):
        """隐藏对话框"""
        if self.dialog_visible:
            # 使用grid_remove而不是place_forget
            self.dialog_canvas.grid_remove()
            self.dialog_visible = False

    def setup_tray_icon(self):
        """创建系统托盘图标"""
        menu = Menu(
            item('显示男孩', self.show_from_tray),
            item('隐藏男孩', self.hide_to_tray),
            Menu.SEPARATOR,
            item('退出', self.quit_app)
        )

        # 使用第一帧图像作为托盘图标
        tray_image = Image.open("images/icon.ico").resize((24, 24))
        self.tray_icon = Icon("cat_icon", tray_image, "桌面男孩", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        """隐藏窗口到系统托盘"""
        self.root.withdraw()
        self.save_settings()
        if self.tray_icon:
            self.tray_icon.visible = True

    def show_from_tray(self):
        """从托盘恢复窗口"""
        self.root.deiconify()

    def quit_app(self):
        """完全退出程序"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
        os._exit(0)

    def add_exp(self, amount):
        """增加经验值并检查是否升级"""
        self.exp += amount

        # 检查是否升级
        while self.exp >= self.exp_to_next:
            self.level_up()

        # 更新显示
        self.update_status_display()
        return self.level

    def level_up(self):
        """升级处理"""
        self.level += 1
        self.exp -= self.exp_to_next

        # 升级所需经验递增（非线性增长）
        self.exp_to_next = int(self.exp_to_next * 1.35)

        # 根据等级更新形态等级
        if self.level < 4:
            self.img_level = 1  # 娃娃
        elif self.level < 7:
            self.img_level = 2  # 儿童
        elif self.level < 13:
            self.img_level = 3  # 小学生
        elif self.level < 16:
            self.img_level = 4  # 少年
        else:
            self.img_level = 5  # 成年
        
        # 升级奖励
        bonus_money = self.level * 10
        self.money += bonus_money

        # 升级效果：恢复部分状态
        self.mood = min(100, self.mood + 20)
        self.energy = min(100, self.energy + 30)

        # 更新人生阶段
        self.update_life_stage()

        # 显示升级信息和人生阶段变化
        stage_info = f"现在是{self.life_stage}！" if hasattr(self, 'previous_life_stage') and self.life_stage != self.previous_life_stage else ""
        self.previous_life_stage = self.life_stage
        self.show_cute_message("升级啦！", f"男孩升级到了{self.level}级！\n获得了{bonus_money}金币奖励！\n{stage_info}")
        self.save_settings()

    def work(self):
        """工作功能 - 消耗能量、饱腹度和饥渴度，获得经验和金钱"""
        # 检查是否有可用的工作配置
        if not self.work_config:
            self.show_cute_message("配置错误", "无法加载零工配置，请检查work_config.json文件！")
            return
        # 获取实际的工作项目（从work_items键下获取）
        work_items = self.work_config.get('work_items', {})
        if not work_items:
            self.show_cute_message("配置错误", "零工配置中找不到work_items项！")
            return

        # 筛选当前等级可用的工作
        available_jobs = {}
        for job_name, job_info in work_items.items():
            min_level = job_info.get('min_level', 1)
            max_level = job_info.get('max_level', 9999)
            if min_level <= self.level <= max_level:
                available_jobs[job_name] = job_info

        if not available_jobs:
            self.show_cute_message("没有可用零工", f"你的等级{self.level}还不能零工，继续成长吧！")
            return

        # 创建工作选择窗口
        work_win = tk.Toplevel(self.root)
        work_win.title("选择零工")
        work_win.geometry("600x400")
        work_win.configure(bg=self.colors["bg_light"])
        work_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        self.center_window(work_win)
        self.style_window(work_win)

        # 工作标题
        tk.Label(
            work_win,
            text="💼 选择要做的零工 💼",
            font=(self.cartoon_font[0], 14, "bold"),
            bg=self.colors["bg_light"]
        ).pack(pady=10)

        # 创建工作列表框架
        jobs_frame = tk.Frame(work_win, bg=self.colors["bg_light"])
        jobs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 创建滚动条
        scrollbar = tk.Scrollbar(jobs_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建列表框来显示工作
        jobs_listbox = tk.Listbox(
            jobs_frame,
            yscrollcommand=scrollbar.set,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            width=40, height=10,
            selectmode=tk.SINGLE
        )
        jobs_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 配置滚动条
        scrollbar.config(command=jobs_listbox.yview)

        # 添加工作到列表框
        job_entries = []  # 存储工作条目，用于后续引用
        for job_name, job_info in available_jobs.items():
            description = job_info.get('description', '无描述')
            money_reward = job_info.get('money_reward', 0)
            exp_reward = job_info.get('exp_reward', 0)
            effects = job_info.get('effects', {})

            # 格式化属性变化显示
            attribute_text = ""
            if effects:
                attr_changes = []
                for attr, value in effects.items():
                    attr_name = self.attr_descriptions.get(attr, attr)
                    attr_changes.append(f"{attr_name}+{value}")
                attribute_text = "\n属性: " + ", ".join(attr_changes)

            # 创建完整的工作信息文本
            job_text = f"{job_name}:{description}  获得💰金币: {money_reward}  📚经验: {exp_reward}  {attribute_text}"
            jobs_listbox.insert(tk.END, job_text)
            job_entries.append((job_name, jobs_listbox.size() - 1))  # 存储工作名称和索引

        # 添加"开始工作"按钮
        def start_selected_job():
            selected_index = jobs_listbox.curselection()
            if selected_index:
                # 查找对应的工作名称
                for job_name, index in job_entries:
                    if index == selected_index[0]:
                        perform_job(job_name)
                        break

        # 执行工作的函数
        def perform_job(job_name):
            job_info = available_jobs.get(job_name)
            if not job_info:
                return

            # 获取工作配置
            energy_cost = job_info.get('energy_cost', 5)
            hunger_cost = job_info.get('hunger_cost', 5)
            thirst_cost = job_info.get('thirst_cost', 5)
            money_reward = job_info.get('money_reward', 0)
            exp_reward = job_info.get('exp_reward', 10)
            mood_change = job_info.get('mood_change', 0)
            effects = job_info.get('effects', {})

            # 检查状态是否足够
            min_required = 0  # 最低要求值
            lacking_attrs = []
            if self.energy < min_required + energy_cost: lacking_attrs.append("能量")
            if self.hunger < min_required + hunger_cost: lacking_attrs.append("饱腹度")
            if self.thirst < min_required + thirst_cost: lacking_attrs.append("饥渴度")

            if lacking_attrs:
                attrs_text = "、".join(lacking_attrs)
                self.show_cute_message("状态不足", f"男孩的{attrs_text}太低了，先休息和补充营养吧！")
                return

            # 消耗各项属性
            self.energy = max(0, self.energy - energy_cost)
            self.hunger = max(0, self.hunger - hunger_cost)
            self.thirst = max(0, self.thirst - thirst_cost)

            # 应用属性效果
            attribute_changes = []
            for attr, value in effects.items():
                if hasattr(self, attr):
                    setattr(self, attr, getattr(self, attr) + value)
                    attr_name = self.attr_descriptions.get(attr, attr)
                    attribute_changes.append(f"{attr_name} +{value}")

            # 获得金钱奖励
            self.money += money_reward
            # 获得经验奖励,检查是否需要升级
            self.add_exp(exp_reward)

            # 应用心情变化
            self.mood = max(0, min(100, self.mood + mood_change))

            # 构建消息
            message_lines = [f"男孩完成了{job_name}的零工！"]
            message_lines.append(f"获得了{money_reward}金币！")
            message_lines.append(f"获得了{exp_reward}经验！")
            if attribute_changes:
                message_lines.append(f"属性提升: {', '.join(attribute_changes)}")
            if mood_change != 0:
                mood_text = "变好了" if mood_change > 0 else "变差了"
                message_lines.append(f"心情{mood_text}{abs(mood_change)}%！")

            self.show_cute_message("零工完成！", "\n".join(message_lines))

            self.update_status_display()
            self.save_settings()

        # 开始工作按钮
        start_button = tk.Button(
            work_win,
            text="开始工作",
            command=start_selected_job,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"]
        )
        start_button.pack(pady=10)

        # 添加关闭按钮
        close_button = tk.Button(
            work_win,
            text="取消",
            command=work_win.destroy,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        )
        close_button.pack(pady=5)
    def rest(self):
        """休息功能 - 恢复能量"""
        if self.energy >= 90:
            self.show_cute_message("不困啦", "男孩现在很有精神，不需要休息哦！")
            return

        # 立即恢复一些能量
        immediate_rest = random.randint(10, 20)
        self.energy = min(100, self.energy + immediate_rest)

        # 心情也会稍微恢复
        self.mood = min(100, self.mood + 5)

        self.show_cute_message("休息中...", f"男孩小睡了一会，恢复了{immediate_rest}点能量！")

        self.update_status_display()
        self.save_settings()

    def open_shop(self):
        """打开商店，显示所有可购买的道具"""
        shop_win = tk.Toplevel(self.root)
        shop_win.title("商店")
        shop_win.geometry("600x600")
        shop_win.configure(bg=self.colors["bg_light"])
        shop_win.wm_attributes('-topmost', True)  # 设置窗口置顶

        self.center_window(shop_win)
        self.style_window(shop_win)

        # 商店标题
        tk.Label(
            shop_win,
            text="🛒 商店 🛒",
            font=(self.cartoon_font[0], 14, "bold"),
            bg=self.colors["bg_light"]
        ).pack(pady=10)

        # 显示当前金钱
        money_label = tk.Label(
            shop_win,
            text=f"当前金钱: {self.money}",
            font=(self.cartoon_font[0], 11, "bold"),
            bg=self.colors["bg_light"],
            fg="#FF6B6B"
        )
        money_label.pack(pady=5)

        # 创建商品列表框架
        items_frame = tk.Frame(shop_win, bg=self.colors["bg_light"])
        items_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 存储数量输入框的字典
        quantity_vars = {}

        # 从配置文件获取商品信息
        for item_name, item_info in self.items_config['items'].items():
            # 商品项框架
            item_frame = tk.Frame(items_frame, bg="#FFF8DC", relief=tk.RAISED, bd=1)
            item_frame.pack(fill=tk.X, pady=5, padx=10)

            # 商品信息框架
            item_info_frame = tk.Frame(item_frame, bg="#FFF8DC")
            item_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(item_info_frame, text=item_name, font=(self.cartoon_font[0], 11, "bold"),
                     bg="#FFF8DC").grid(row=0, column=0, sticky=tk.W)
            tk.Label(item_info_frame, text=item_info['description'], font=self.cartoon_font,
                     bg="#FFF8DC").grid(row=1, column=0, sticky=tk.W)
            tk.Label(item_info_frame, text=f"价格: {item_info['price']}金币", font=self.cartoon_font,
                     bg="#FFF8DC", fg="#FF6B6B").grid(row=0, column=1, padx=10)

            effects = item_info.get('effects', {})
            effects_text = "效果: "
            effect_parts = []
            if 'hunger' in effects: effect_parts.append(f"饱腹度+{effects['hunger']}%")
            if 'thirst' in effects: effect_parts.append(f"饥渴度+{effects['thirst']}%")
            if 'mood' in effects: effect_parts.append(f"心情+{effects['mood']}%")
            if 'energy' in effects: effect_parts.append(f"能量+{effects['energy']}%")
            if 'exp' in effects: effect_parts.append(f"经验+{effects['exp']}")

            effects_text += "、".join(effect_parts) if effect_parts else "无"
            tk.Label(item_info_frame, text=effects_text, font=self.cartoon_font,
                     bg="#FFF8DC", fg="#2E8B57").grid(row=1, column=1, sticky=tk.W)
            # 购买数量选择
            quantity_frame = tk.Frame(item_frame, bg="#FFF8DC")
            quantity_frame.pack(padx=5)

            tk.Label(quantity_frame, text="数量:", font=self.cartoon_font, bg="#FFF8DC").pack(side=tk.LEFT)
            quantity_var = tk.StringVar(value="1")
            quantity_entry = tk.Entry(quantity_frame, textvariable=quantity_var, width=5, font=self.cartoon_font)
            quantity_entry.pack(side=tk.LEFT, padx=5)
            quantity_vars[item_name] = quantity_var
            # 只能输入数字
            quantity_entry.config(validate="key", validatecommand=(self.root.register(self.validate_numeric), "%P"))

            # 购买按钮
            def buy_item(item=item_name, price=item_info['price']):
                try:
                    # 获取购买数量，默认为1
                    quantity = int(quantity_vars[item].get())
                    if quantity <= 0:
                        raise ValueError("数量必须大于0")

                    # 计算总价
                    total_price = price * quantity

                    if self.money >= total_price:
                        self.money -= total_price
                        self.items[item] = self.items.get(item, 0) + quantity
                        self.save_settings()
                        self.show_cute_message("购买成功！", f"获得了{item} x{quantity}！")
                        # 更新金钱显示
                        money_label.config(text=f"当前金钱: {self.money}")
                        # 重置数量为1
                        quantity_vars[item].set("1")
                    else:
                        self.show_cute_message("金币不足",
                                               f"购买{item} x{quantity}需要{total_price}金币，还差{total_price - self.money}金币！")
                except ValueError:
                    self.show_cute_message("输入错误", "请输入有效的数字！")
                    quantity_vars[item].set("1")

            tk.Button(item_frame, text="购买", command=buy_item,
                      font=self.cartoon_font, bg=self.colors["accent"], fg=self.colors["text"]).pack(side=tk.RIGHT, padx=5)
        # 关闭按钮
        tk.Button(shop_win, text="关闭商店", command=shop_win.destroy,
                  font=self.cartoon_font).pack(pady=10)

    def use_item(self, item_name):
        """使用道具，根据配置文件中的属性更新状态"""
        if self.items.get(item_name, 0) <= 0:
            self.show_cute_message("没有道具", f"你没有{item_name}可以使用！")
            return

        # 减少道具数量
        self.items[item_name] -= 1

        # 从配置文件获取道具效果
        item_info = self.items_config['items'].get(item_name)
        if not item_info:
            self.show_cute_message("道具错误", f"无法找到{item_name}的配置信息！")
            return

        effects = item_info.get('effects', {})
        messages = []

        # 应用道具效果
        if 'hunger' in effects:
            self.hunger = min(100, self.hunger + effects['hunger'])
            messages.append(f"饱腹度增加了{effects['hunger']}%")
        if 'thirst' in effects:
            self.thirst = min(100, self.thirst + effects['thirst'])
            messages.append(f"饥渴度增加了{effects['thirst']}%")
        if 'mood' in effects:
            self.mood = min(100, self.mood + effects['mood'])
            messages.append(f"心情变好了{effects['mood']}%")
        if 'energy' in effects:
            self.energy = min(100, self.energy + effects['energy'])
            messages.append(f"能量恢复了{effects['energy']}%")
        if 'exp' in effects:
            exp_gain = effects['exp']
            self.add_exp(exp_gain)
            messages.append(f"获得了{exp_gain}经验值")

        # 显示使用效果
        if messages:
            self.show_cute_message(f"使用了{item_name}", "\n".join(messages))

        self.update_status_display()
        self.save_settings()

    def show_items_window(self):
        """显示已拥有的道具窗口"""
        # 检查是否已经有道具窗口打开，如果有则先关闭
        if hasattr(self, 'items_window') and self.items_window.winfo_exists():
            self.items_window.destroy()

        # 创建新的道具窗口
        self.items_window = tk.Toplevel(self.root)
        self.items_window.title("已拥有道具")
        self.items_window.geometry("650x400")
        self.items_window.config(bg=self.colors["bg_light"])
        self.items_window.wm_attributes('-topmost', True)  # 设置窗口置顶

        self.center_window(self.items_window)

        # 添加状态显示区域
        status_frame = tk.Frame(self.items_window, bg=self.colors["bg_light"])
        status_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(
            status_frame,
            text="角色状态",
            font=(self.cartoon_font[0], 12, "bold"),
            bg=self.colors["bg_light"]
        ).grid(row=0, column=0, columnspan=5, pady=5)

        # 显示心情、能量、饱腹度、饥渴度
        status_labels = [
            f"经验: {self.exp}/{self.exp_to_next}",
            f"  心情: {int(self.mood)}%",
            f"  能量: {int(self.energy)}%",
            f"  饱腹度: {int(self.hunger)}%",
            f"  饥渴度: {int(self.thirst)}%"
            f"  力量: {int(self.strength)}"
            f"  敏捷: {int(self.dexterity)}"
            f"  体质: {int(self.constitution)}"
            f"  智力: {int(self.intelligence)}"
            f"  感知: {int(self.wisdom)}"
            f"  魅力: {int(self.charisma)}"
        ]

        for i, label_text in enumerate(status_labels):
            tk.Label(
                status_frame,
                text=label_text,
                font=self.cartoon_font,
                bg=self.colors["bg_light"]
            ).grid(row=1, column=i)

        # 创建滚动条
        scrollbar = tk.Scrollbar(self.items_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建列表框来显示道具
        items_listbox = tk.Listbox(
            self.items_window,
            yscrollcommand=scrollbar.set,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            width=40, height=10,
            exportselection = False  # 添加这一行，保持选中状态
        )
        items_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 配置滚动条
        scrollbar.config(command=items_listbox.yview)

        # 从配置文件获取道具描述
        self.item_entries = []  # 存储道具条目，用于后续引用
        for item_name, count in self.items.items():
            if count > 0:  # 只显示拥有数量大于0的道具
                item_info = self.items_config['items'].get(item_name, {})
                description = item_info.get('description', '无描述')

                # 添加道具效果描述
                effects = item_info.get('effects', {})
                effects_text = "效果: "
                effect_parts = []
                if 'hunger' in effects: effect_parts.append(f"饱腹度+{effects['hunger']}%")
                if 'thirst' in effects: effect_parts.append(f"饥渴度+{effects['thirst']}%")
                if 'mood' in effects: effect_parts.append(f"心情+{effects['mood']}%")
                if 'energy' in effects: effect_parts.append(f"能量+{effects['energy']}%")
                if 'exp' in effects: effect_parts.append(f"经验+{effects['exp']}")

                effects_text += "、".join(effect_parts) if effect_parts else "无"

                item_text = f"{item_name} - {count}个\n{description}\n{effects_text}"
                items_listbox.insert(tk.END, item_text)
                self.item_entries.append((item_name, items_listbox.size() - 1))  # 存储道具名称和索引

        # 添加数量选择区域
        quantity_frame = tk.Frame(self.items_window, bg=self.colors["bg_light"])
        quantity_frame.pack(pady=10)

        tk.Label(
            quantity_frame,
            text="使用数量: ",
            font=self.cartoon_font,
            bg=self.colors["bg_light"]
        ).pack(side=tk.LEFT, padx=5)

        # 创建数量输入框
        quantity_var = tk.StringVar(value="1")
        quantity_entry = tk.Entry(
            quantity_frame,
            textvariable=quantity_var,
            width=5,
            font=self.cartoon_font,
            validate="key",
            validatecommand=(self.root.register(self.validate_numeric), "%P")
        )
        quantity_entry.pack(side=tk.LEFT, padx=5)

        # 添加"使用"按钮
        def use_selected_item_with_quantity():
            selected_index = items_listbox.curselection()
            if selected_index:
                # 查找对应的道具名称
                for item_name, index in self.item_entries:
                    if index == selected_index[0]:
                        try:
                            # 获取输入的数量
                            quantity = int(quantity_var.get() or "0")
                            max_quantity = self.items.get(item_name, 0)

                            # 验证数量
                            if quantity <= 0:
                                self.show_cute_message("数量错误", "使用数量必须大于0！")
                                quantity_var.set("1")
                                return

                            if quantity > max_quantity:
                                self.show_cute_message("数量错误", f"最多只能使用{max_quantity}个！")
                                quantity_var.set(str(max_quantity))
                                return

                            # 使用指定数量的道具
                            for _ in range(quantity):
                                self.use_item(item_name)

                            # 更新状态显示
                            self.update_status_display()

                            # 重新打开道具窗口以刷新列表
                            self.show_items_window()

                        except ValueError:
                            self.show_cute_message("输入错误", "请输入有效的数字！")
                            quantity_var.set("1")
                        break

        use_button = tk.Button(
            self.items_window,
            text="使用选中的道具",
            command=use_selected_item_with_quantity,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"]
        )
        use_button.pack(pady=10)

        # 添加关闭按钮
        close_button = tk.Button(
            self.items_window,
            text="关闭",
            command=self.items_window.destroy,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        )
        close_button.pack(pady=5)

    def load_items_config(self):
        """加载道具配置文件"""
        try:
            with open('configs/items_config.json', 'r', encoding='utf-8') as f:
                self.items_config = json.load(f)
                # 初始化所有道具数量为0
                for item_name in self.items_config['items']:
                    self.items[item_name] = 0
        except FileNotFoundError:
            # 如果配置文件不存在，使用默认配置
            self.items_config = {
                'items': {
                    '面包': {
                        'description': '普通的面包，能填饱肚子',
                        'price': 10,
                        'effects': {
                            'hunger': 20,
                            'mood': 5
                        }
                    },
                    '矿泉水': {
                        'description': '普通的矿泉水，解渴',
                        'price': 5,
                        'effects': {
                            'thirst': 20
                        }
                    }
                }
            }
            # 保存默认配置到文件
            with open('configs/items_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.items_config, f, ensure_ascii=False, indent=2)

    def show_character_window(self):
        """显示角色信息窗口"""
        char_win = tk.Toplevel(self.root)
        char_win.title("角色信息")
        char_win.geometry("400x400")
        char_win.configure(bg=self.colors["bg_light"])
        char_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        self.center_window(char_win)
        self.style_window(char_win)

        # 角色姓名
        tk.Label(
            char_win,
            text=f"姓名: {self.character_name}",
            font=(self.cartoon_font[0], 14, "bold"),
            bg=self.colors["bg_light"]
        ).pack(pady=10)

        # 人生阶段和等级
        tk.Label(
            char_win,
            text=f"人生阶段: {self.life_stage}    年龄（等级）: {self.level}",
            font=(self.cartoon_font[0], 10),
            bg=self.colors["bg_light"]
        ).pack(pady=5)

        # 当前职业
        tk.Label(
            char_win,
            text=f"当前职业: {self.current_career}",
            font=(self.cartoon_font[0], 10),
            bg=self.colors["bg_light"]
        ).pack(pady=5)
        # 六维属性 - 居中展示
        attrs_frame = tk.Frame(
            char_win,
            bg=self.colors["bg_light"],
            width=200  # 设置一个合适的宽度，确保居中效果
        )
        attrs_frame.pack(pady=10, padx=20, fill=None, expand=False)
        attrs_frame.grid_columnconfigure(0, weight=1)

        attrs = [
            ("力量", self.strength),
            ("敏捷", self.dexterity),
            ("体质", self.constitution),
            ("智力", self.intelligence),
            ("感知", self.wisdom),
            ("魅力", self.charisma)
        ]

        for i, (attr_name, attr_value) in enumerate(attrs):
            # 属性标签
            tk.Label(
                attrs_frame,
                text=f"{attr_name}: {attr_value}",
                font=(self.cartoon_font[0], 10),
                bg=self.colors["bg_light"],
                anchor="center"
            ).grid(row=i, column=0, sticky="w", pady=2)
        # 关闭按钮
        tk.Button(
            char_win,
            text="重生",
            command=self.rebirth,
            font=self.cartoon_font
        ).pack(pady=10)

        # 关闭按钮
        tk.Button(
            char_win,
            text="关闭",
            command=char_win.destroy,
            font=self.cartoon_font
        ).pack(pady=10)

    def show_birth_window(self):
        """显示出生设置窗口"""
        birth_win = tk.Toplevel(self.root)
        birth_win.title("你出生了")
        birth_win.geometry("250x500")
        birth_win.configure(bg=self.colors["bg_light"])
        birth_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        self.center_window(birth_win)
        self.style_window(birth_win)

        # 添加协议处理程序，当用户关闭窗口时退出程序
        birth_win.protocol("WM_DELETE_WINDOW", self.quit_app)

        # 标题
        tk.Label(
            birth_win,
            text="你出生了",
            font=(self.cartoon_font[0], 16, "bold"),
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        ).pack(pady=20)

        # 名字输入
        name_frame = tk.Frame(birth_win, bg=self.colors["bg_light"])
        name_frame.pack(pady=10, padx=20, fill=tk.X)
        tk.Label(
            name_frame,
            text="请输入你的名字:",
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        ).pack(side=tk.LEFT)
        name_entry = tk.Entry(
            name_frame,
            font=self.cartoon_font,
            width=20,
            bg="white",
            fg=self.colors["text"]
        )
        name_entry.pack(side=tk.LEFT, padx=10)
        name_entry.insert(0, "小男孩")

        # 剩余属性点
        remaining_points = [15]  # 使用列表存储可变值
        points_label = tk.Label(
            birth_win,
            text=f"剩余属性点: {remaining_points[0]}",
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        )
        points_label.pack(pady=10)

        # 六维属性框架
        attrs_frame = tk.Frame(birth_win, bg=self.colors["bg_light"])
        attrs_frame.pack(pady=10, padx=20, fill=tk.X)

        # 随机生成六维属性，每项最高5
        self.strength = random.randint(1, 5)
        self.dexterity = random.randint(1, 5)
        self.constitution = random.randint(1, 5)
        self.intelligence = random.randint(1, 5)
        self.wisdom = random.randint(1, 5)
        self.charisma = random.randint(1, 5)

        # 存储基础属性值，用于重置
        base_attrs = {
            "力量": self.strength,
            "敏捷": self.dexterity,
            "体质": self.constitution,
            "智力": self.intelligence,
            "感知": self.wisdom,
            "魅力": self.charisma
        }

        # 存储额外分配的属性点
        extra_attrs = {
            "力量": 0,
            "敏捷": 0,
            "体质": 0,
            "智力": 0,
            "感知": 0,
            "魅力": 0
        }

        # 创建显示总属性的变量
        attr_vars = {
            "力量": tk.IntVar(value=self.strength),
            "敏捷": tk.IntVar(value=self.dexterity),
            "体质": tk.IntVar(value=self.constitution),
            "智力": tk.IntVar(value=self.intelligence),
            "感知": tk.IntVar(value=self.wisdom),
            "魅力": tk.IntVar(value=self.charisma)
        }

        # 创建属性调整界面
        attr_labels = {}
        for i, (attr_name, attr_var) in enumerate(attr_vars.items()):
            row_frame = tk.Frame(attrs_frame, bg=self.colors["bg_light"])
            row_frame.pack(fill=tk.X, pady=5)

            # 属性标签
            label = tk.Label(
                row_frame,
                text=f"{attr_name}: ",
                font=self.cartoon_font,
                bg=self.colors["bg_light"],
                fg=self.colors["text"],
                width=6,
                anchor="w"
            )
            label.pack(side=tk.LEFT)

            # 减少按钮 - 移除额外分配的属性点
            def decrease_attr(name=attr_name):
                if extra_attrs[name] > 0:
                    extra_attrs[name] -= 1
                    remaining_points[0] += 1
                    attr_vars[name].set(base_attrs[name] + extra_attrs[name])
                    points_label.config(text=f"剩余属性点: {remaining_points[0]}")

            tk.Button(
                row_frame,
                text="-",
                command=decrease_attr,
                font=self.cartoon_font,
                bg="#B0E2FF",
                fg=self.colors["text"],
                width=3
            ).pack(side=tk.LEFT)

            # 属性值显示
            value_label = tk.Label(
                row_frame,
                textvariable=attr_var,
                font=self.cartoon_font,
                bg=self.colors["bg_light"],
                fg=self.colors["text"],
                width=3,
                anchor="center"
            )
            value_label.pack(side=tk.LEFT, padx=5)
            attr_labels[attr_name] = value_label

            # 增加按钮 - 使用额外属性点
            def increase_attr(name=attr_name):
                if remaining_points[0] > 0:
                    extra_attrs[name] += 1
                    remaining_points[0] -= 1
                    attr_vars[name].set(base_attrs[name] + extra_attrs[name])
                    points_label.config(text=f"剩余属性点: {remaining_points[0]}")

            tk.Button(
                row_frame,
                text="+",
                command=increase_attr,
                font=self.cartoon_font,
                bg="#B0E2FF",
                fg=self.colors["text"],
                width=3
            ).pack(side=tk.LEFT)

            # 显示基础属性值
            base_label = tk.Label(
                row_frame,
                text=f"(基础: {base_attrs[attr_name]})",
                font=(self.cartoon_font[0], 7),
                bg=self.colors["bg_light"],
                fg="#888888",
                anchor="w"
            )
            base_label.pack(side=tk.LEFT, padx=5)

        # 完成出生按钮
        def confirm_birth(remaining_points):
            # 检查剩余属性点是否为0
            if remaining_points[0] > 0:
                # 弹出提醒对话框
                messagebox.showinfo("提醒", "您还有未分配的属性点，请分配完毕再确认出生！")
                return

            # ... 保存名字和属性值的现有代码 ...
            name = name_entry.get()
            if not name:  # 确保有输入名字
                messagebox.showinfo("提醒", "请输入角色名字！")
                return

            # 保存最终属性值
            self.strength = attr_vars["力量"].get()
            self.dexterity = attr_vars["敏捷"].get()
            self.constitution = attr_vars["体质"].get()
            self.intelligence = attr_vars["智力"].get()
            self.wisdom = attr_vars["感知"].get()
            self.charisma = attr_vars["魅力"].get()

            # 保存设置
            self.save_settings()
            birth_win.destroy()
            self.show_cute_message("欢迎来到世界！", f"你好，{self.character_name}！祝你有美好的人生旅程～")

        tk.Button(
            birth_win,
            text="完成出生",
            command=lambda: confirm_birth(remaining_points),
            font=(self.cartoon_font[0], 12, "bold"),
            bg=self.colors["accent"],
            fg=self.colors["text"],
            padx=20,
            pady=5
        ).pack(pady=20)

        # 隐藏主窗口直到出生设置完成
        self.root.withdraw()
        birth_win.wait_window()
        self.root.deiconify()

    def update_life_stage(self):
        """根据等级更新人生阶段"""
        if self.level <= 3:
            self.life_stage = "学龄前"
        elif self.level <= 6:
            self.life_stage = "幼儿园"
        elif self.level <= 12:
            self.life_stage = "小学"
        elif self.level <= 15:
            self.life_stage = "中学"
        elif self.level <= 18:
            self.life_stage = "高中"
        elif self.level <= 22:
            self.life_stage = "大学"
        elif self.level < 65:
            self.life_stage = "工作"
        else:
            self.life_stage = "退休"

    def load_study_config(self):
        """加载学习项目配置"""
        try:
            with open('configs/study_config.json', 'r', encoding='utf-8') as f:
                self.study_config = json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            self.study_config = {
                'studies': {
                    "读书": {
                        "description": "简单的认知学习，适合学龄前儿童",
                        "min_level": 1,
                        "max_level": 9999,
                        "effects": {
                            "intelligence": 1,
                            "wisdom": 1
                        },
                        "energy_cost": 5,
                        "hunger_cost": 5,
                        "thirst_cost": 5,
                        "mood_change": 5
                    }
                }
            }

    def load_work_config(self):
        """加载工作项目配置"""
        try:
            with open('configs/work_config.json', 'r', encoding='utf-8') as f:
                self.work_config = json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            self.work_config = {
                'jobs': {
                    "赚钱": {
                        "description": "赚钱",
                        "min_level": 1,
                        "max_level": 9999,
                        "effects": {
                            "strength": 1,
                            "dexterity": 1,
                            "constitution": 1
                        },
                        "energy_cost": 5,
                        "hunger_cost": 5,
                        "thirst_cost": 5,
                        "money_reward": 5,
                        "mood_change": -3
                    },
                }
            }

    def load_exercise_config(self):
        """加载运动项目配置"""
        try:
            with open('configs/exercise_config.json', 'r', encoding='utf-8') as f:
                self.exercise_config = json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            self.exercise_config = {
                'exercise_items': {
                    "散步": {
                        "description": "轻松的散步，恢复心情和能量",
                        "min_level": 4,
                        "max_level": 999,
                        "effects": {
                            "strength": 1,
                            "constitution": 1,
                            "dexterity": 1
                        },
                        "energy_cost": 5,
                        "hunger_cost": 5,
                        "thirst_cost": 5,
                        "exp_reward": 10,
                        "mood_change": 10
                    }
                }
            }

    def load_play_config(self):
        """加载玩耍项目配置"""
        try:
            with open('configs/play_config.json', 'r', encoding='utf-8') as f:
                self.play_config = json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            self.play_config = {
                'games': {
                    "积木游戏": {
                        "description": "开发创造力的积木游戏",
                        "min_level": 1,
                        "max_level": 999,
                        "effects": {
                            "wisdom": 1,
                            "dexterity": 1,
                            "intelligence": 1
                        },
                        "energy_cost": 5,
                        "hunger_cost": 5,
                        "thirst_cost": 5,
                        "exp_reward": 10,
                        "mood_change": 12
                    }
                }
            }

    def study(self):
        """学习功能 - 提供多种学习选项"""
        # 确保学习配置已加载
        if not hasattr(self, 'study_config') or not self.study_config:
            self.load_study_config()

        # 获取适合当前等级的学习项目
        available_studies = {}
        for name, config in self.study_config.get('study_items', {}).items():
            if config.get('min_level', 1) <= self.level <= config.get('max_level', 9999):
                available_studies[name] = config

        # 如果没有可用的学习项目
        if not available_studies:
            self.show_cute_message("学习", "当前等级没有适合的学习项目哦～")
            return

        # 创建学习选择窗口
        study_win = tk.Toplevel(self.root)
        study_win.title("选择学习项目")
        study_win.geometry("600x400")
        study_win.configure(bg=self.colors["bg_light"])
        study_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        study_win.transient(self.root)

        # 工作标题
        tk.Label(
            study_win,
            text="📕 选择学习项目 📕",
            font=(self.cartoon_font[0], 14, "bold"),
            bg=self.colors["bg_light"]
        ).pack(pady=10)

        # 创建滚动条
        scrollbar = tk.Scrollbar(study_win)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建列表框
        study_listbox = tk.Listbox(
            study_win,
            yscrollcommand=scrollbar.set,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_light"],
            width=40,
            height=10,
            selectmode=tk.SINGLE
        )
        study_listbox.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        scrollbar.config(command=study_listbox.yview)

        # 填充学习项目
        study_entries = []  # 存储学习项目条目，用于后续引用
        for name, config in available_studies.items():
            description = config.get('description', '无描述')
            exp_reward = config.get('exp_reward', 0)
            effects = config.get('effects', {})
            money_reward = config.get('money_reward', 0)  # 有些学习可能也有金币奖励

            # 格式化属性变化显示
            attribute_text = ""
            if effects:
                attr_changes = []
                for attr, value in effects.items():
                    attr_name = self.attr_descriptions.get(attr, attr)
                    attr_changes.append(f"{attr_name}+{value}")
                attribute_text = "\n属性: " + ", ".join(attr_changes)

            # 创建完整的学习信息文本
            money_text = f" 💰金币: {money_reward}" if money_reward > 0 else ""
            study_text = f"{name}:{description}  📚经验: {exp_reward}  {money_text}  {attribute_text}"
            study_listbox.insert(tk.END, study_text)
            study_entries.append((name, study_listbox.size() - 1))  # 存储学习项目名称和索引

        # 创建确认按钮
        def start_study():
            selected_index = study_listbox.curselection()
            if not selected_index:
                self.show_cute_message("提示", "请先选择一个学习项目～")
                return

            # 找到对应的学习项目名称
            selected_study = None
            for name, index in study_entries:
                if index == selected_index[0]:
                    selected_study = name
                    break

            if not selected_study:
                return

            study_config = available_studies[selected_study]

            # 检查状态是否足够
            energy_cost = study_config.get('energy_cost', 0)
            hunger_cost = study_config.get('hunger_cost', 0)
            thirst_cost = study_config.get('thirst_cost', 0)

            # 检查状态是否足够
            min_required = 0  # 最低要求值
            lacking_attrs = []
            if self.energy < min_required + energy_cost: lacking_attrs.append("能量")
            if self.hunger < min_required + hunger_cost: lacking_attrs.append("饱腹度")
            if self.thirst < min_required + thirst_cost: lacking_attrs.append("饥渴度")

            if lacking_attrs:
                attrs_text = "、".join(lacking_attrs)
                self.show_cute_message("状态不足", f"男孩的{attrs_text}太低了，先休息和补充营养吧！")
                return

            # 消耗状态
            self.energy = max(0, self.energy - energy_cost)
            self.hunger = max(0, self.hunger - hunger_cost)
            self.thirst = max(0, self.thirst - thirst_cost)

            # 增加经验
            exp_reward = study_config.get('exp_reward', 10)
            self.add_exp(exp_reward)

            # 应用属性效果
            effects = study_config.get('effects', {})
            attribute_changes = []
            for attr, value in effects.items():
                if hasattr(self, attr):
                    setattr(self, attr, getattr(self, attr) + value)
                    attr_name = self.attr_descriptions.get(attr, attr)
                    attribute_changes.append(f"{attr_name} +{value}")

            # 改变心情
            mood_change = study_config.get('mood_change', 0)
            self.mood = max(0, min(100, self.mood + mood_change))

            # 构建消息
            message_lines = [f"男孩完成了{selected_study}的学习！"]
            message_lines.append(f"获得了{exp_reward}经验！")
            if attribute_changes:
                message_lines.append(f"属性提升: {', '.join(attribute_changes)}")
            if mood_change != 0:
                mood_text = "变好了" if mood_change > 0 else "变差了"
                message_lines.append(f"心情{mood_text}{abs(mood_change)}%！")
            self.show_cute_message("学习完成", "\n".join(message_lines))
            # 更新状态显示
            self.update_status_display()

        # 创建按钮容器
        button_frame = tk.Frame(study_win, bg=self.colors["bg_light"])
        button_frame.pack(fill=tk.X, pady=10, padx=20)

        # 确认按钮
        confirm_btn = tk.Button(
            button_frame,
            text="开始学习",
            command=start_study,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"],
        )
        confirm_btn.pack(side=tk.LEFT, expand=True, padx=5)

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            command=study_win.destroy,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        )
        cancel_btn.pack(side=tk.LEFT, expand=True, padx=5)

        # 居中显示窗口
        study_win.update_idletasks()
        width = study_win.winfo_width()
        height = study_win.winfo_height()
        x = (study_win.winfo_screenwidth() // 2) - (width // 2)
        y = (study_win.winfo_screenheight() // 2) - (height // 2)
        study_win.geometry(f"{width}x{height}+{x}+{y}")

        # 确保窗口在最上层
        study_win.lift()

    def exercise(self):
        """运动功能 - 提供多种运动选项"""
        # 确保运动配置已加载
        if not hasattr(self, 'exercise_config') or not self.exercise_config:
            self.load_exercise_config()

        # 获取适合当前等级的运动项目
        available_exercises = {}
        for name, config in self.exercise_config.get('exercise_items', {}).items():
            if config.get('min_level', 1) <= self.level <= config.get('max_level', 9999):
                available_exercises[name] = config

        # 如果没有可用的运动项目
        if not available_exercises:
            self.show_cute_message("运动", "当前等级没有适合的运动项目哦～")
            return

        # 创建运动选择窗口
        exercise_win = tk.Toplevel(self.root)
        exercise_win.title("选择运动项目")
        exercise_win.geometry("600x400")
        exercise_win.configure(bg=self.colors["bg_light"])
        exercise_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        exercise_win.transient(self.root)

        # 工作标题
        tk.Label(
            exercise_win,
            text="🏃 选择运动项目 🏃",
            font=(self.cartoon_font[0], 14, "bold"),
            bg=self.colors["bg_light"]
        ).pack(pady=10)

        # 创建滚动条
        scrollbar = tk.Scrollbar(exercise_win)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建列表框
        exercise_listbox = tk.Listbox(
            exercise_win,
            yscrollcommand=scrollbar.set,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_light"],
            width=40,
            height=10,
            selectmode=tk.SINGLE
        )
        exercise_listbox.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        scrollbar.config(command=exercise_listbox.yview)

        # 填充运动项目
        exercise_entries = []  # 存储运动项目条目，用于后续引用
        for name, config in available_exercises.items():
            description = config.get('description', '无描述')
            exp_reward = config.get('exp_reward', 0)
            effects = config.get('effects', {})
            money_reward = config.get('money_reward', 0)  # 有些运动可能也有金币奖励

            # 格式化属性变化显示
            attribute_text = ""
            if effects:
                attr_changes = []
                for attr, value in effects.items():
                    attr_name = self.attr_descriptions.get(attr, attr)
                    attr_changes.append(f"{attr_name}+{value}")
                attribute_text = "\n属性: " + ", ".join(attr_changes)

            # 创建完整的运动信息文本
            money_text = f" 💰金币: {money_reward}" if money_reward > 0 else ""
            exercise_text = f"{name}:{description}  📚经验: {exp_reward}  {money_text}  {attribute_text}"
            exercise_listbox.insert(tk.END, exercise_text)
            exercise_entries.append((name, exercise_listbox.size() - 1))  # 存储运动项目名称和索引

        # 创建确认按钮
        def start_exercise():
            selected_index = exercise_listbox.curselection()
            if not selected_index:
                self.show_cute_message("提示", "请先选择一个运动项目～")
                return

            # 找到对应的运动项目名称
            selected_exercise = None
            for name, index in exercise_entries:
                if index == selected_index[0]:
                    selected_exercise = name
                    break

            if not selected_exercise:
                return

            exercise_config = available_exercises[selected_exercise]

            # 检查状态是否足够
            energy_cost = exercise_config.get('energy_cost', 0)
            hunger_cost = exercise_config.get('hunger_cost', 0)
            thirst_cost = exercise_config.get('thirst_cost', 0)

            # 检查状态是否足够
            min_required = 0  # 最低要求值
            lacking_attrs = []
            if self.energy < min_required + energy_cost: lacking_attrs.append("能量")
            if self.hunger < min_required + hunger_cost: lacking_attrs.append("饱腹度")
            if self.thirst < min_required + thirst_cost: lacking_attrs.append("饥渴度")

            if lacking_attrs:
                attrs_text = "、".join(lacking_attrs)
                self.show_cute_message("状态不足", f"男孩的{attrs_text}太低了，先休息和补充营养吧！")
                return

            # 消耗状态
            self.energy = max(0, self.energy - energy_cost)
            self.hunger = max(0, self.hunger - hunger_cost)
            self.thirst = max(0, self.thirst - thirst_cost)

            # 增加经验
            exp_reward = exercise_config.get('exp_reward', 10)
            self.add_exp(exp_reward)

            # 应用属性效果
            effects = exercise_config.get('effects', {})
            attribute_changes = []
            for attr, value in effects.items():
                if hasattr(self, attr):
                    setattr(self, attr, getattr(self, attr) + value)
                    attr_name = self.attr_descriptions.get(attr, attr)
                    attribute_changes.append(f"{attr_name} +{value}")

            # 改变心情
            mood_change = exercise_config.get('mood_change', 0)
            self.mood = max(0, min(100, self.mood + mood_change))

            # 构建消息
            message_lines = [f"男孩完成了{selected_exercise}的运动！"]
            message_lines.append(f"获得了{exp_reward}经验！")
            if attribute_changes:
                message_lines.append(f"属性提升: {', '.join(attribute_changes)}")
            if mood_change != 0:
                mood_text = "变好了" if mood_change > 0 else "变差了"
                message_lines.append(f"心情{mood_text}{abs(mood_change)}%！")
            self.show_cute_message("运动完成", "\n".join(message_lines))
            # 更新状态显示
            self.update_status_display()

        # 创建按钮容器
        button_frame = tk.Frame(exercise_win, bg=self.colors["bg_light"])
        button_frame.pack(fill=tk.X, pady=10, padx=20)

        # 确认按钮
        confirm_btn = tk.Button(
            button_frame,
            text="开始运动",
            command=start_exercise,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"],
        )
        confirm_btn.pack(side=tk.LEFT, expand=True, padx=5)

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            command=exercise_win.destroy,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        )
        cancel_btn.pack(side=tk.LEFT, expand=True, padx=5)

        # 居中显示窗口
        exercise_win.update_idletasks()
        width = exercise_win.winfo_width()
        height = exercise_win.winfo_height()
        x = (exercise_win.winfo_screenwidth() // 2) - (width // 2)
        y = (exercise_win.winfo_screenheight() // 2) - (height // 2)
        exercise_win.geometry(f"{width}x{height}+{x}+{y}")

        # 确保窗口在最上层
        exercise_win.lift()

    def play(self):
        """玩耍功能 - 消耗能量、饱腹度和饥渴度，获得经验"""
        # 检查是否有可用的玩耍配置
        if not self.play_config:
            self.show_cute_message("配置错误", "无法加载玩耍配置，请检查play_config.json文件！")
            return
        # 获取实际的玩耍项目（从play_items键下获取）
        play_items = self.play_config.get('play_items', {})
        if not play_items:
            self.show_cute_message("配置错误", "玩耍配置中找不到play_items项！")
            return

        # 筛选当前等级可用的玩耍项目
        available_play = {}
        for play_name, play_info in play_items.items():
            min_level = play_info.get('min_level', 1)
            max_level = play_info.get('max_level', 9999)
            if min_level <= self.level <= max_level:
                available_play[play_name] = play_info

        if not available_play:
            self.show_cute_message("没有可用玩耍项目", f"你的等级{self.level}还不能玩耍，继续成长吧！")
            return

        # 创建玩耍项目选择窗口
        play_win = tk.Toplevel(self.root)
        play_win.title("选择玩耍项目")
        play_win.geometry("600x400")
        play_win.configure(bg=self.colors["bg_light"])
        play_win.wm_attributes('-topmost', True)  # 设置窗口置顶
        self.center_window(play_win)
        self.style_window(play_win)

        # 玩耍标题
        tk.Label(
            play_win,
            text="🎮 选择要玩耍的项目 🎮",
            font=(self.cartoon_font[0], 14, "bold"),
            bg=self.colors["bg_light"]
        ).pack(pady=10)

        # 创建玩耍项目列表框框架
        play_frame = tk.Frame(play_win, bg=self.colors["bg_light"])
        play_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 创建滚动条
        scrollbar = tk.Scrollbar(play_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建列表框来显示工作
        play_listbox = tk.Listbox(
            play_frame,
            yscrollcommand=scrollbar.set,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            width=40, height=10,
            selectmode=tk.SINGLE
        )
        play_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 配置滚动条
        scrollbar.config(command=play_listbox.yview)

        # 添加玩耍项目到列表框
        play_entries = []  # 存储玩耍条目，用于后续引用
        for play_name, play_info in available_play.items():
            description = play_info.get('description', '无描述')
            energy_cost = play_info.get('energy_cost', 0)
            exp_reward = play_info.get('exp_reward', 0)
            money_reward = play_info.get('money_reward', 0)  # 有些玩耍可能也有金币奖励
            effects = play_info.get('effects', {})

            # 格式化属性变化显示
            attribute_text = ""
            if effects:
                attr_changes = []
                for attr, value in effects.items():
                    attr_name = self.attr_descriptions.get(attr, attr)
                    attr_changes.append(f"{attr_name}+{value}")
                attribute_text = "\n属性: " + ", ".join(attr_changes)

            # 创建完整的玩耍信息文本
            money_text = f" 💰金币: {money_reward}" if money_reward > 0 else ""
            play_text = f"{play_name}:{description}  📚经验: {exp_reward}  {money_text}  {attribute_text}"
            play_listbox.insert(tk.END, play_text)
            play_entries.append((play_name, play_listbox.size() - 1))  # 存储玩耍项目名称和索引

            # 创建确认按钮
        def start_play():
            selected_index = play_listbox.curselection()
            if not selected_index:
                self.show_cute_message("提示", "请先选择一个玩耍项目～")
                return
            # 找到对应的玩耍项目名称
            selected_play = None
            for name, index in play_entries:
                 if index == selected_index[0]:
                    selected_play = name
                    break

            if not selected_play:
                return

            play_config = available_play[selected_play]

            # 检查状态是否足够
            energy_cost = play_config.get('energy_cost', 0)
            hunger_cost = play_config.get('hunger_cost', 0)
            thirst_cost = play_config.get('thirst_cost', 0)

            # 检查状态是否足够
            min_required = 0  # 最低要求值
            lacking_attrs = []
            if self.energy < min_required + energy_cost: lacking_attrs.append("能量")
            if self.hunger < min_required + hunger_cost: lacking_attrs.append("饱腹度")
            if self.thirst < min_required + thirst_cost: lacking_attrs.append("饥渴度")

            if lacking_attrs:
                attrs_text = "、".join(lacking_attrs)
                self.show_cute_message("状态不足", f"男孩的{attrs_text}太低了，先休息和补充营养吧！")
                return

            # 消耗状态
            self.energy = max(0, self.energy - energy_cost)
            self.hunger = max(0, self.hunger - hunger_cost)
            self.thirst = max(0, self.thirst - thirst_cost)

            # 增加经验
            exp_reward = play_config.get('exp_reward', 10)
            self.add_exp(exp_reward)

            # 应用属性效果
            effects = play_config.get('effects', {})
            attribute_changes = []
            for attr, value in effects.items():
                if hasattr(self, attr):
                    setattr(self, attr, getattr(self, attr) + value)
                    attr_name = self.attr_descriptions.get(attr, attr)
                    attribute_changes.append(f"{attr_name} +{value}")

            # 改变心情
            mood_change = play_config.get('mood_change', 0)
            self.mood = max(0, min(100, self.mood + mood_change))

            # 构建消息
            message_lines = [f"男孩进行了{selected_play}！"]
            message_lines.append(f"获得了{exp_reward}经验！")
            if attribute_changes:
                message_lines.append(f"属性提升: {', '.join(attribute_changes)}")
            if mood_change != 0:
                mood_text = "变好了" if mood_change > 0 else "变差了"
                message_lines.append(f"心情{mood_text}{abs(mood_change)}%！")
            self.show_cute_message("玩耍结束", "\n".join(message_lines))
            # 更新状态显示
            self.update_status_display()

        # 创建按钮容器
        button_frame = tk.Frame(play_win, bg=self.colors["bg_light"])
        button_frame.pack(fill=tk.X, pady=10, padx=20)

        # 确认按钮
        confirm_btn = tk.Button(
            button_frame,
            text="开始玩耍",
            command=start_play,
            font=self.cartoon_font,
            bg=self.colors["accent"],
            fg=self.colors["text"],
        )
        confirm_btn.pack(side=tk.LEFT, expand=True, padx=5)

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            command=play_win.destroy,
            font=self.cartoon_font,
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        )
        cancel_btn.pack(side=tk.LEFT, expand=True, padx=5)

        # 居中显示窗口
        play_win.update_idletasks()
        width = play_win.winfo_width()
        height = play_win.winfo_height()
        x = (play_win.winfo_screenwidth() // 2) - (width // 2)
        y = (play_win.winfo_screenheight() // 2) - (height // 2)
        play_win.geometry(f"{width}x{height}+{x}+{y}")

        # 确保窗口在最上层
        play_win.lift()

    def load_career_config(self):
        """加载职业配置"""
        try:
            with open('configs/career_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.career_config = config.get('careers', {})
        except Exception as e:
            print(f"加载职业配置失败: {e}")
            self.show_cute_message("配置错误", "无法加载职业配置文件！")

    def job(self):
        """处理工作"""
        if self.life_stage != "工作":
            self.show_cute_message("人生阶段不符", f"您当前处于{self.life_stage}阶段，需要到达'工作'阶段才能找工作。")
            return
        if not self.career_config:
            self.show_cute_message("配置错误", "职业配置文件未加载！")
            return

        careers = self.career_config
        # 创建职业选择窗口
        career_win = tk.Toplevel(self.root)
        career_win.title("职业选择")
        career_win.geometry("700x500")
        career_win.configure(bg=self.colors["bg_light"])
        career_win.wm_attributes('-topmost', True)
        self.center_window(career_win)
        self.style_window(career_win)

        # 添加标题
        title_frame = tk.Frame(career_win, bg=self.colors["bg_light"])
        title_frame.pack(pady=10, fill=tk.X, padx=20)
        title_label = tk.Label(
            title_frame,
            text="选择职业",
            font=(self.cartoon_font[0], 14, "bold"),
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        )
        title_label.pack()

        # 当前职业显示
        current_career_frame = tk.Frame(career_win, bg=self.colors["bg_light"])
        current_career_frame.pack(pady=5, fill=tk.X, padx=20)

        if self.current_career != "无":
            current_career_info = self.career_config.get(self.current_career, {})
            current_salary = current_career_info.get("salary", 0)
            current_exp = current_career_info.get("experience", 0)

        current_career_label = tk.Label(
            current_career_frame,
            text=f"当前职业：{self.current_career}\n周薪：{current_salary}\n每周经验：{current_exp}",
            font=(self.cartoon_font[0], 10),
            bg=self.colors["bg_light"],
            fg=self.colors["text"]
        )
        current_career_label.pack(anchor=tk.W)

        # 换工作提示
        if self.current_career != "无":
            cost_frame = tk.Frame(career_win, bg=self.colors["bg_light"])
            cost_frame.pack(pady=5, fill=tk.X, padx=20)
            cost_label = tk.Label(
                cost_frame,
                text="换工作将花费2000元",
                font=(self.cartoon_font[0], 10, "italic"),
                bg=self.colors["bg_light"],
                fg=self.colors["text"]
            )
            cost_label.pack(anchor=tk.W)

        # 创建滚动区域
        canvas_frame = tk.Frame(career_win, bg=self.colors["bg_light"])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(canvas_frame, bg=self.colors["bg_light"])
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors["bg_light"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 添加职业列表
        for career_name, career_data in careers.items():
            career_frame = tk.Frame(scrollable_frame, bg="white", relief="solid", bd=1)
            career_frame.pack(fill=tk.X, padx=5, pady=5)

            # 职业名称和薪资
            header_frame = tk.Frame(career_frame, bg="white")
            header_frame.pack(fill=tk.X, padx=10, pady=5)
            name_label = tk.Label(
                header_frame,
                text=career_name,
                font=(self.cartoon_font[0], 11, "bold"),
                bg="white",
                fg=self.colors["text"]
            )
            name_label.pack(side=tk.LEFT)
            salary_label = tk.Label(
                header_frame,
                text=f"周薪: {career_data.get('salary', 0)}",
                font=(self.cartoon_font[0], 10),
                bg="white",
                fg=self.colors["accent"]
            )
            salary_label.pack(side=tk.RIGHT)

            # 经验值奖励
            exp_frame = tk.Frame(career_frame, bg="white")
            exp_frame.pack(fill=tk.X, padx=10)
            exp_label = tk.Label(
                exp_frame,
                text=f"每周经验值: {career_data.get('experience', 0)}",
                font=(self.cartoon_font[0], 10),
                bg="white",
                fg=self.colors["text"]
            )
            exp_label.pack(anchor=tk.W)

            # 需求条件
            req_frame = tk.Frame(career_frame, bg="white")
            req_frame.pack(fill=tk.X, padx=10, pady=5)
            req_label = tk.Label(
                req_frame,
                text="需求条件:",
                font=(self.cartoon_font[0], 10, "bold"),
                bg="white",
                fg=self.colors["text"]
            )
            req_label.pack(anchor=tk.W)

            # 显示具体需求
            reqs = career_data.get('requirements', {})
            req_details = ""
            for attr, value in reqs.items():
                attr_name = {
                    'strength': '力量',
                    'dexterity': '敏捷',
                    'constitution': '体质',
                    'intelligence': '智力',
                    'wisdom': '智慧',
                    'charisma': '魅力'
                }.get(attr, attr)
                current_value = getattr(self, attr, 0)
                req_details += f"{attr_name}: {current_value}/{value}\n"

            req_text = tk.Text(req_frame, height=min(3, len(reqs)), width=60, font=(self.cartoon_font[0], 10))
            req_text.pack(fill=tk.X, pady=2)
            req_text.insert(tk.END, req_details)
            req_text.config(state=tk.DISABLED)

            # 检查是否满足条件
            can_apply = all(getattr(self, attr, 0) >= value for attr, value in reqs.items())
            can_afford = (self.current_career == "无" or self.money >= 2000)

            # 申请按钮
            button_frame = tk.Frame(career_frame, bg="white")
            button_frame.pack(fill=tk.X, padx=10, pady=5)

            if career_name == self.current_career:
                # 当前职业，不可再次申请
                tk.Button(
                    button_frame,
                    text="当前职业",
                    font=self.cartoon_font,
                    bg="#CCCCCC",  # 灰色按钮
                    fg=self.colors["text"],
                    state=tk.DISABLED,
                    width=10
                ).pack(pady=5)
            else:
                tk.Button(
                    button_frame,
                    text="申请",
                    command=lambda c=career_name, data=career_data: self.apply_for_career(c, data) or career_win.destroy(),
                    state=tk.NORMAL if can_apply and can_afford else tk.DISABLED,
                    bg=self.colors["accent"],
                    fg="white",
                    relief="flat",
                    font=(self.cartoon_font[0], 10, "bold")
                ).pack(side=tk.RIGHT)

            # 显示无法申请的原因
            if not can_apply:
                reason_label = tk.Label(
                    button_frame,
                    text="条件不满足",
                    font=(self.cartoon_font[0], 10),
                    bg="white",
                    fg="red"
                )
                reason_label.pack(side=tk.RIGHT, padx=5)
            elif not can_afford:
                reason_label = tk.Label(
                    button_frame,
                    text="资金不足",
                    font=(self.cartoon_font[0], 10),
                    bg="white",
                    fg="red"
                )
                reason_label.pack(side=tk.RIGHT, padx=5)

        # 关闭按钮
        close_frame = tk.Frame(career_win, bg=self.colors["bg_light"])
        close_frame.pack(pady=10, fill=tk.X, padx=20)
        close_button = tk.Button(
            close_frame,
            text="关闭",
            command=career_win.destroy,
            bg=self.colors["accent"],
            fg="white",
            relief="flat",
            font=(self.cartoon_font[0], 10, "bold")
        )
        close_button.pack(side=tk.RIGHT)

    def apply_for_career(self, career_name, career_data):
        """申请职业并更新当前职业信息"""
        # 检查是否需要支付换工作费用（2000元）
        if self.current_career != "无":
            if self.money < 2000:
                self.show_cute_message("资金不足", "换工作需要支付2000元手续费！")
                return
            else:
                # 扣除换工作费用
                self.money -= 2000
                cost_message = f"扣除了2000元换工作费用，剩余{self.money}元。\n"
        else:
            cost_message = ""

        # 更新当前职业
        self.current_career = career_name

        # 记录当前时间为上次领薪时间
        self.last_salary_time = datetime.now()

        # 显示成功消息
        self.show_cute_message(
            "职业申请成功",
            f"{cost_message}你成功成为了一名{career_name}！\n"\
            f"每周可获得{career_data['salary']}金币和{career_data['experience']}经验。"
        )

        # 保存设置，确保职业信息持久化
        self.save_settings()

        # 刷新界面显示，更新当前职业信息
        self.update_status_display()

        # 重新设置薪资定时器
        self.setup_career_salary_timer()

    def setup_career_salary_timer(self):
        """设置每周发放工资和经验的定时器"""
        # 每一分钟检查一次是否需要发放工资
        self.root.after(60000, self.check_and_pay_salary)

    def check_and_pay_salary(self):
        """检查并发放工资"""
        if self.last_salary_time is not None:
            # 获取当前时间和上次发工资时间
            current_time = datetime.now()
            # 如果距离上次发工资已经超过7天（604800秒），则发放工资
            if (current_time - self.last_salary_time).total_seconds() >= 604800:
                self.pay_salary()
        else:
            # 首次运行，记录当前时间
            self.last_salary_time = datetime.now()
            # 保存到设置中
            self.save_settings()

        # 继续定时检查
        self.setup_career_salary_timer()

    def pay_salary(self):
        """发放工资和经验"""
        if self.current_career != "无" and self.life_stage == "工作":
            # 加载职业配置
            careers = self.career_config
            if self.current_career in careers:
                career_data = careers[self.current_career]
                salary = career_data.get('salary', 0)
                experience = career_data.get('experience', 0)

                # 添加工资
                self.money += salary
                # 添加经验
                self.add_exp(experience)

                # 更新显示
                self.update_status_display()

                # 显示工资发放消息
                self.show_cute_message("工资发放", f"恭喜您获得了一周的工资！\n+ {salary}元\n+ {experience}经验值")

        # 更新上次发工资时间
        self.last_salary_time = datetime.now()
        # 保存设置
        self.save_settings()

    def rebirth(self):
        """重生"""
        # 确认重生
        confirm = tk.messagebox.askyesno("确认重生", "您确定要重生吗？\n所有进度将被重置，应用将重启，需要等待一段时间。")
        if not confirm:
            return
        # 删除settings.json
        try:
            os.remove("configs/settings.json")
        except FileNotFoundError:
            pass

        # 关闭应用并重新启动
        os.execl(sys.executable, sys.executable, *sys.argv)

    def validate_numeric(self, value):
        """验证输入是否为有效的数字（正整数）"""
        # 允许空字符串（表示0）或者只包含数字的字符串
        if value == "" or value.isdigit():
            return True
        return False

if __name__ == "__main__":
    root = tk.Tk()
    pet = MyBoy(root)
    root.mainloop()
