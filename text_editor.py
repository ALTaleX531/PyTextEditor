# 该文件负责文本编辑器的实现和逻辑整合
import tkinter as tk
from tkinter.font import Font
import utils

from text import TextEx
from file import File
from edit import Edit
from format import Format
from view import View
from help import Help
        
# underline是指label中要加入下划线字符的索引
# 通常用Alt快捷键调出后，会再次按下特定的键触发指定功能
# 而加了下划线的字符就是要按下的键
        
class TextEditor(tk.Tk):
    def run(self): self.mainloop()
    # 重写new_window方法
    # 因为本身File没有TextEditor的声明，无法创建实例
    def new_window(self): TextEditor(self._format.is_auto_line_break(), self._view.get_syntax_highlight().get(), self._view.get_status_bar().get()); self.run()
    # 在字体原始大小发生改变时被调用
    def __on_font_size_changed(self, var, index, mode):
        if self._view is not None: self._view.update_font_real_size()
        self._text.configure(tabs=self._font.measure('    '))
    # 用于更新字体真实大小，提供给View调用
    def update_font_real_size(self, font_size:float):
        self._font.configure(size=round(font_size))
    # 缩放比例发生更改
    def __on_zoom_factor_changed(self, var, index, mode):
        if self._view is not None: self._view.status_bar_zoom_factor.configure(text=str(self._view.get_zoom_factor().get()) + '%')
    def __on_file_path_changed(self, var, index, mode):
        if self._file.get_opened_file_path().get():
            if self._view is not None: self._encoding_menu.entryconfigure(index=5, state=tk.NORMAL)
        else:
            if self._view is not None: self._encoding_menu.entryconfigure(index=5, state=tk.DISABLED)
        
    def __init__(self, auto_line_break:bool, syntax_highlight:bool, status_bar:bool) -> None:
        # 创建主窗口
        tk.Tk.__init__(self)
        self.geometry('1000x480')
        # 创建菜单栏
        self._menu_bar = tk.Menu(self, tearoff=False)
        self.config(menu=self._menu_bar)
        # 文本编辑框
        # 配置初始字体
        self._font_size = tk.IntVar(master=self, value=9)
        self._font_size.trace_add("write", self.__on_font_size_changed)
        self._font = Font(
            root=self,
            family="微软雅黑", 
            size=self._font_size.get()
        )
        # 配置LOGFONT字典
        # 选择字体对话框需要
        self._logfont = {
            "height": self._font_size.get() * 2,
            "name": self._font["family"],
            "weight": 700 if self._font["weight"] == "bold" else 400,
            "italic": True if self._font["slant"] == "italic" else False
        }
        
        # 配置文本编辑框
        # 1Tab=4Space
        # 最大撤销次数不限制
        # 允许编辑框在另一个部件获得焦点时保持选择状态
        self._text = TextEx(
            self, 
            relief=tk.FLAT,
            wrap=tk.NONE,
            font=self._font, 
            exportselection=False, 
            undo=True, 
            maxundo=-1,
            tabs=self._font.measure('    ')
        )
        self._text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # 配置颜色
        self._text.tag_config("sel", foreground="", background="#ADD6FF")
        self._text['background'] = "#FFFFFF"
        self._text['inactiveselect'] = "#E5EBF1"    # 非活动状态的选择
        
        self._file = None
        self._edit = None
        self._format = None
        self._view = None
        self._help = None
        # 初始化文件功能
        self._file = File(
            self, 
            self._menu_bar, 
            self._text,
            self.new_window
        )
        # 初始化编辑功能
        self._edit = Edit(
            self, 
            self._menu_bar, 
            self._text
        )
        # 初始化格式功能
        self._format = Format(
            self, 
            self._menu_bar, 
            self._text,
            auto_line_break,
            self._font,
            self._logfont, 
            self._font_size
        )
        # 初始化视图功能
        self._view = View(
            self, 
            self._menu_bar, 
            self._text,
            self._font_size,
            syntax_highlight,
            status_bar,
            self.update_font_real_size
        )
        # 初始化帮助功能
        self._help = Help(
            self,
            self._menu_bar
        )
        
        # 注册文件路径改变回调
        if self._file is not None: self._file.get_opened_file_path().trace_add("write", self.__on_file_path_changed)
        # 配置状态栏的按钮
        if self._view is not None:
            self._view.status_bar_encoding["textvariable"] = self._file.get_encoding()
            self._view.status_bar_line_ending["textvariable"] = self._file.get_line_ending()
            
            self._line_ending_menu = tk.Menu(self._view.status_bar_line_ending, tearoff=False)
            self._line_ending_menu.add_radiobutton(label=utils.CRLF, value=utils.CRLF, underline=10, variable=self._file.get_line_ending(), command=lambda: self._file.request_line_ending(utils.CRLF))
            self._line_ending_menu.add_radiobutton(label=utils.LF, value=utils.LF, underline=6, variable=self._file.get_line_ending(), command=lambda: self._file.request_line_ending(utils.LF))
            self._line_ending_menu.add_radiobutton(label=utils.CR, value=utils.CR, underline=11, variable=self._file.get_line_ending(), command=lambda: self._file.request_line_ending(utils.CR))
            self._view.status_bar_line_ending['menu'] = self._line_ending_menu
            
            # TO-DO
            # 菜单在被选中后会有写入一次encoding变量的意外行为
            # 我们希望只调用File给定的request_encoding方法
            self._encoding_menu = tk.Menu(self._view.status_bar_encoding, tearoff=False)
            self._encoding_menu.add_radiobutton(
                label="保存为 UTF-8", 
                value="UTF-8",
                underline=4, 
                variable=self._file.get_encoding(), 
                command=lambda: self._file.request_encoding("UTF-8")
            )
            self._encoding_menu.add_radiobutton(
                label="保存为 带有BOM的UTF-8", 
                value="UTF-8-SIG",
                underline=6, 
                variable=self._file.get_encoding(), 
                command=lambda: self._file.request_encoding("UTF-8-SIG")
            )
            self._encoding_menu.add_radiobutton(
                label="保存为 UTF-16", 
                value="UTF-16",
                underline=5, 
                variable=self._file.get_encoding(), 
                command=lambda: self._file.request_encoding("UTF-16")
            )
            self._encoding_menu.add_radiobutton(
                label="保存为 ANSI", 
                value="ASCII",
                underline=4, 
                variable=self._file.get_encoding(), 
                command=lambda: self._file.request_encoding("ASCII")
            )
            self._encoding_menu.add_radiobutton(
                label="保存为 GB2312", 
                value="GB2312",
                underline=4, 
                variable=self._file.get_encoding(), 
                command=lambda: self._file.request_encoding("GB2312")
            )
            # 编码重新打开
            self._reopen_menu = tk.Menu(self._encoding_menu, tearoff=False)
            self._reopen_menu.add_command(label="UTF-8", underline=0, command=lambda: self._file.reopen("UTF-8"))
            self._reopen_menu.add_command(label="UTF-8-SIG", underline=0, command=lambda: self._file.reopen("UTF-8-SIG"))
            self._reopen_menu.add_command(label="UTF-16", underline=0, command=lambda: self._file.reopen("UTF-16"))
            self._reopen_menu.add_command(label="ANSI", underline=0, command=lambda: self._file.reopen("ASCII"))
            self._reopen_menu.add_command(label="GB2312", underline=0, command=lambda: self._file.reopen("GB2312"))
            self._encoding_menu.add_cascade(label="通过编码重新打开(R)...", underline=9, state=tk.DISABLED, menu=self._reopen_menu)
            self._view.status_bar_encoding['menu'] = self._encoding_menu
            # 缩放
            self._zoom_factor_menu = tk.Menu(self._view.status_bar_zoom_factor, tearoff=False)
            self._zoom_factor_menu.add_radiobutton(label="20%", variable=self._view.get_zoom_factor(), value=20)
            self._zoom_factor_menu.add_radiobutton(label="50%", variable=self._view.get_zoom_factor(), value=50)
            self._zoom_factor_menu.add_radiobutton(label="70%", variable=self._view.get_zoom_factor(), value=70)
            self._zoom_factor_menu.add_radiobutton(label="100%", variable=self._view.get_zoom_factor(), value=100)
            self._zoom_factor_menu.add_radiobutton(label="150%", variable=self._view.get_zoom_factor(), value=150)
            self._zoom_factor_menu.add_radiobutton(label="200%", variable=self._view.get_zoom_factor(), value=200)
            self._zoom_factor_menu.add_radiobutton(label="400%", variable=self._view.get_zoom_factor(), value=400)
            self._view.status_bar_zoom_factor['menu'] = self._zoom_factor_menu
            
            # 注册缩放系数改变回调
            self._view.get_zoom_factor().trace_add("write", self.__on_zoom_factor_changed)