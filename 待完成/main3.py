import datetime
import json
import os
import random
import requests
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, colorchooser
import winreg
import win32gui
import win32con

class CountdownTimer:
    def __init__(self):
        # 初始化主窗口，设置标题为“高考倒计时软件”
        self.root = tk.Tk()
        self.root.title("高考倒计时软件")
        self.root.overrideredirect(True)  # 移除窗口边框，使其无边框
        self.root.geometry('300x240')  # 设置窗口大小为300x240
        self.root.configure(bg='white')  # 设置初始背景为白色

        # 加载配置文件，包含主题颜色和透明度等设置
        self.config = self.load_config()
        self.root.attributes('-alpha', self.config.get('transparency', 0.8))  # 设置初始透明度

        # 设置圆角窗口（Windows特定）
        self.set_rounded_corners()

        # 当前目标索引初始化为0
        self.current_target_index = 0

        # 创建主框架，背景使用配置文件中的颜色
        self.main_frame = ttk.Frame(self.root, style='TFrame')
        self.main_frame.pack(padx=10, pady=5)

        # 创建标题标签，应用配置文件中的颜色
        self.title_label = ttk.Label(self.main_frame, text="", font=("微软雅黑", 14),
                                  foreground=self.config['colors']['title_label_fg'],
                                  background=self.config['colors']['title_label_bg'])
        self.title_label.pack()

        # 创建剩余天数标签，应用配置文件中的颜色
        self.days_label = ttk.Label(self.main_frame, text="", font=("微软雅黑", 30, "bold"),
                                 foreground=self.config['colors']['days_label_fg'],
                                 background=self.config['colors']['days_label_bg'])
        self.days_label.pack()

        # 创建倒计时标签，应用配置文件中的颜色
        self.countdown_label = ttk.Label(self.main_frame, text="", font=("微软雅黑", 16),
                                      foreground=self.config['colors']['countdown_label_fg'],
                                      background=self.config['colors']['countdown_label_bg'])
        self.countdown_label.pack()

        # 创建日期标签，应用配置文件中的颜色
        self.date_label = ttk.Label(self.main_frame, text="", font=("微软雅黑", 12),
                                 foreground=self.config['colors']['date_label_fg'],
                                 background=self.config['colors']['date_label_bg'])
        self.date_label.pack()

        # 初始化激励语句列表和当前语句
        self.default_mottos = [
            "不明白你们遇到好事，为什么要掐腿揉眼睛，真醒了怎么办？",
            "天道酬勤，未来可期。",
            "一分耕耘，一分收获。",
            "坚持就是胜利。",
            "相信自己，你就是最好的。",
            "付出终有回报，努力不会白费。"
        ]
        self.current_motto = self.get_motto()
        # 创建激励语句标签，应用配置文件中的颜色
        self.motto_label = ttk.Label(self.main_frame, text=self.current_motto, font=("微软雅黑", 10),
                                  foreground=self.config['colors']['motto_label_fg'],
                                  background=self.config['colors']['motto_label_bg'],
                                  wraplength=260)
        self.motto_label.pack()

        # 创建目标指示器框架，背景为白色
        self.dots_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.dots_frame.pack(pady=5)
        self.dot_labels = []

        # 背景图像相关变量初始化
        self.bg_image = None
        self.bg_label = None

        # 加载背景图像，应用动态调整功能
        self.load_background_image()

        # 控制面板初始化
        self.control_window = None
        self.color_labels = {}  # 用于存储颜色显示标签的字典，新增用于主题自定义

        # 绑定鼠标事件：左键拖动，右键显示控制面板
        self.root.bind('<Button-1>', self.save_last_click)
        self.root.bind('<B1-Motion>', self.drag_window)
        self.root.bind('<Button-3>', self.show_control_panel)

        # 开始更新倒计时
        self.update_countdown()

    def set_rounded_corners(self):
        # 设置窗口圆角，Windows特定功能
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style | win32con.WS_POPUP)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                             win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        self._region = win32gui.CreateRoundRectRgn(0, 0, 301, 241, 40, 40)
        win32gui.SetWindowRgn(hwnd, self._region, True)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, int(self.config.get('transparency', 0.8) * 255), win32con.LWA_ALPHA)

    def load_config(self):
        # 加载配置文件，若不存在则使用默认配置
        default_config = {
            'transparency': 0.8,
            'targets': [{'name': '高考', 'date': '2025-06-07', 'time': '00:00'}],
            'position': [100, 100],
            'topmost': False,
            'auto_start': False,
            'bg_image': '',
            'colors': {  # 新增：默认颜色设置，用于主题自定义
                'title_label_fg': '#4169E1',  # 标题标签前景色
                'title_label_bg': 'white',    # 标题标签背景色
                'days_label_fg': '#FF4500',   # 天数标签前景色
                'days_label_bg': 'white',     # 天数标签背景色
                'countdown_label_fg': '#758796',  # 倒计时标签前景色
                'countdown_label_bg': 'white',    # 倒计时标签背景色
                'date_label_fg': '#696969',   # 日期标签前景色
                'date_label_bg': 'white',     # 日期标签背景色
                'motto_label_fg': '#77C5E6',  # 激励语句标签前景色
                'motto_label_bg': 'white',    # 激励语句标签背景色
                'main_frame_bg': 'white'      # 主框架背景色
            }
        }
        config_path = 'daojishi_config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 确保配置文件包含所有默认键
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        return default_config

    def save_config(self):
        # 保存配置文件到JSON文件
        with open('daojishi_config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def save_last_click(self, event):
        # 保存最后一次点击的位置，用于拖动窗口
        self.x = event.x
        self.y = event.y

    def drag_window(self, event):
        # 拖动窗口到新位置，并保存位置到配置文件
        new_x = self.root.winfo_x() + (event.x - self.x)
        new_y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{new_x}+{new_y}")
        self.config['position'] = [new_x, new_y]
        self.save_config()

    def load_background_image(self):
        # 加载背景图像，并动态调整大小以适应窗口，保持纵横比
        if self.config['bg_image']:
            try:
                image = Image.open(self.config['bg_image'])  # 打开背景图像文件
                window_width, window_height = 300, 240  # 窗口固定大小
                image_width, image_height = image.size  # 获取图像原始尺寸

                # 计算图像和窗口的宽高比，决定缩放方式
                if image_width / image_height > window_width / window_height:
                    # 图像较宽，按窗口高度缩放
                    new_height = window_height
                    new_width = int((image_width / image_height) * new_height)
                    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
                    # 计算裁剪量，居中显示
                    crop_left = (new_width - window_width) // 2
                    crop_right = new_width - window_width - crop_left
                    cropped_image = resized_image.crop((crop_left, 0, new_width - crop_right, new_height))
                else:
                    # 图像较窄或等高，按窗口宽度缩放
                    new_width = window_width
                    new_height = int((image_height / image_width) * new_width)
                    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
                    # 计算裁剪量，居中显示
                    crop_top = (new_height - window_height) // 2
                    crop_bottom = new_height - window_height - crop_top
                    cropped_image = resized_image.crop((0, crop_top, new_width, new_height - crop_bottom))

                # 更新背景图像为调整后的版本
                self.bg_image = ImageTk.PhotoImage(cropped_image)
                if self.bg_label:
                    self.bg_label.config(image=self.bg_image)
                else:
                    self.bg_label = ttk.Label(self.root, image=self.bg_image)
                    self.bg_label.place(x=0, y=0)
            except Exception as e:
                # 处理加载图像失败的情况
                print(f"加载背景图像错误: {e}")
                self.config['bg_image'] = ''
                self.save_config()

    def show_control_panel(self, event):
        # 显示控制面板，包含主题颜色设置等功能
        if self.control_window is None or not self.control_window.winfo_exists():
            self.control_window = tk.Toplevel(self.root)
            self.control_window.title("设置")
            self.control_window.geometry('300x520')
            self.control_window.resizable(False, False)

            main_frame = ttk.Frame(self.control_window, padding=20)
            main_frame.pack(fill='both', expand=True)

            # 透明度设置框架
            transparency_frame = ttk.LabelFrame(main_frame, text="透明度设置", padding=10)
            transparency_frame.pack(fill='x', pady=(0, 10))
            transparency = ttk.Scale(
                transparency_frame,
                from_=0.1,
                to=1.0,
                value=self.config['transparency'],
                command=self.update_transparency
            )
            transparency.pack(fill='x', pady=5)

            # 目标管理框架
            targets_frame = ttk.LabelFrame(main_frame, text="倒计时目标管理", padding=10)
            targets_frame.pack(fill='both', expand=True)
            self.target_frame = ttk.Frame(targets_frame)
            self.target_frame.pack(fill='both', expand=True, pady=5)
            add_button = ttk.Button(targets_frame, text="添加新目标", command=self.add_target, width=15)
            add_button.pack(pady=10)

            # 背景图像选择按钮
            bg_button = ttk.Button(main_frame, text="选择背景图片", command=self.choose_background_image, width=15)
            bg_button.pack(pady=10)

            # 新增：主题颜色设置框架
            color_frame = ttk.LabelFrame(main_frame, text="主题颜色设置", padding=10)
            color_frame.pack(fill='x', pady=(0, 10))
            self.color_labels = {}  # 初始化颜色标签字典，用于显示当前颜色
            row = 0
            for element, color in self.config['colors'].items():
                label = ttk.Label(color_frame, text=f"{element} 颜色:")
                label.grid(row=row, column=0, padx=5, pady=5)
                current_color = ttk.Label(color_frame, background=color, width=2, height=1)
                current_color.grid(row=row, column=1, padx=5, pady=5)
                self.color_labels[element] = current_color  # 存储颜色标签
                button = ttk.Button(color_frame, text="更改", command=lambda elem=element: self.choose_color(elem))
                button.grid(row=row, column=2, padx=5, pady=5)
                row += 1

            # 其他设置框架
            options_frame = ttk.LabelFrame(main_frame, text="其他设置", padding=10)
            options_frame.pack(fill='x', pady=(0, 10))
            self.topmost_var = tk.BooleanVar(value=self.config.get('topmost', False))
            topmost_check = ttk.Checkbutton(
                options_frame,
                text="窗口置顶",
                variable=self.topmost_var,
                command=self.toggle_topmost
            )
            topmost_check.pack(anchor='w')
            self.auto_start_var = tk.BooleanVar(value=self.config.get('auto_start', False))
            auto_start_check = ttk.Checkbutton(
                options_frame,
                text="开机启动",
                variable=self.auto_start_var,
                command=self.toggle_auto_start
            )
            auto_start_check.pack(anchor='w')

            # 按钮框架
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill='x', pady=10)
            change_motto_button = ttk.Button(
                buttons_frame,
                text="切换激励语句",
                command=self.change_motto,
                width=15
            )
            change_motto_button.pack(side='left', padx=5)
            close_button = ttk.Button(
                buttons_frame,
                text="关闭程序",
                command=self.confirm_exit,
                foreground='red',
                width=15
            )
            close_button.pack(side='right', padx=5)

            self.update_target_list()

    def choose_color(self, element):
        # 打开颜色选择对话框，允许用户自定义颜色
        color = askcolor(title="选择颜色")[1]  # 获取颜色值，格式为"#RRGGBB"
        if color:
            self.config['colors'][element] = color  # 更新配置文件中的颜色值
            self.save_config()  # 保存配置文件
            if element.endswith('_fg'):  # 如果是前景色
                label_name = element.split('_')[0]
                getattr(self, f"{label_name}_label").config(foreground=color)  # 更新标签前景色
            elif element.endswith('_bg'):  # 如果是背景色
                label_name = element.split('_')[0]
                if label_name == 'main_frame':
                    self.main_frame.config(background=color)  # 更新主框架背景色
                else:
                    getattr(self, f"{label_name}_label").config(background=color)  # 更新标签背景色
            self.color_labels[element].config(background=color)  # 更新控制面板中的颜色显示

    def update_transparency(self, value):
        # 更新窗口透明度，并保存设置
        transparency = float(value)
        self.root.attributes('-alpha', transparency)
        self.config['transparency'] = transparency
        self.save_config()
        self.set_rounded_corners()

    def add_target(self):
        # 添加新倒计时目标，限制最多5个
        if len(self.config['targets']) >= 5:
            messagebox.showwarning("提示", "最多只能添加5个倒计时目标")
            return

        dialog = tk.Toplevel(self.control_window)
        dialog.title("添加目标")
        dialog.geometry('300x250')
        dialog.resizable(False, False)

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)

        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(name_frame, text="目标名称:", width=10, anchor='w').pack(side='left')
        name_entry = ttk.Entry(name_frame)
        name_entry.pack(side='left', fill='x', expand=True)

        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(date_frame, text="目标日期:", width=10, anchor='w').pack(side='left')
        year_var = tk.StringVar(value=str(datetime.datetime.now().year))
        year_spinbox = ttk.Spinbox(date_frame, from_=2024, to=2100, width=5, textvariable=year_var)
        year_spinbox.pack(side='left')
        ttk.Label(date_frame, text="年").pack(side='left', padx=2)
        month_var = tk.StringVar(value='01')
        month_spinbox = ttk.Spinbox(date_frame, from_=1, to=12, width=3, textvariable=month_var, format='%02.0f')
        month_spinbox.pack(side='left')
        ttk.Label(date_frame, text="月").pack(side='left', padx=2)
        day_var = tk.StringVar(value='01')
        day_spinbox = ttk.Spinbox(date_frame, from_=1, to=31, width=3, textvariable=day_var, format='%02.0f')
        day_spinbox.pack(side='left')
        ttk.Label(date_frame, text="日").pack(side='left', padx=2)

        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill='x', pady=(0, 20))
        ttk.Label(time_frame, text="目标时间:", width=10, anchor='w').pack(side='left')
        hour_var = tk.StringVar(value='00')
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=hour_var, format='%02.0f')
        hour_spinbox.pack(side='left')
        ttk.Label(time_frame, text=":").pack(side='left', padx=2)
        minute_var = tk.StringVar(value='00')
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=minute_var, format='%02.0f')
        minute_spinbox.pack(side='left')

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side='bottom', pady=(0, 10))

        def save():
            name = name_entry.get().strip()
            year = year_var.get().zfill(4)
            month = month_var.get().zfill(2)
            day = day_var.get().zfill(2)
            hour = hour_var.get().zfill(2)
            minute = minute_var.get().zfill(2)
            if not name:
                messagebox.showwarning("提示", "请输入目标名称")
                return
            date = f"{year}-{month}-{day}"
            try:
                datetime.datetime.strptime(f"{date} {hour}:{minute}", '%Y-%m-%d %H:%M')
                self.config['targets'].append({'name': name, 'date': date, 'time': f"{hour}:{minute}"})
                self.save_config()
                self.update_target_list()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("错误", "日期无效，请检查输入")

        ttk.Button(button_frame, text="取消", width=10, command=dialog.destroy).pack(side='left', padx=5)
        ttk.Button(button_frame, text="保存", width=10, command=save).pack(side='left', padx=5)

    def update_target_list(self):
        # 更新控制面板中的目标列表
        for widget in self.target_frame.winfo_children():
            widget.destroy()
        for i, target in enumerate(self.config['targets']):
            frame = ttk.Frame(self.target_frame)
            frame.pack(fill='x', pady=2)
            time_str = target.get('time', '00:00')
            ttk.Label(frame, text=f"{target['name']}: {target['date']} {time_str}", anchor='w').pack(side='left', fill='x', expand=True)
            ttk.Button(frame, text="删除", command=lambda idx=i: self.delete_target(idx), width=6).pack(side='right')

    def confirm_exit(self):
        # 确认退出程序
        if messagebox.askokcancel("确认", "确定要关闭程序吗？"):
            self.root.quit()
            self.root.destroy()

    def delete_target(self, index):
        # 删除目标并调整当前索引
        self.config['targets'].pop(index)
        if index == self.current_target_index:
            self.current_target_index = 0
        elif index < self.current_target_index:
            self.current_target_index -= 1
        self.save_config()
        self.update_target_list()
        self.update_countdown()

    def get_motto(self):
        # 从API获取激励语句，或使用默认语句
        try:
            response = requests.get('https://jkapi.com/api/one_yan?type=json', timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('content', random.choice(self.default_mottos))
        except (requests.RequestException, ValueError):
            return random.choice(self.default_mottos)

    def update_countdown(self):
        # 更新倒计时显示
        now = datetime.datetime.now()
        if not self.config['targets']:
            self.title_label.config(text="没有设置倒计时目标")
            self.days_label.config(text="请右键添加目标")
            self.countdown_label.config(text="")
            self.date_label.config(text="")
            self.update_count_label()
            self.root.after(1000, self.update_countdown)
            return

        if self.current_target_index >= len(self.config['targets']):
            self.current_target_index = 0

        target = self.config['targets'][self.current_target_index]
        time_str = target.get('time', '00:00')
        target_datetime = datetime.datetime.strptime(f"{target['date']} {time_str}", '%Y-%m-%d %H:%M')
        delta = target_datetime - now
        year = target_datetime.year

        self.title_label.config(text=f"距离{year}年{target['name']}")
        if delta.days < 0:
            self.days_label.config(text="0天（已结束）")
            self.countdown_label.config(text="0小时0分0秒")
        else:
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            seconds = delta.seconds % 60
            self.days_label.config(text=f"{days}天")
            self.countdown_label.config(text=f"{hours}小时{minutes}分{seconds}秒")

        self.date_label.config(text=target_datetime.strftime("%Y年%m月%d日"))
        self.update_count_label()
        self.root.after(1000, self.update_countdown)

    def update_count_label(self):
        # 更新目标指示器圆点
        for dot in self.dot_labels:
            dot.destroy()
        self.dot_labels.clear()
        if len(self.config['targets']) <= 1:
            return
        for i in range(len(self.config['targets'])):
            dot = ttk.Label(self.dots_frame, text="●", font=("微软雅黑", 8),
                         foreground='#D3D3D3' if i != self.current_target_index else '#4169E1',
                         background='white', cursor='hand2')
            dot.pack(side='left', padx=2)
            dot.bind('<Button-1>', lambda e, idx=i: self.switch_to_target(idx))
            self.dot_labels.append(dot)

    def switch_to_target(self, index):
        # 切换到指定目标
        self.current_target_index = index
        self.update_countdown()

    def toggle_topmost(self):
        # 切换窗口置顶状态
        is_topmost = self.topmost_var.get()
        self.root.attributes('-topmost', is_topmost)
        self.config['topmost'] = is_topmost
        self.save_config()

    def change_motto(self):
        # 切换显示的激励语句
        self.current_motto = self.get_motto()
        self.motto_label.config(text=self.current_motto)

    def toggle_auto_start(self):
        # 切换开机启动状态
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        app_path = os.path.abspath(sys.argv[0])
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if self.auto_start_var.get():
                winreg.SetValueEx(key, 'GaokaoCountdown', 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, 'GaokaoCountdown')
                except WindowsError:
                    pass
            winreg.CloseKey(key)
            self.config['auto_start'] = self.auto_start_var.get()
            self.save_config()
        except Exception as e:
            messagebox.showerror("错误", f"设置开机启动失败：{str(e)}")
            self.auto_start_var.set(not self.auto_start_var.get())

    def choose_background_image(self):
        # 选择背景图像文件
        file_path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            self.config['bg_image'] = file_path
            self.save_config()
            self.load_background_image()

    def run(self):
        # 运行应用程序，设置初始位置和状态
        if 'position' in self.config:
            self.root.geometry(f"+{self.config['position'][0]}+{self.config['position'][1]}")
        if self.config.get('topmost', False):
            self.root.attributes('-topmost', True)
        self.root.mainloop()

if __name__ == "__main__":
    app = CountdownTimer()
    app.run()