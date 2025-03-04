import tkinter as tk
from tkinter import ttk
import datetime
import json
import os
import random
import requests
from tkinter import messagebox

class CountdownTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("高考倒计时软件")
        self.root.attributes('-alpha', 0.8)  # 设置初始透明度
        self.root.overrideredirect(True)  # 无边框窗口
        # 设置窗口大小
        self.root.geometry('300x240')
        # 设置窗口背景为白色
        self.root.configure(bg='white')
        # 设置窗口透明度
        self.root.attributes('-alpha', 0.8)

        # 设置圆角窗口
        self.set_rounded_corners()

    def set_rounded_corners(self):
        """设置窗口圆角"""
        import win32gui
        import win32con
        import win32api

        # 等待窗口完全加载
        self.root.update_idletasks()

        # 获取窗口句柄
        hwnd = self.root.winfo_id()

        # 获取窗口当前样式
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

        # 设置窗口样式
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_STYLE,
            style | win32con.WS_POPUP
        )

        # 设置窗口为圆角并启用分层窗口
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED
        )

        # 设置窗口为圆角
        self._region = win32gui.CreateRoundRectRgn(
            0, 0,
            self.root.winfo_width() + 1,
            self.root.winfo_height() + 1,
            40, 40  # 圆角的宽度和高度
        )
        win32gui.SetWindowRgn(hwnd, self._region, True)

        # 设置窗口透明色键，使圆角外区域完全透明
        win32gui.SetLayeredWindowAttributes(hwnd, 0, int(0.8 * 255), win32con.LWA_ALPHA)

        # 保存窗口位置用的变量
        self.x = 0
        self.y = 0

        # 加载配置
        self.config = self.load_config()

        # 当前显示的目标索引
        self.current_target_index = 0

        # 主框架
        self.main_frame = tk.Frame(self.root, bg='white')
        self.main_frame.pack(padx=10, pady=5)

        # 标题显示（第一行）
        self.title_label = tk.Label(
            self.main_frame,
            text="",  # 将在update_countdown中设置
            font=("微软雅黑", 14),
            fg='#4169E1',
            bg='white'
        )
        self.title_label.pack()

        # 剩余天数显示（第二行）
        self.days_label = tk.Label(
            self.main_frame,
            text="",
            font=("微软雅黑", 30, "bold"),
            fg='#FF4500',
            bg='white'
        )
        self.days_label.pack()

        # 倒计时显示（第三行）
        self.countdown_label = tk.Label(
            self.main_frame,
            text="",
            font=("微软雅黑", 16, ),
            fg='#758796',
            bg='white'
        )
        self.countdown_label.pack()

        # 日期显示（第四行）
        self.date_label = tk.Label(
            self.main_frame,
            text="",
            font=("微软雅黑", 12),
            fg='#696969',
            bg='white'
        )
        self.date_label.pack()

        # 默认激励语句列表
        self.default_mottos = [
            "不明白你们遇到好事，为什么要掐腿揉眼睛，真醒了怎么办？",
            "天道酬勤，未来可期。",
            "一分耕耘，一分收获。",
            "坚持就是胜利。",
            "相信自己，你就是最好的。",
            "付出终有回报，努力不会白费。"
        ]

        # 当前使用的激励语句
        self.current_motto = self.get_motto()

        # 激励文字
        self.motto_label = tk.Label(
            self.main_frame,
            text=self.current_motto,
            font=("微软雅黑", 10),
            fg='#77C5E6',
            bg='white',
            wraplength=260,  # 设置较小的换行宽度以确保两行显示
            height=3  # 设置固定高度为2行
        )
        self.motto_label.pack()
        # 添加切换按钮框架
        self.button_frame = tk.Frame(self.main_frame, bg='white')
        self.button_frame.pack(pady=5)

        # 添加目标指示器框架
        self.dots_frame = tk.Frame(self.button_frame, bg='white')
        self.dots_frame.pack()

        # 存储圆点标签的列表
        self.dot_labels = []

        # 控制面板
        self.control_window = None

        # 绑定鼠标事件
        self.root.bind('<Button-1>', self.save_last_click)
        self.root.bind('<B1-Motion>', self.drag_window)
        self.root.bind('<Button-3>', self.show_control_panel)

        # 开始倒计时
        self.update_countdown()

    # 修复所有方法的缩进，确保它们都是 CountdownTimer 类的直接方法
    def load_config(self):
        default_config = {
            'transparency': 0.8,
            'targets': [
                {
                    'name': '高考',
                    'date': '2025-06-07'
                }
            ],
            'position': [100, 100],
            'topmost': False,
            'auto_start': False
        }

        try:
            if os.path.exists('gaokao_config.json'):
                with open('gaokao_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if not all(key in config for key in default_config.keys()):
                        return default_config
                    return config
            return default_config
        except:
            return default_config

    def save_config(self):
        with open('gaokao_config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def save_last_click(self, event):
        self.x = event.x
        self.y = event.y

    def drag_window(self, event):
        new_x = self.root.winfo_x() + (event.x - self.x)
        new_y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{new_x}+{new_y}")
        self.config['position'] = [new_x, new_y]
        self.save_config()

    def show_control_panel(self, event):
        if self.control_window is None or not tk.Toplevel.winfo_exists(self.control_window):
            self.control_window = tk.Toplevel(self.root)
            self.control_window.title("设置")
            self.control_window.geometry('300x520')
            self.control_window.resizable(False, False)

            # 创建主框架并添加内边距
            main_frame = tk.Frame(self.control_window, padx=20, pady=10)
            main_frame.pack(fill='both', expand=True)

            # 透明度控制区域
            transparency_frame = tk.LabelFrame(main_frame, text="透明度设置", padx=10, pady=5)
            transparency_frame.pack(fill='x', pady=(0, 10))

            transparency = ttk.Scale(
                transparency_frame,
                from_=0.1,
                to=1.0,
                value=self.config['transparency'],
                command=self.update_transparency
            )
            transparency.pack(fill='x', pady=5)

            # 目标管理区域
            targets_frame = tk.LabelFrame(main_frame, text="倒计时目标管理", padx=10, pady=5)
            targets_frame.pack(fill='both', expand=True)

            # 目标列表框架
            self.target_frame = tk.Frame(targets_frame)
            self.target_frame.pack(fill='both', expand=True, pady=5)

            # 添加目标按钮
            add_button = tk.Button(
                targets_frame,
                text="添加新目标",
                command=self.add_target,
                width=15
            )
            add_button.pack(pady=10)

            # 添加窗口置顶和开机启动选项
            options_frame = tk.LabelFrame(main_frame, text="其他设置", padx=10, pady=5)
            options_frame.pack(fill='x', pady=(0, 10))

            # 窗口置顶选项
            self.topmost_var = tk.BooleanVar(value=self.config.get('topmost', False))
            topmost_check = tk.Checkbutton(
                options_frame,
                text="窗口置顶",
                variable=self.topmost_var,
                command=self.toggle_topmost
            )
            topmost_check.pack(anchor='w')

            # 开机启动选项
            self.auto_start_var = tk.BooleanVar(value=self.config.get('auto_start', False))
            auto_start_check = tk.Checkbutton(
                options_frame,
                text="开机启动",
                variable=self.auto_start_var,
                command=self.toggle_auto_start
            )
            auto_start_check.pack(anchor='w')
            # 添加切换激励语句和关闭程序按钮的框架
            buttons_frame = tk.Frame(main_frame)
            buttons_frame.pack(fill='x', pady=10)

            # 添加切换激励语句按钮（靠左）
            change_motto_button = tk.Button(
                buttons_frame,
                text="切换激励语句",
                command=self.change_motto,
                width=15
            )
            change_motto_button.pack(side='left', padx=5)

            # 添加关闭程序按钮（靠右）
            close_button = tk.Button(
                buttons_frame,
                text="关闭程序",
                command=self.confirm_exit,
                fg='red',
                width=15
            )
            close_button.pack(side='right', padx=5)

            self.update_target_list()
    def update_transparency(self, value):
        transparency = float(value)
        self.root.attributes('-alpha', transparency)
        self.config['transparency'] = transparency
        self.save_config()

    def add_target(self):
        # 检查目标数量是否已达到上限
        if len(self.config['targets']) >= 5:
            tk.messagebox.showwarning("提示", "最多只能添加5个倒计时目标")
            return

        dialog = tk.Toplevel(self.control_window)
        dialog.title("添加目标")
        dialog.geometry('300x250')
        dialog.resizable(False, False)

        # 创建主框架
        main_frame = tk.Frame(dialog, padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)

        # 名称输入区域
        name_frame = tk.Frame(main_frame)
        name_frame.pack(fill='x', pady=(0, 10))
        tk.Label(name_frame, text="目标名称:", width=10, anchor='w').pack(side='left')
        name_entry = tk.Entry(name_frame)
        name_entry.pack(side='left', fill='x', expand=True)

        # 日期输入区域
        date_frame = tk.Frame(main_frame)
        date_frame.pack(fill='x', pady=(0, 10))
        tk.Label(date_frame, text="目标日期:", width=10, anchor='w').pack(side='left')

        # 年份输入
        year_var = tk.StringVar(value=str(datetime.datetime.now().year))
        year_spinbox = ttk.Spinbox(date_frame, from_=2024, to=2100, width=5, textvariable=year_var)
        year_spinbox.pack(side='left')
        tk.Label(date_frame, text="年").pack(side='left', padx=2)

        # 月份输入
        month_var = tk.StringVar(value='01')
        month_spinbox = ttk.Spinbox(date_frame, from_=1, to=12, width=3, textvariable=month_var, format='%02.0f')
        month_spinbox.pack(side='left')
        tk.Label(date_frame, text="月").pack(side='left', padx=2)

        # 日期输入
        day_var = tk.StringVar(value='01')
        day_spinbox = ttk.Spinbox(date_frame, from_=1, to=31, width=3, textvariable=day_var, format='%02.0f')
        day_spinbox.pack(side='left')
        tk.Label(date_frame, text="日").pack(side='left', padx=2)

        # 时间输入区域
        time_frame = tk.Frame(main_frame)
        time_frame.pack(fill='x', pady=(0, 20))
        tk.Label(time_frame, text="目标时间:", width=10, anchor='w').pack(side='left')

        # 小时输入
        hour_var = tk.StringVar(value='00')
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=hour_var, format='%02.0f')
        hour_spinbox.pack(side='left')
        tk.Label(time_frame, text=":").pack(side='left', padx=2)

        # 分钟输入
        minute_var = tk.StringVar(value='00')
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=minute_var, format='%02.0f')
        minute_spinbox.pack(side='left')

        # 按钮区域
        button_frame = tk.Frame(main_frame)
        button_frame.pack(side='bottom', pady=(0, 10))

        def save():
            name = name_entry.get().strip()
            year = year_var.get().zfill(4)
            month = month_var.get().zfill(2)
            day = day_var.get().zfill(2)
            hour = hour_var.get().zfill(2)
            minute = minute_var.get().zfill(2)

            if not name:
                tk.messagebox.showwarning("提示", "请输入目标名称")
                return

            date = f"{year}-{month}-{day}"

            try:
                datetime.datetime.strptime(f"{date} {hour}:{minute}", '%Y-%m-%d %H:%M')
                self.config['targets'].append({
                    'name': name,
                    'date': date,
                    'time': f"{hour}:{minute}"
                })
                self.save_config()
                self.update_target_list()
                dialog.destroy()
            except ValueError:
                tk.messagebox.showerror("错误", "日期无效，请检查输入")

        # 取消按钮
        tk.Button(button_frame, text="取消", width=10, command=dialog.destroy).pack(side='left', padx=5)
        # 保存按钮
        tk.Button(button_frame, text="保存", width=10, command=save).pack(side='left', padx=5)

    def update_target_list(self):
        for widget in self.target_frame.winfo_children():
            widget.destroy()

        for i, target in enumerate(self.config['targets']):
            frame = tk.Frame(self.target_frame)
            frame.pack(fill='x', pady=2)

            time_str = target.get('time', '00:00')
            tk.Label(
                frame,
                text=f"{target['name']}: {target['date']} {time_str}",
                anchor='w'
            ).pack(side='left', fill='x', expand=True)

            tk.Button(
                frame,
                text="删除",
                command=lambda idx=i: self.delete_target(idx),
                width=6
            ).pack(side='right')

    def confirm_exit(self):
        if tk.messagebox.askokcancel("确认", "确定要关闭程序吗？"):
            self.root.quit()
            self.root.destroy()

    def delete_target(self, index):
        self.config['targets'].pop(index)
        # 如果删除的是当前显示的目标，调整当前索引
        if index == self.current_target_index:
            self.current_target_index = 0
        elif index < self.current_target_index:
            self.current_target_index -= 1

        self.save_config()
        self.update_target_list()
        self.update_countdown()

    def get_motto(self):
        """获取激励语句，优先从API获取，失败则使用默认语句"""
        try:
            response = requests.get('https://jkapi.com/api/one_yan?type=json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('content', random.choice(self.default_mottos))
        except:
            pass
        return random.choice(self.default_mottos)

    def update_countdown(self):
        now = datetime.datetime.now()

        # 不再每次更新激励语句
        # self.motto_label.config(text=self.get_motto())

        # 检查是否有目标
        if not self.config['targets']:
            self.title_label.config(text="没有设置倒计时目标")
            self.days_label.config(text="请右键添加目标")
            self.countdown_label.config(text="")
            self.date_label.config(text="")
            self.update_count_label()
            self.root.after(1000, self.update_countdown)
            return

        # 确保当前索引在有效范围内
        if self.current_target_index >= len(self.config['targets']):
            self.current_target_index = 0

        # 只显示当前选中的目标
        target = self.config['targets'][self.current_target_index]
        time_str = target.get('time', '00:00')
        target_datetime = datetime.datetime.strptime(f"{target['date']} {time_str}", '%Y-%m-%d %H:%M')
        delta = target_datetime - now

        # 获取年份
        year = target_datetime.year

        # 更新标题（第一行）- 距离2025年"项目标题"还有：
        self.title_label.config(text=f"距离{year}年{target['name']}")

        # 处理目标日期已过的情况
        if delta.days < 0:
            # 第二行 - 显示剩余天数
            self.days_label.config(text="0天（已结束）")
            # 第三行 - 显示倒计时
            self.countdown_label.config(text="0小时0分0秒")
        else:
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            seconds = delta.seconds % 60

            # 第二行 - 显示剩余天数
            self.days_label.config(text=f"{days}天")
            # 第三行 - 显示倒计时
            self.countdown_label.config(text=f"{hours}小时{minutes}分{seconds}秒")

        # 第四行 - 显示倒计时日期
        formatted_date = target_datetime.strftime("%Y年%m月%d日")
        self.date_label.config(text=formatted_date)

        self.update_count_label()
        self.root.after(1000, self.update_countdown)
    def update_count_label(self):
        """更新目标指示器显示"""
        total = len(self.config['targets'])

        # 清除现有的圆点
        for dot in self.dot_labels:
            dot.destroy()
        self.dot_labels.clear()

        # 如果只有一个目标或没有目标，不显示圆点
        if total <= 1:
            return

        # 为每个目标创建一个圆点
        for i in range(total):
            dot = tk.Label(
                self.dots_frame,
                text="●",
                font=("微软雅黑", 8),
                fg='#D3D3D3' if i != self.current_target_index else '#4169E1',
                bg='white',
                cursor='hand2'  # 添加手型光标
            )
            dot.pack(side='left', padx=2)
            # 绑定点击事件
            dot.bind('<Button-1>', lambda e, idx=i: self.switch_to_target(idx))
            self.dot_labels.append(dot)
    def switch_to_target(self, index):
        """切换到指定目标"""
        if self.config['targets']:
            self.current_target_index = index
            self.update_countdown()
    def toggle_topmost(self):
        """切换窗口置顶状态"""
        is_topmost = self.topmost_var.get()
        self.root.attributes('-topmost', is_topmost)
        self.config['topmost'] = is_topmost
        self.save_config()

    def change_motto(self):
        """切换激励语句"""
        new_motto = self.get_motto()
        self.current_motto = new_motto
        self.motto_label.config(text=new_motto)

    def toggle_auto_start(self):
        """切换开机启动状态"""
        import winreg
        key_path = r'Software\\Microsoft\\Windows\\CurrentVersion\\Run'
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

    def run(self):
        # 设置初始位置
        if 'position' in self.config:
            self.root.geometry(f"+{self.config['position'][0]}+{self.config['position'][1]}")

        # 设置初始透明度
        self.root.attributes('-alpha', self.config['transparency'])

        # 设置窗口置顶状态
        if self.config.get('topmost', False):
            self.root.attributes('-topmost', True)

        self.root.mainloop()

if __name__ == "__main__":
    app = CountdownTimer()
    app.run()