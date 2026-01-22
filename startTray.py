import os
import subprocess
import sys
import threading
import re
from tkinter import Tk, Button, Label, Frame, messagebox, font
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ProcLableButtonsFrame(Frame):
    def __init__(self, parentFrame, program, font):
        super().__init__(parentFrame)
        self.red_color = '#8B0000'
        self.green_color = '#006400'
        self.program = program
        self.font = font
        self.label_text = program[self.program.rfind("/") + 1:]
        self.label_text_fix_size = 15
        self.label_text = self.label_text[:self.label_text_fix_size]
        self.label_text = self.label_text.ljust(self.label_text_fix_size)
        self.label = Label(self, text=f"{self.label_text} 未运行", bg=self.red_color, font=self.font)
        self.label.pack(side="left", padx=5)
        self.button_stop = Button(self, text="停止", command=self.stop_program, font=self.font)
        self.button_stop.pack(side="right", padx=5)
        self.button_start = Button(self, text="启动", command=self.start_program, font=self.font)
        self.button_start.pack(side="right", padx=5)
        self.process = None

    def cmd_to_args(self, cmd: str):
        """将命令字符串转换为列表，处理空格和引号"""
        args = []
        exe_path_end = cmd.find(".exe")
        if exe_path_end == -1:
            return args
        exe_path = cmd[:exe_path_end + 4]
        args.append(exe_path)
        args.extend(cmd[exe_path_end + 4:].split())
        return args

    def start_program(self):
        """启动程序，作为当前进程的子进程"""
        if self.process is not None and self.process.poll() is None:
            return
        cmd = self.program
        args = self.cmd_to_args(cmd)
        if len(args) == 0:
            messagebox.showerror("启动失败", f"无法解析命令: {cmd}")
            return
        if self.process is not None and self.process.poll() is None:
            messagebox.showerror("启动失败", f"程序 {self.label_text} 已在运行")
            return
        try:
            self.process = subprocess.Popen(args)
            self.label.config(text=f"{self.label_text} 运行中", bg=self.green_color)
        except Exception as e:
            messagebox.showerror("启动失败", f"{cmd}\n\n错误: {e}")
            self.process = None

    def stop_program(self):
        """停止程序"""
        if self.process is None or self.process.poll() is not None:
            # messagebox.showerror("停止失败", f"程序 {self.label_text} 未在运行")
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=3)
            if self.process.poll() is None:
                self.process.kill()
        except Exception as e:
            messagebox.showerror("停止失败", f"程序 {self.label_text} 停止失败\n\n错误: {e}")
            return
        self.update_process_state()

    def update_process_state(self):
        """更新进程状态"""
        if self.process is not None and self.process.poll() is None:
            self.label.config(text=f"{self.label_text} 运行中", bg=self.green_color)
        else:
            self.label.config(text=f"{self.label_text} 未运行", bg=self.red_color)
            self.process = None


class AppGUI:
    def __init__(self):
        self.root = None
        self.icon = None
        self.programs = [
            "cmd.exe /c set ENABLE_LOCAL_VIP=true && node D:\\code\\node\\modules\\node_modules\\@unblockneteasemusic\\server\\app.js -p 11111:11112",
            "D:\\software\\cloudmusic\\install\\CloudMusic\\cloudmusic.exe",
        ]
        self.frames = []

    def setup_gui(self):
        self.root = Tk()
        self.root.withdraw()
        self.font = font.Font(family="Hack Nerd Font", size=10)
        self.root.title("Work")
        self.width = 300
        self.line_dis = 30
        self.hight = 170 + len(self.programs) * self.line_dis
        windows_width = self.root.winfo_screenwidth()
        windows_height = self.root.winfo_screenheight()
        x = (windows_width - self.width - 200)
        y = (windows_height - self.hight - 80)
        self.root.geometry(f"{self.width}x{self.hight}+{x}+{y}")
        self.icon_path = BASE_DIR + "/avatar.ico"
        self.root.iconbitmap(self.icon_path)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        main_frame = Frame(self.root)
        main_frame.pack(pady=0)

        Button(main_frame, text="启动所有程序", command=self.start_all, font=self.font).pack(pady=5)

        for program in self.programs:
            row_frame = ProcLableButtonsFrame(main_frame, program, self.font)
            row_frame.pack(pady=5)
            self.frames.append(row_frame)

        Button(main_frame, text="退出（关闭所有子进程）", command=self.exit_app, font=self.font).pack(pady=5)

        self.root.withdraw()  # 初始隐藏

        menu = (
            item("全部启动", lambda _: self.start_all()),
            item('显示窗口', lambda _: self.show_window()),
            item('退出', lambda _: self.exit_app())
        )
        image = Image.open(self.icon_path)

        class MyIcon(pystray.Icon):
            self.left_click_func = None
            def __call__(self):
                # 在这里添加您的逻辑，比如显示/隐藏窗口
                if self.left_click_func is not None:
                    self.left_click_func()

        self.icon = MyIcon("launcher", image, "启动管理器", menu)
        # 设置左键点击事件
        self.icon.left_click_func = self.show_window

    def start_all(self):
        for frame in self.frames:
            frame.start_program()

    def kill_all_children(self):
        for frame in self.frames:
            frame.stop_program()

    def update_process_state(self):
        for frame in self.frames:
            frame.update_process_state()

    def show_window(self):
        """安全地显示窗口（确保在主线程中执行）"""
        if self.root:
            self.root.after(0, self._show_window)

    def _show_window(self):
        """实际显示窗口的方法（在主线程中调用）"""
        self.update_process_state()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self):
        """安全地隐藏窗口"""
        if self.root:
            self.root.after(0, self._hide_window)

    def _hide_window(self):
        """实际隐藏窗口的方法"""
        self.root.withdraw()

    def exit_app(self):
        # if messagebox.askokcancel("确认退出", "退出后所有子进程将被关闭，确定吗？"):
        #     self.kill_all_children()
        #     if self.icon:
        #         self.icon.stop()
        #     if self.root:
        #         self.root.destroy()
        self.kill_all_children()
        if self.icon:
            self.icon.stop()
        if self.root:
            self.root.destroy()

    def run(self):
        self.setup_gui()
        # 托盘在后台线程运行
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        self.root.mainloop()


if __name__ == "__main__":
    app = AppGUI()
    app.run()