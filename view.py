import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkFont
import regex as re
import utils
from text import TextEx, ColorDelegatorEx

class View:
    def __init_color_delegator(self):
        self._code_filter = ColorDelegatorEx()
        
        # 清除默认的高亮颜色
        for key, value in self._code_filter.tagdefs.items():
            value["foreground"] = None
        self._code_filter.tagdefs["COMMENT"]["foreground"] = "#008000"
        self._code_filter.tagdefs["DEFINITION"]["foreground"] = "#795E26"
        self._code_filter.tagdefs["ERROR"]["foreground"] = "#FF0000"
        
        # 语法高亮用到的正则表达式
        KEYWORD1   = r"\b(?P<KEYWORD1>as|and|not|or|is|assert|async|await|break|continue|del|elif|else|except|finally|for|from|if|import|pass|raise|return|try|while|with|yield)\b"
        KEYWORD2   = r"\b(?P<KEYWORD2>False|None|True|class|def|global|lambda|nonlocal)\b"
        EXCEPTION = r"([^.'\"\\#]\b|^)(?P<EXCEPTION>ArithmeticError|AssertionError|AttributeError|BaseException|BlockingIOError|BrokenPipeError|BufferError|BytesWarning|ChildProcessError|ConnectionAbortedError|ConnectionError|ConnectionRefusedError|ConnectionResetError|DeprecationWarning|EOFError|Ellipsis|EnvironmentError|Exception|FileExistsError|FileNotFoundError|FloatingPointError|FutureWarning|GeneratorExit|IOError|ImportError|ImportWarning|IndentationError|IndexError|InterruptedError|IsADirectoryError|KeyError|KeyboardInterrupt|LookupError|MemoryError|ModuleNotFoundError|NameError|NotADirectoryError|NotImplemented|NotImplementedError|OSError|OverflowError|PendingDeprecationWarning|PermissionError|ProcessLookupError|RecursionError|ReferenceError|ResourceWarning|RuntimeError|RuntimeWarning|StopAsyncIteration|StopIteration|SyntaxError|SyntaxWarning|SystemError|SystemExit|TabError|TimeoutError|TypeError|UnboundLocalError|UnicodeDecodeError|UnicodeEncodeError|UnicodeError|UnicodeTranslateError|UnicodeWarning|UserWarning|ValueError|Warning|WindowsError|ZeroDivisionError)\b"
        BUILTIN   = r"([^.'\"\\#]\b|^)(?P<BUILTIN>abs|all|any|ascii|bin|breakpoint|callable|chr|classmethod|compile|complex|copyright|credits|delattr|dir|divmod|enumerate|eval|exec|exit|filter|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|isinstance|issubclass|iter|len|license|locals|map|max|memoryview|min|next|oct|open|ord|pow|print|quit|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|sum|type|vars|zip)\b"
        STRING    = r"(?P<STRING>(?i:r|u|f|fr|rf|b|br|rb)?'[^'\\\n]*(\\.[^'\\\n]*)*'?|(?i:r|u|f|fr|rf|b|br|rb)?\"[^\"\\\n]*(\\.[^\"\\\n]*)*\"?)"
        TYPES     = r"\b(?P<TYPES>bool|bytearray|bytes|dict|float|int|list|str|tuple|object)\b"
        NUMBER    = r"\b(?P<NUMBER>((0x|0b|0o|#)[\da-fA-F]+)|((\d*\.)?\d+))\b"
        CLASSDEF  = r"(?<=\bclass)[ \t]+(?P<CLASSDEF>\w+)[ \t]*[:\(]" # 对DEFINITION中的类声明重新着色
        DECORATOR = r"(^[ \t]*(?P<DECORATOR>@[\w\d\.]+))"
        INSTANCE  = r"\b(?P<INSTANCE>super|self|cls)\b"
        COMMENT   = r"(?P<COMMENT>#[^\n]*)"
        PROG   = rf"{KEYWORD1}|{KEYWORD2}|{BUILTIN}|{EXCEPTION}|{TYPES}|{COMMENT}|{STRING}|{INSTANCE}|{DECORATOR}|{NUMBER}|{CLASSDEF}"
        IDPROG = r"(?<!class)\s+(\w+)"
        
        self._code_filter.prog    = re.compile(PROG, re.S|re.M)
        self._code_filter.idprog  = re.compile(IDPROG, re.S)
        self._code_filter.tagdefs = \
        {
            **self._code_filter.tagdefs,
            **{
                "KEYWORD1": {"foreground":"#AF00DB", "background":None},
                "KEYWORD2": {"foreground":"#0000FF", "background":None},
                "EXCEPTION": {"foreground":"#267F99", "background":None},
                "BUILTIN": {"foreground":"#795E26", "background":None},
                "STRING": {"foreground":"#A31515", "background":None},
                "TYPES": {"foreground":"#267F99", "background":None},
                "NUMBER": {"foreground":"#098658", "background":None},
                "CLASSDEF": {"foreground":"#267F99", "background":None},
                "DECORATOR": {"foreground":"#795E26", "background":None},
                "INSTANCE": {"foreground":"#267F9C", "background":None},
                "COMMENT": {"foreground":"#008000", "background":None}
            }
        }
    # 缩放比例发生更改
    def __on_zoom_factor_changed(self, var, index, mode):
        self.update_font_real_size()
    
    # 公开的方法
    # 设置字体的实际大小
    def update_font_real_size(self):
        if self._update_font_real_size_func is not None: self._update_font_real_size_func(self._font_size.get() * self._zoom_factor.get() / 100)
    def get_zoom_factor(self): return self._zoom_factor
    def set_zoom(self, new_zoom_factor):
        self._zoom_factor.set(max(10, min(200, new_zoom_factor)))
    # 刷新语法高亮
    def flush_syntax_highlight(self):
        self.enable_syntax_highlight(not self._syntax_highlight.get())
        self.enable_syntax_highlight(self._syntax_highlight.get())
    def get_syntax_highlight(self): return self._syntax_highlight
    def get_status_bar(self): return self._status_bar
    # 视图(V)的菜单项对应的方法
    # 缩放不低于10%
    def zoom_in(self): self.set_zoom(self._zoom_factor.get() + 10)
    def zoom_out(self): self.set_zoom(self._zoom_factor.get() - 10)
    def zoom_reset(self): 
        if self._zoom_factor.get() != 100:
            self._zoom_factor.set(100)
    
    def toggle_syntax_highlight(self):
        # 语法高亮
        if self._syntax_highlight.get():
            if self._code_filter is None:
                self.__init_color_delegator()
            self._text.get_percolator_ex().insertfilter(self._code_filter)
        # 取消了语法高亮
        elif self._code_filter is not None and self._code_filter.delegate:
            self._code_filter.removecolors()
            self._text.get_percolator_ex().removefilter(self._code_filter)
            self._code_filter = None
            
    def toggle_status_bar(self):
        if self._status_bar.get():
            self._text.pack_forget()
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
            self._text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        else:
            self.status_bar.pack_forget()
            
    def enable_syntax_highlight(self, syntax_highlight:bool):
        if hasattr(self, "_syntax_highlight") == False:
            self._syntax_highlight = tk.BooleanVar(self._root)
            self._syntax_highlight.set(syntax_highlight)
            
            self.__init_color_delegator()
        elif self._syntax_highlight.get() != syntax_highlight:
            self._syntax_highlight.set(syntax_highlight)
        
        self.toggle_syntax_highlight()
    def enable_status_bar(self, status_bar:bool):
        if hasattr(self, "_status_bar") == False:
            self._status_bar = tk.BooleanVar(self._root)
            self._status_bar.set(status_bar)
        elif self._status_bar.get() != status_bar:
            self._status_bar.set(status_bar)
        
        self.toggle_status_bar()
    
    def __init__(
        self, 
        root:tk.Tk, 
        menu_bar:tk.Menu, 
        text:TextEx, 
        font_size:tk.IntVar=None, 
        syntax_highlight:bool=False, 
        status_bar:bool=True, 
        update_font_real_size_func=None
    ) -> None:
        self._row_column_text = "第{}行，第{}列"
        self._root = root
        self._text = text
        self._font_size =  font_size if font_size is not None else tk.IntVar(self._root)
        self._update_font_real_size_func = update_font_real_size_func
        
        # 配置状态栏
        self.status_bar = ttk.Frame(self._root)
        self.status_bar_position = ttk.Label(self.status_bar, text=self._row_column_text.format(1, 1), padding=4, width=18)
        self.status_bar_zoom_factor = ttk.Menubutton(self.status_bar, text="100%", padding=4, width=6, direction='above')
        self.status_bar_line_ending = ttk.Menubutton(self.status_bar, text=utils.CRLF, padding=4, width=15, direction='above')
        self.status_bar_encoding = ttk.Menubutton(self.status_bar, text="UTF-8", padding=4, width=15, direction='above')
        
        self.status_bar_encoding.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        self.status_bar_line_ending.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        self.status_bar_zoom_factor.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        self.status_bar_position.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        
        self._text.bind(
            '<<InsertChange>>', 
            lambda event:  self.status_bar_position.configure(
                    text=self._row_column_text.format(
                        *((lambda index: (index[0], index[1] + 1))(utils.get_insert_marker_index(self._text)))
                )
            )
        )
        self.enable_status_bar(status_bar)
        # 配置语法高亮的选项
        self.enable_syntax_highlight(syntax_highlight)
        # 缩放选项
        self._zoom_factor = tk.IntVar(self._root, value=0)
        self._zoom_factor.trace_add("write", self.__on_zoom_factor_changed)
        self.zoom_reset()
        
        self.view_menu = tk.Menu(menu_bar, tearoff=False)
        self.zoom_menu = tk.Menu(self.view_menu, tearoff=False)
        
        self.zoom_menu.add_command(label="放大(I)", accelerator='Ctrl+加号', underline=3, command=self.zoom_in)
        self.zoom_menu.add_command(label="缩小(O)", accelerator='Ctrl+减号', underline=3, command=self.zoom_out)
        self.zoom_menu.add_command(label="恢复默认缩放", accelerator='Ctrl+0', command=self.zoom_reset)
        # 鼠标滚轮
        # delta值大于0则说明鼠标滚轮向上滚动，否则向下滚动
        self._text.bind_all(
            '<Control-MouseWheel>', 
            lambda event: self.set_zoom(self._zoom_factor.get() + (10 if int(event.delta/120) > 0 else -10))
        )
        self._text.bind_all('<Control-+>', lambda event: self.zoom_in())
        self._text.bind_all('<Control-minus>', lambda event: self.zoom_out())
        self._text.bind_all('<Control-0>', lambda event: self.zoom_reset())
        
        self.view_menu.add_cascade(label="缩放(Z)", menu=self.zoom_menu, underline=3)
        self.view_menu.add_checkbutton(label="状态栏(S)", onvalue=True, offvalue=False, variable=self._status_bar, command=self.toggle_status_bar, underline=4)
        self.view_menu.add_separator()
        self.view_menu.add_checkbutton(label="语法高亮(H)", onvalue=True, offvalue=False, variable=self._syntax_highlight, command=self.toggle_syntax_highlight, underline=5)
        
        menu_bar.add_cascade(label="查看(V)", menu=self.view_menu, underline=3)
        