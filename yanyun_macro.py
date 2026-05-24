import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys
import ctypes
import requests
import webbrowser
import keyboard
import mouse
import random


# ==========================================
# 🛡️ 强制获取管理员权限
# ==========================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# ==========================================
# 个人配置区
# ==========================================
AUTHOR_NAME = "南宫悠丶"
GUILD_AD = "🔥 寒塘渡鹤百业战 持续招人中 🔥"
CURRENT_VERSION = "v不知道"

GITHUB_ANNOUNCEMENT_URL = "https://raw.githubusercontent.com/你的用户名/你的仓库名/main/announcement.txt"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/你的用户名/你的仓库名/main/version.txt"
GITHUB_RELEASE_PAGE = "https://github.com/你的用户名/你的仓库名/releases"

DATA_FILE = "macros_data.json"
CONFIG_FILE = "config.json"
MAX_MACROS = 10

# 硬件级热键字典表 (Virtual-Key Codes)
VK_MAP = {
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74, 'F6': 0x75,
    'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
    'Home': 0x24, 'End': 0x23, 'PageUp': 0x21, 'PageDown': 0x22, 'Insert': 0x2D, 'Delete': 0x2E
}

# ==========================================
# 🎨 UI 配色与字体全局配置
# ==========================================
COLOR_BG = "#F5F7FA"
COLOR_SURFACE = "#FFFFFF"
COLOR_PRIMARY = "#FF5722"
COLOR_SUCCESS = "#4CAF50"
COLOR_DANGER = "#F44336"
COLOR_TEXT = "#333333"
COLOR_TEXT_MUTED = "#888888"

FONT_BASE = ("Microsoft YaHei", 10)
FONT_TITLE = ("Microsoft YaHei", 14, "bold")
FONT_TAB = ("Microsoft YaHei", 11, "bold")


class MacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"燕云十六声刷毒助手 {CURRENT_VERSION} (管理员已授权)")

        self.root.geometry("650x550")
        self.root.minsize(550, 450)
        self.root.config(bg=COLOR_BG)
        self.root.attributes("-topmost", True)

        self.macros = self.load_macros()
        self.load_config()
        self.current_recording = []
        self.is_recording = False
        self.is_playing = False
        self.play_thread = None

        self.setup_styles()
        self.setup_ui()
        self.start_hardware_hotkey_listener()
        self.update_ui_texts()

        threading.Thread(target=self.fetch_announcement, args=(True,), daemon=True).start()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TNotebook', background=COLOR_BG, borderwidth=0)
        self.style.configure('TNotebook.Tab', font=FONT_TAB, padding=[20, 8], background="#E1E4E8",
                             foreground=COLOR_TEXT_MUTED, borderwidth=0)
        self.style.map('TNotebook.Tab', background=[('selected', COLOR_SURFACE)],
                       foreground=[('selected', COLOR_PRIMARY)])
        self.style.configure('Card.TFrame', background=COLOR_SURFACE)
        self.style.configure('TCombobox', font=FONT_BASE, padding=5)

    def create_flat_button(self, parent, text, color, command, width=15):
        btn = tk.Button(parent, text=text, bg=color, fg="white", font=FONT_BASE,
                        relief="flat", borderwidth=0, cursor="hand2", width=width,
                        activebackground="#333333", activeforeground="white", command=command)
        return btn

    def load_macros(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_macros(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.macros, f, ensure_ascii=False, indent=4)

    def load_config(self):
        self.hk_record = 'F8'
        self.hk_play = 'F9'
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.hk_record = config.get("hk_record", 'F8')
                    self.hk_play = config.get("hk_play", 'F9')
            except Exception:
                pass

    def save_config(self):
        config = {"hk_record": self.hk_record, "hk_play": self.hk_play}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        banner = tk.Frame(self.root, bg=COLOR_PRIMARY, height=4)
        banner.pack(fill='x')

        window_frame = tk.Frame(self.root, bg=COLOR_SURFACE)
        window_frame.pack(fill='x', padx=15, pady=(15, 0))

        tk.Label(window_frame, text="🎯 目标游戏窗口:", font=FONT_BASE, bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(
            side='left', padx=(10, 5), pady=10)
        self.window_combo = ttk.Combobox(window_frame, state="readonly", width=25, font=FONT_BASE)
        self.window_combo.pack(side='left', padx=5, pady=10)

        btn_refresh_win = self.create_flat_button(window_frame, "刷新窗口", "#2196F3", self.refresh_windows, width=10)
        btn_refresh_win.pack(side='left', padx=10)
        self.refresh_windows()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=15, pady=15)

        self.tab_record = ttk.Frame(self.notebook, style='Card.TFrame')
        self.tab_play = ttk.Frame(self.notebook, style='Card.TFrame')
        self.tab_settings = ttk.Frame(self.notebook, style='Card.TFrame')

        self.notebook.add(self.tab_record, text=' 🔴 录制管理 ')
        self.notebook.add(self.tab_play, text=' ⚡ 运行中心 ')
        self.notebook.add(self.tab_settings, text=' ⚙️ 设置与公告 ')

        self.build_record_tab()
        self.build_play_tab()
        self.build_settings_tab()

    def update_ui_texts(self):
        if not self.is_recording:
            self.btn_record.config(text=f"开始录制 ({self.hk_record})")
            self.lbl_record_status.config(text="当前状态: 空闲" if not self.macros else "当前状态: 已就绪")

        if not self.is_playing:
            self.btn_play.config(text=f"🚀 启动循环运行 ({self.hk_play})")

        self.lbl_record_tip.config(
            text=f"💡 会自动切入目标窗口录制\n按 {self.hk_record} 开始/停止录制，仅录制有效点击防漂移")

    def build_record_tab(self):
        tk.Label(self.tab_record, text="已保存的宏列表", font=FONT_TITLE, bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(
            pady=(20, 10))

        list_frame = tk.Frame(self.tab_record, bg=COLOR_SURFACE, highlightbackground="#EEEEEE", highlightthickness=2)
        list_frame.pack(fill='x', padx=30, pady=5)

        self.macro_listbox = tk.Listbox(list_frame, height=6, font=FONT_BASE, relief="flat", bg="#FAFAFA",
                                        fg=COLOR_TEXT, selectbackground=COLOR_PRIMARY)
        self.macro_listbox.pack(fill='both', padx=5, pady=5)
        self.refresh_listbox()

        btn_frame = tk.Frame(self.tab_record, bg=COLOR_SURFACE)
        btn_frame.pack(pady=15)

        self.btn_record = self.create_flat_button(btn_frame, f"开始录制", COLOR_PRIMARY, self.toggle_record)
        self.btn_record.grid(row=0, column=0, padx=10, ipady=5)

        self.btn_delete = self.create_flat_button(btn_frame, "删除选中宏", COLOR_TEXT_MUTED, self.delete_macro)
        self.btn_delete.grid(row=0, column=1, padx=10, ipady=5)

        self.lbl_record_status = tk.Label(self.tab_record, text="当前状态: 空闲", font=FONT_BASE, fg=COLOR_TEXT_MUTED,
                                          bg=COLOR_SURFACE)
        self.lbl_record_status.pack(pady=5)

        self.lbl_record_tip = tk.Label(self.tab_record, text="💡 提示占位", fg="#999999", bg=COLOR_SURFACE,
                                       font=("Microsoft YaHei", 9), justify="center")
        self.lbl_record_tip.pack(pady=10)

    def build_play_tab(self):
        tk.Label(self.tab_play, text="选择要循环运行的宏", font=FONT_TITLE, bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(
            pady=(40, 15))

        self.play_combobox = ttk.Combobox(self.tab_play, state="readonly", width=35, font=FONT_BASE)
        self.play_combobox.pack(pady=10)
        self.play_combobox.option_add('*TCombobox*Listbox.font', FONT_BASE)
        self.refresh_combobox()

        self.btn_play = self.create_flat_button(self.tab_play, "🚀 启动循环运行", COLOR_SUCCESS, self.toggle_play,
                                                width=25)
        self.btn_play.pack(pady=30, ipady=10)

        self.lbl_play_status = tk.Label(self.tab_play, text="状态: 等待指令", font=("Microsoft YaHei", 12, "bold"),
                                        fg=COLOR_TEXT_MUTED, bg=COLOR_SURFACE)
        self.lbl_play_status.pack(pady=10)

    def build_settings_tab(self):
        hk_frame = tk.LabelFrame(self.tab_settings, text=" 快捷键自定义 ", font=FONT_BASE, bg=COLOR_SURFACE,
                                 fg=COLOR_TEXT)
        hk_frame.pack(fill='x', padx=30, pady=(20, 10))

        tk.Label(hk_frame, text="录制热键:", font=FONT_BASE, bg=COLOR_SURFACE).grid(row=0, column=0, padx=5, pady=10)
        self.combo_hk_rec = ttk.Combobox(hk_frame, values=list(VK_MAP.keys()), state="readonly", width=10,
                                         font=FONT_BASE)
        self.combo_hk_rec.set(self.hk_record)
        self.combo_hk_rec.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(hk_frame, text="运行热键:", font=FONT_BASE, bg=COLOR_SURFACE).grid(row=0, column=2, padx=(15, 5),
                                                                                    pady=10)
        self.combo_hk_play = ttk.Combobox(hk_frame, values=list(VK_MAP.keys()), state="readonly", width=10,
                                          font=FONT_BASE)
        self.combo_hk_play.set(self.hk_play)
        self.combo_hk_play.grid(row=0, column=3, padx=5, pady=10)

        btn_save_hk = self.create_flat_button(hk_frame, "保存键位", COLOR_SUCCESS, self.apply_hotkeys, width=10)
        btn_save_hk.grid(row=0, column=4, padx=15, ipady=2)

        tk.Label(self.tab_settings, text=f"✍️ 本程序由 {AUTHOR_NAME} 开发", font=FONT_TITLE, fg=COLOR_TEXT,
                 bg=COLOR_SURFACE).pack(pady=(15, 5))
        tk.Label(self.tab_settings, text=GUILD_AD, font=("Microsoft YaHei", 13, "bold"), fg=COLOR_PRIMARY,
                 bg=COLOR_SURFACE).pack(pady=5)
        tk.Label(self.tab_settings, text=f"当前版本: {CURRENT_VERSION}", font=FONT_BASE, fg=COLOR_TEXT_MUTED,
                 bg=COLOR_SURFACE).pack(pady=5)

        btn_frame = tk.Frame(self.tab_settings, bg=COLOR_SURFACE)
        btn_frame.pack(pady=10)

        btn_refresh_ad = self.create_flat_button(btn_frame, "刷新云端公告", "#2196F3",
                                                 lambda: threading.Thread(target=self.fetch_announcement,
                                                                          daemon=True).start())
        btn_refresh_ad.grid(row=0, column=0, padx=10, ipady=5)

        btn_update = self.create_flat_button(btn_frame, "检查应用更新", "#FF9800",
                                             lambda: threading.Thread(target=self.check_update, daemon=True).start())
        btn_update.grid(row=0, column=1, padx=10, ipady=5)

        txt_frame = tk.Frame(self.tab_settings, bg=COLOR_SURFACE, highlightbackground="#EEEEEE", highlightthickness=2)
        txt_frame.pack(fill='both', expand=True, padx=30, pady=(10, 20))

        self.txt_announcement = tk.Text(txt_frame, height=3, font=FONT_BASE, relief="flat", bg="#FAFAFA", fg=COLOR_TEXT,
                                        padx=10, pady=10)
        self.txt_announcement.pack(fill='both', expand=True)
        self.txt_announcement.insert(tk.END, "正在获取公告...")
        self.txt_announcement.config(state="disabled")

    def apply_hotkeys(self):
        new_rec = self.combo_hk_rec.get()
        new_play = self.combo_hk_play.get()
        if new_rec == new_play:
            return messagebox.showwarning("冲突", "录制热键和运行热键不能设置成同一个！")
        self.hk_record = new_rec
        self.hk_play = new_play
        self.save_config()
        self.update_ui_texts()
        messagebox.showinfo("成功", f"快捷键已保存！\n录制: {self.hk_record}\n运行: {self.hk_play}")

    def refresh_windows(self):
        titles = []

        def foreach_window(hwnd, lParam):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if title not in titles and "Default IME" not in title and "MSCTFIME" not in title:
                        titles.append(title)
            return True

        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        EnumWindows(EnumWindowsProc(foreach_window), 0)

        self.window_combo['values'] = titles
        if titles:
            for idx, t in enumerate(titles):
                if "燕云十六声" in t or "yanyun" in t.lower():
                    self.window_combo.current(idx)
                    return
            self.window_combo.current(0)

    def activate_target_window(self):
        target_title = self.window_combo.get()
        if not target_title: return False

        hwnd = ctypes.windll.user32.FindWindowW(None, target_title)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            return True
        return False

    def start_hardware_hotkey_listener(self):
        def listener():
            rec_pressed = False
            play_pressed = False

            while True:
                vk_rec = VK_MAP.get(self.hk_record, 0x77)
                vk_play = VK_MAP.get(self.hk_play, 0x78)

                if ctypes.windll.user32.GetAsyncKeyState(vk_rec) & 0x8000:
                    if not rec_pressed:
                        rec_pressed = True
                        self.root.after(0, self.toggle_record)
                else:
                    rec_pressed = False

                if ctypes.windll.user32.GetAsyncKeyState(vk_play) & 0x8000:
                    if not play_pressed:
                        play_pressed = True
                        self.root.after(0, self.toggle_play)
                else:
                    play_pressed = False

                time.sleep(0.01)

        threading.Thread(target=listener, daemon=True).start()

    def toggle_record(self):
        if self.is_playing: return messagebox.showwarning("警告", "正在运行宏，请先停止！")

        if not self.is_recording:
            if len(self.macros) >= MAX_MACROS:
                return messagebox.showwarning("上限提示", f"最多只能录制 {MAX_MACROS} 个宏。")

            if self.activate_target_window():
                time.sleep(0.5)

            self.is_recording = True
            self.current_recording = []
            self.btn_record.config(text=f"停止录制 ({self.hk_record})", bg=COLOR_DANGER)
            self.lbl_record_status.config(text=f"🔴 录制中... (按 {self.hk_record} 停止)", fg=COLOR_DANGER)

            self.record_start_time = time.time()
            keyboard.hook(self.keyboard_event_hook)
            mouse.hook(self.mouse_event_hook)
        else:
            self.is_recording = False
            keyboard.unhook_all()
            mouse.unhook_all()

            if self.current_recording and hasattr(self, 'record_start_time'):
                final_delay = time.time() - self.record_start_time
                self.current_recording.append({
                    "type": "wait",
                    "time": final_delay
                })

            self.btn_record.config(text=f"开始录制 ({self.hk_record})", bg=COLOR_PRIMARY)
            self.lbl_record_status.config(text="当前状态: 录制已保存", fg=COLOR_SUCCESS)
            self.save_recorded_macro()

    def keyboard_event_hook(self, event):
        ignore_keys = [self.hk_record.lower(), self.hk_record.lower().replace("page", "page ")]
        if str(event.name).lower() in ignore_keys:
            return

        self.current_recording.append({
            "type": "keyboard", "event_type": event.event_type,
            "name": event.name, "time": time.time() - self.record_start_time
        })

    def mouse_event_hook(self, event):
        if isinstance(event, mouse.ButtonEvent):
            self.current_recording.append({
                "type": "mouse", "event_type": event.event_type,
                "button": event.button, "time": time.time() - self.record_start_time
            })

    def save_recorded_macro(self):
        if not self.current_recording: return
        macro_name = f"刷毒路线_{len(self.macros) + 1}_{time.strftime('%H%M')}"
        self.macros[macro_name] = self.current_recording
        self.save_macros()
        self.refresh_listbox()
        self.refresh_combobox()

    def delete_macro(self):
        selection = self.macro_listbox.curselection()
        if not selection: return
        macro_name = self.macro_listbox.get(selection[0])
        if messagebox.askyesno("确认删除", f"确定要删除 '{macro_name}' 吗？"):
            del self.macros[macro_name]
            self.save_macros()
            self.refresh_listbox()
            self.refresh_combobox()

    def refresh_listbox(self):
        self.macro_listbox.delete(0, tk.END)
        for name in self.macros.keys():
            self.macro_listbox.insert(tk.END, name)

    def refresh_combobox(self):
        self.play_combobox['values'] = list(self.macros.keys())
        if self.macros:
            self.play_combobox.current(0)

    def toggle_play(self):
        if self.is_recording: return messagebox.showwarning("警告", "正在录制宏，请先停止！")

        selected_macro = self.play_combobox.get()
        if not selected_macro or selected_macro not in self.macros:
            return messagebox.showwarning("提示", "请先选择一个有效的路线！")

        self.is_playing = not self.is_playing

        if self.is_playing:
            if self.activate_target_window():
                time.sleep(0.5)

            self.btn_play.config(text=f"⏹ 停止运行 ({self.hk_play})", bg=COLOR_DANGER)
            self.lbl_play_status.config(text=f"▶ 正在运行: {selected_macro}", fg=COLOR_SUCCESS)
            self.play_thread = threading.Thread(target=self.play_macro_loop, args=(selected_macro,), daemon=True)
            self.play_thread.start()
        else:
            self.btn_play.config(text=f"🚀 启动循环运行 ({self.hk_play})", bg=COLOR_SUCCESS)
            self.lbl_play_status.config(text="状态: 已安全停止", fg=COLOR_TEXT_MUTED)

    def play_macro_loop(self, macro_name):
        events = self.macros[macro_name]
        while self.is_playing:
            last_time = 0
            for event in events:
                if not self.is_playing: break

                # 计算原本录制好的间隔时间
                raw_delay = event["time"] - last_time

                if raw_delay > 0:
                    # 加入 -15毫秒 到 +25毫秒 的随机波动
                    jitter = random.uniform(-0.015, 0.025)
                    # 确保随机减少后的延迟不会变成负数
                    final_delay = max(0.001, raw_delay + jitter)
                    time.sleep(final_delay)

                last_time = event["time"]

                if event["type"] == "wait":
                    continue

                try:
                    if event["type"] == "keyboard":
                        if event["event_type"] == "down":
                            keyboard.press(event["name"])
                        elif event["event_type"] == "up":
                            keyboard.release(event["name"])
                    elif event["type"] == "mouse":
                        if event["event_type"] == "down":
                            mouse.press(event["button"])
                        elif event["event_type"] == "up":
                            mouse.release(event["button"])
                except:
                    pass

            if self.is_playing: time.sleep(0.1)

    def fetch_announcement(self, silent=False):
        try:
            response = requests.get(GITHUB_ANNOUNCEMENT_URL, timeout=5)
            if response.status_code == 200:
                self.root.after(0, self.update_announcement_ui, response.text)
            else:
                self.root.after(0, self.update_announcement_ui, "未找到公告。")
        except:
            self.root.after(0, self.update_announcement_ui, "无法连接服务器，请检查网络。")

    def update_announcement_ui(self, text):
        self.txt_announcement.config(state="normal")
        self.txt_announcement.delete(1.0, tk.END)
        self.txt_announcement.insert(tk.END, text)
        self.txt_announcement.config(state="disabled")

    def check_update(self):
        try:
            response = requests.get(GITHUB_VERSION_URL, timeout=5)
            if response.status_code == 200:
                latest = response.text.strip()
                if latest != CURRENT_VERSION:
                    if messagebox.askyesno("发现新版本", f"发现新版本 {latest}。\n是否前往下载？"):
                        webbrowser.open(GITHUB_RELEASE_PAGE)
                else:
                    messagebox.showinfo("检查更新", "当前已是最新版本！")
        except:
            messagebox.showerror("网络错误", "检查更新失败。")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = MacroApp(root)
    root.mainloop()