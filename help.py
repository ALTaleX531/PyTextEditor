import os
import tkinter as tk
from ctypes import *
from ctypes import wintypes

class Help:
    # 帮助(H)的菜单项对应的方法
    def about(self):
        windll.shell32.ShellAboutW.argtypes =  [
            wintypes.HWND,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.HICON
        ]
        windll.shell32.ShellAboutW.restype = c_int
        windll.shell32.ShellAboutW(self._root.winfo_id(), "文本编辑器", "文本编辑器 1.0", None)
    
    def __init__(self, root:tk.Tk, menu_bar:tk.Menu) -> None:
        self._root = root
        self.help_menu = tk.Menu(menu_bar, tearoff=False)
        self.help_menu.add_command(label="查看帮助(H)", underline=5, state=tk.DISABLED)
        self.help_menu.add_command(label="发送反馈(F)", underline=5, state=tk.DISABLED)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="关于文本编辑器(A)", underline=8, command=self.about)
        
        menu_bar.add_cascade(label="帮助(H)", menu=self.help_menu, underline=3)