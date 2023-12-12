import os
import tkinter as tk
from tkinter.font import Font
import win32ui
import win32gui
import win32con
from text import TextEx

class Format:
    # 公开的方法
    def is_auto_line_break(self) -> bool: return self._auto_line_break.get()
    # 格式(O)的菜单项对应的方法
    def toggle_auto_line_break(self, auto_line_break:bool): 
        self._text['wrap'] = ('char' if auto_line_break else 'none')
    def enable_auto_line_break(self, auto_line_break:bool):
        if hasattr(self, "_auto_line_break") == False:
            self._auto_line_break = tk.BooleanVar(self._root)
            self._auto_line_break.set(auto_line_break)
            self.toggle_auto_line_break(self.is_auto_line_break())
        elif self.is_auto_line_break() != auto_line_break:
            self._auto_line_break.set(auto_line_break)
            self.toggle_auto_line_break(self.is_auto_line_break())
    def change_font(self): 
        dc = win32gui.GetDC(0)
        cf = win32ui.CreateFontDialog(
            self._logfont,
            win32con.CF_SCREENFONTS | win32con.CF_FORCEFONTEXIST, 
            dc,
            win32ui.CreateWindowFromHandle(self._root.winfo_id())
        )
        
        if cf.DoModal() == win32con.IDOK:
            self._logfont = cf.GetCurrentFont()
            self._font_size.set(round(cf.GetSize() / 10))  # GetSize方法返回的是像素的10倍
            # 这里改变了字体原始大小，因为字体的大小同时受view.py缩放比例的影响
            # 所以子类将会调用相应的方法来调用view.py的update_font_size方法，设置字体的实际大小
            
            self._font.configure(
                family=cf.GetFaceName(),
                slant="italic" if cf.IsItalic() else "roman",
                weight="bold" if cf.GetWeight() > 400 else "normal"
            )
            
        win32gui.ReleaseDC(0, dc)
    
    def __init__(self, root:tk.Tk, menu_bar:tk.Menu, text:TextEx, auto_line_break:bool, font:Font, logfont:dict, font_size:tk.IntVar=None) -> None:
        self._root = root
        self._text = text
        # 配置自动换行的选项
        self.enable_auto_line_break(auto_line_break)
        # 字体
        self._font = font
        self._logfont = logfont if logfont is not None else dict(
            height=0,
            name="",
            weight=400,
            italic=False
        )
        self._font_size =  font_size if font_size is not None else tk.IntVar(self._root)
        
        self.format_menu = tk.Menu(menu_bar, tearoff=False)
        self.format_menu.add_checkbutton(label="自动换行(W)", onvalue=True, offvalue=False, variable=self._auto_line_break, command=lambda: self.toggle_auto_line_break(self.is_auto_line_break()), underline=5)
        self.format_menu.add_command(label="字体(F)...", underline=3, command=self.change_font)
        
        menu_bar.add_cascade(label="格式(O)", menu=self.format_menu, underline=3)