import tkinter as tk
import tkinter.ttk as ttk
from idlelib.percolator import Percolator
from idlelib.redirector import WidgetRedirector
from idlelib.colorizer import ColorDelegator, Delegator

# 扩写这两个idlelib的类是因为它们没有处理被replace后，高亮失效的问题
# 另外我们还要要对光标的位置进行监控
# 由于WidgetRedirector每个部件只能存在一个，所以我们只能在TextEx内置一个PercolatorEx满足我们的需求

class PercolatorEx(Percolator):
    def __init__(self, text):
        super().__init__(text)
        
        # 像链表一样
        # xxxxx -> ColorDelegator -> Delegator -> org
        self.bottom.replace = self.redir.register("replace", self.replace)
        self.bottom.dispatch = self.dispatch
        text.tk.createcommand(text._w, self.dispatch_wrapper)
        
    def dispatch_wrapper(self, operation, *args):
        return self.top.dispatch(self.redir, operation, *args)
        
    def dispatch(self, redirector, operation, *args):
        return WidgetRedirector.dispatch(redirector, operation, *args)
    
    def replace(self, index1, index2, chars, tags=None):
        self.top.replace(index1, index2, chars, tags)

class ColorDelegatorEx(ColorDelegator):
    def replace(self, index1, index2, chars, tags=None):
        index1 = self.index(index1)
        index2 = self.index(index2)
        self.delegate.replace(index1, index2, chars, tags)
        self.notify_range(index1)
        self.notify_range(index1, index1 + "+%dc" % len(chars))
        
class InsertDelegator(Delegator): 
    def insert(self, index, chars, tags=None):
        self.delegate.insert(index, chars, tags)
        self.event_generate("<<InsertChange>>", when="tail")
    def delete(self, index1, index2=None):
        self.delegate.delete(index1, index2)
        self.event_generate("<<InsertChange>>", when="tail")
    def replace(self, index1, index2, chars, tags=None):
        self.delegate.replace(index1, index2, chars, tags)
        self.event_generate("<<InsertChange>>", when="tail")
    # 为什么不像replace那样再加个mark？
    # 试过了，WidgetRedirector这个框架还是有点缺陷，
    # 在某些情况它会触发TypeError: missing required positinal argument: index
    # 参考：https://stackoverflow.com/questions/1552749/difference-between-cr-lf-lf-and-cr-line-break-types
    def dispatch(self, redirector, operation, *args):
        if (operation, ) + args[0:2] == ("mark", "set", "insert"):
            self.event_generate("<<InsertChange>>", when="tail")
        return self.delegate.dispatch(redirector, operation, *args)

# 继承和整合tk.Text和tk.scrolledtext.ScrolledText
class TextEx(tk.Text):
    def __str__(self):
        return str(self.frame)
    
    # 部分代码复制自 tkinter.scrolledtext
    def __init__(self, master: tk.Misc | None = None, **kwargs) -> None:
        self.frame = ttk.Frame(master, relief=tk.FLAT)
        self.vbar = ttk.Scrollbar(self.frame)
        self.hbar = ttk.Scrollbar(self.frame, orient=tk.HORIZONTAL)

        kwargs.update({'yscrollcommand': self.vbar.set, "xscrollcommand": self.hbar.set})
        tk.Text.__init__(self, self.frame, **kwargs)
        self.vbar['command'] = self.yview
        self.hbar['command'] = self.xview

        self.update_wrap()   # 更新换行选项
        
        # Copy geometry methods of self.frame without overriding Text
        # methods -- hack!
        text_meths = vars(tk.Text).keys()
        methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        methods = methods.difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

        # 初始化插入符监控的相关例程
        self.percolator_ex = PercolatorEx(self)
        self.percolator_ex.insertfilter(InsertDelegator())
    
    
    def get_percolator_ex(self): return self.percolator_ex
    
    def configure(self, cnf=None, **kw):
        wrap = self['wrap']
        result = super().configure(cnf, **kw)
        if wrap != self['wrap']:
            self.update_wrap()
        return result
    
    def update_wrap(self):
        if self['wrap'] == 'char':
            self.hbar.pack_forget()
            self.vbar.pack_forget()
            tk.Text.pack_forget(self)
            self.vbar.pack(side=tk.RIGHT, fill=tk.Y, anchor=tk.E)
            tk.Text.pack(self, side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.W)
        else:
            self.hbar.pack_forget()
            self.vbar.pack_forget()
            tk.Text.pack_forget(self)
            self.hbar.pack(side=tk.BOTTOM, fill=tk.X, anchor=tk.S)
            self.vbar.pack(side=tk.RIGHT, fill=tk.Y, anchor=tk.E)
            tk.Text.pack(self, side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.W)