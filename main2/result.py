import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import json
import os
import random
import requests
from PIL import Image, ImageTk
import sys
import winreg
import win32gui
import win32con
import win32api

class CountdownTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("高考倒计时软件")
        self.root.overrideredirect(True)  # Borderless window
        self.root.geometry('300x240')
        self.root.configure(bg='white')

        # Background image variables
        self.bg_image = None
        self.bg_label = None

        # Load configuration
        self.config = self.load_config()
        self.root.attributes('-alpha', self.config.get('transparency', 0.8))

        # Set rounded corners
        self.set_rounded_corners()

        # Load background image
        self.load_background_image()

        # Current target index
        self.current_target_index = 0

        # Main frame
        self.main_frame = tk.Frame(self.root, bg='white')
        self.main_frame.pack(padx=10, pady=5)

        # Title label (first row)
        self.title_label = tk.Label(
            self.main_frame,
            text="",
            font=("微软雅黑", 14),
            fg='#4169E1',
            bg='white'
        )
        self.title_label.pack()

        # Days remaining label (second row)
        self.days_label = tk.Label(
            self.main_frame,
            text="",
            font=("微软雅黑", 30, "bold"),
            fg='#FF4500',
            bg='white'
        )
        self.days_label.pack()

        # Countdown label (third row)
        self.countdown_label = tk.Label(
            self.main_frame,
            text="",
            font=("微软雅黑", 16),
            fg='#758796',
            bg='white'
        )
        self.countdown_label.pack()

        # Date label (fourth row)
        self.date_label = tk.Label(
            self.main_frame,
            text="",
            font=("微软雅黑", 12),
            fg='#696969',
            bg='white'
        )
        self.date_label.pack()

        # Default mottos
        self.default_mottos = [
            "不明白你们遇到好事，为什么要掐腿揉眼睛，真醒了怎么办？",
            "天道酬勤，未来可期。",
            "一分耕耘，一分收获。",
            "坚持就是胜利。",
            "相信自己，你就是最好的。",
            "付出终有回报，努力不会白费。"
        ]
        self.current_motto = self.get_motto()

        # Motto label
        self.motto_label = tk.Label(
            self.main_frame,
            text=self.current_motto,
            font=("微软雅黑", 10),
            fg='#77C5E6',
            bg='white',
            wraplength=260,
            height=3
        )
        self.motto_label.pack()

        # Target indicator frame
        self.dots_frame = tk.Frame(self.main_frame, bg='white')
        self.dots_frame.pack(pady=5)
        self.dot_labels = []

        # Control panel
        self.control_window = None

        # Mouse bindings
        self.root.bind('<Button-1>', self.save_last_click)
        self.root.bind('<B1-Motion>', self.drag_window)
        self.root.bind('<Button-3>', self.show_control_panel)

        # Start countdown
        self.update_countdown()

    def set_rounded_corners(self):
        """Set window with rounded corners."""
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style | win32con.WS_POPUP)
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED
        )
        self._region = win32gui.CreateRoundRectRgn(0, 0, 301, 241, 40, 40)
        win32gui.SetWindowRgn(hwnd, self._region, True)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, int(self.config.get('transparency', 0.8) * 255), win32con.LWA_ALPHA)

    def load_config(self):
        """Load configuration from file or return default."""
        default_config = {
            'transparency': 0.8,
            'targets': [{'name': '高考', 'date': '2025-06-07', 'time': '00:00'}],
            'position': [100, 100],
            'topmost': False,
            'auto_start': False,
            'bg_image': ''
        }
        try:
            if os.path.exists('daojishi_config.json'):
                with open('daojishi_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if all(key in config for key in default_config):
                        return config
            return default_config
        except:
            return default_config

    def save_config(self):
        """Save configuration to file."""
        with open('daojishi_config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def save_last_click(self, event):
        """Store last click position for dragging."""
        self.x = event.x
        self.y = event.y

    def drag_window(self, event):
        """Drag the window to a new position."""
        new_x = self.root.winfo_x() + (event.x - self.x)
        new_y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{new_x}+{new_y}")
        self.config['position'] = [new_x, new_y]
        self.save_config()

    def load_background_image(self):
        """Load and display background image."""
        if self.config['bg_image']:
            try:
                image = Image.open(self.config['bg_image'])
                self.bg_image = ImageTk.PhotoImage(image)
                if self.bg_label:
                    self.bg_label.config(image=self.bg_image)
                else:
                    self.bg_label = tk.Label(self.root, image=self.bg_image)
                    self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                messagebox.showerror("错误", f"无法加载背景图片: {e}")
                self.config['bg_image'] = ''
                self.save_config()

    def show_control_panel(self, event):
        """Display the control panel."""
        if self.control_window is None or not tk.Toplevel.winfo_exists(self.control_window):
            self.control_window = tk.Toplevel(self.root)
            self.control_window.title("设置")
            self.control_window.geometry('300x520')
            self.control_window.resizable(False, False)

            main_frame = tk.Frame(self.control_window, padx=20, pady=10)
            main_frame.pack(fill='both', expand=True)

            # Transparency settings
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

            # Target management
            targets_frame = tk.LabelFrame(main_frame, text="倒计时目标管理", padx=10, pady=5)
            targets_frame.pack(fill='both', expand=True)
            self.target_frame = tk.Frame(targets_frame)
            self.target_frame.pack(fill='both', expand=True, pady=5)
            add_button = tk.Button(targets_frame, text="添加新目标", command=self.add_target, width=15)
            add_button.pack(pady=10)

            # Background image selection
            bg_button = tk.Button(main_frame, text="选择背景图片", command=self.choose_background_image, width=15)
            bg_button.pack(pady=10)

            # Other settings
            options_frame = tk.LabelFrame(main_frame, text="其他设置", padx=10, pady=5)
            options_frame.pack(fill='x', pady=(0, 10))
            self.topmost_var = tk.BooleanVar(value=self.config.get('topmost', False))
            topmost_check = tk.Checkbutton(
                options_frame,
                text="窗口置顶",
                variable=self.topmost_var,
                command=self.toggle_topmost
            )
            topmost_check.pack(anchor='w')
            self.auto_start_var = tk.BooleanVar(value=self.config.get('auto_start', False))
            auto_start_check = tk.Checkbutton(
                options_frame,
                text="开机启动",
                variable=self.auto_start_var,
                command=self.toggle_auto_start
            )
            auto_start_check.pack(anchor='w')

            # Buttons frame
            buttons_frame = tk.Frame(main_frame)
            buttons_frame.pack(fill='x', pady=10)
            change_motto_button = tk.Button(
                buttons_frame,
                text="切换激励语句",
                command=self.change_motto,
                width=15
            )
            change_motto_button.pack(side='left', padx=5)
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
        """Update window transparency."""
        transparency = float(value)
        self.root.attributes('-alpha', transparency)
        self.config['transparency'] = transparency
        self.save_config()
        self.set_rounded_corners()  # Reapply rounded corners with new transparency

    def add_target(self):
        """Add a new countdown target."""
        if len(self.config['targets']) >= 5:
            messagebox.showwarning("提示", "最多只能添加5个倒计时目标")
            return

        dialog = tk.Toplevel(self.control_window)
        dialog.title("添加目标")
        dialog.geometry('300x250')
        dialog.resizable(False, False)

        main_frame = tk.Frame(dialog, padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)

        # Name input
        name_frame = tk.Frame(main_frame)
        name_frame.pack(fill='x', pady=(0, 10))
        tk.Label(name_frame, text="目标名称:", width=10, anchor='w').pack(side='left')
        name_entry = tk.Entry(name_frame)
        name_entry.pack(side='left', fill='x', expand=True)

        # Date input
        date_frame = tk.Frame(main_frame)
        date_frame.pack(fill='x', pady=(0, 10))
        tk.Label(date_frame, text="目标日期:", width=10, anchor='w').pack(side='left')
        year_var = tk.StringVar(value=str(datetime.datetime.now().year))
        year_spinbox = ttk.Spinbox(date_frame, from_=2024, to=2100, width=5, textvariable=year_var)
        year_spinbox.pack(side='left')
        tk.Label(date_frame, text="年").pack(side='left', padx=2)
        month_var = tk.StringVar(value='01')
        month_spinbox = ttk.Spinbox(date_frame, from_=1, to=12, width=3, textvariable=month_var, format='%02.0f')
        month_spinbox.pack(side='left')
        tk.Label(date_frame, text="月").pack(side='left', padx=2)
        day_var = tk.StringVar(value='01')
        day_spinbox = ttk.Spinbox(date_frame, from_=1, to=31, width=3, textvariable=day_var, format='%02.0f')
        day_spinbox.pack(side='left')
        tk.Label(date_frame, text="日").pack(side='left', padx=2)

        # Time input
        time_frame = tk.Frame(main_frame)
        time_frame.pack(fill='x', pady=(0, 20))
        tk.Label(time_frame, text="目标时间:", width=10, anchor='w').pack(side='left')
        hour_var = tk.StringVar(value='00')
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=hour_var, format='%02.0f')
        hour_spinbox.pack(side='left')
        tk.Label(time_frame, text=":").pack(side='left', padx=2)
        minute_var = tk.StringVar(value='00')
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=minute_var, format='%02.0f')
        minute_spinbox.pack(side='left')

        # Buttons
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

        tk.Button(button_frame, text="取消", width=10, command=dialog.destroy).pack(side='left', padx=5)
        tk.Button(button_frame, text="保存", width=10, command=save).pack(side='left', padx=5)

    def update_target_list(self):
        """Update the target list in the control panel."""
        for widget in self.target_frame.winfo_children():
            widget.destroy()
        for i, target in enumerate(self.config['targets']):
            frame = tk.Frame(self.target_frame)
            frame.pack(fill='x', pady=2)
            time_str = target.get('time', '00:00')
            tk.Label(frame, text=f"{target['name']}: {target['date']} {time_str}", anchor='w').pack(side='left', fill='x', expand=True)
            tk.Button(frame, text="删除", command=lambda idx=i: self.delete_target(idx), width=6).pack(side='right')

    def confirm_exit(self):
        """Confirm and exit the application."""
        if messagebox.askokcancel("确认", "确定要关闭程序吗？"):
            self.root.quit()
            self.root.destroy()

    def delete_target(self, index):
        """Delete a target and adjust current index."""
        self.config['targets'].pop(index)
        if index == self.current_target_index:
            self.current_target_index = 0
        elif index < self.current_target_index:
            self.current_target_index -= 1
        self.save_config()
        self.update_target_list()
        self.update_countdown()

    def get_motto(self):
        """Fetch a motto from API or use default."""
        try:
            response = requests.get('https://jkapi.com/api/one_yan?type=json', timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('content', random.choice(self.default_mottos))
        except (requests.RequestException, ValueError):
            return random.choice(self.default_mottos)

    def update_countdown(self):
        """Update the countdown display."""
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
        """Update target indicator dots."""
        for dot in self.dot_labels:
            dot.destroy()
        self.dot_labels.clear()
        if len(self.config['targets']) <= 1:
            return
        for i in range(len(self.config['targets'])):
            dot = tk.Label(
                self.dots_frame,
                text="●",
                font=("微软雅黑", 8),
                fg='#D3D3D3' if i != self.current_target_index else '#4169E1',
                bg='white',
                cursor='hand2'
            )
            dot.pack(side='left', padx=2)
            dot.bind('<Button-1>', lambda e, idx=i: self.switch_to_target(idx))
            self.dot_labels.append(dot)

    def switch_to_target(self, index):
        """Switch to a specific target."""
        self.current_target_index = index
        self.update_countdown()

    def toggle_topmost(self):
        """Toggle window always-on-top."""
        is_topmost = self.topmost_var.get()
        self.root.attributes('-topmost', is_topmost)
        self.config['topmost'] = is_topmost
        self.save_config()

    def change_motto(self):
        """Change the displayed motto."""
        self.current_motto = self.get_motto()
        self.motto_label.config(text=self.current_motto)

    def toggle_auto_start(self):
        """Toggle auto-start on boot."""
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
            messagebox.showerror("错误", f"设置开机启动失败：{e}")
            self.auto_start_var.set(not self.auto_start_var.get())

    def choose_background_image(self):
        """Choose a background image."""
        file_path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            self.config['bg_image'] = file_path
            self.save_config()
            self.load_background_image()

    def run(self):
        """Run the application."""
        if 'position' in self.config:
            self.root.geometry(f"+{self.config['position'][0]}+{self.config['position'][1]}")
        if self.config.get('topmost', False):
            self.root.attributes('-topmost', True)
        self.root.mainloop()

if __name__ == "__main__":
    app = CountdownTimer()
    app.run()