import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as sd
import datetime as dt
import win32api

CRLF="Windows (CRLF)"
LF="Unix (LF)"
CR="Macintosh (CR)"

class NonModalDialog(sd.Dialog):
    # 重写只是为了避免调用grab_set方法
    # 一旦调用就再也没有机会调用grab_release了
    # 此时搜索进行的时候无法激活编辑框，这显然不是我们想要看到的
    def grab_set(self) -> None: pass
    def __init__(self, master, title):
        sd.Dialog.__init__(self, master, title)

class EditContextMenu:
    def __right_clicked(self, event):
        self.text_menu.post(event.x_root, event.y_root)
    
    def prepare_popup(self):
        state = "normal" if is_text_being_selected(self._text) else "disabled"
        self.text_menu.entryconfig(0, state=state) # 剪切
        self.text_menu.entryconfig(1, state=state) # 复制
        self.text_menu.entryconfig(3, state=state) # 删除
        self.text_menu.entryconfig(5, state=state) # 使用Bing搜索

    def undo(self): self._text.event_generate("<<Undo>>")
    def redo(self): self._text.event_generate("<<Redo>>")
    def cut(self): self._text.event_generate("<<Cut>>")
    def copy(self): self._text.event_generate("<<Copy>>")
    def paste(self): self._text.event_generate("<<Paste>>")
    def delete(self): self._text.event_generate("<<Clear>>")
    
    def search_by_bing(self):
        if is_text_being_selected(self._text): 
            win32api.ShellExecute(
                self._master.winfo_id(),
                "open",
                "https://www.bing.com/search?q=" + get_selection_text(self._text),
                None,
                None,
                0
            )
    def select_all(self): pass
    def insert_date(self):
        self.delete()
        self._text.insert('insert', dt.datetime.now().strftime("%I:%M %Y/%m/%d"))
    
    def init_menu_hierarchy_1(self): 
        self.text_menu.add_command(label="剪切(T)", accelerator='Ctrl+X', underline=3, command=self.cut)
        self.text_menu.add_command(label="复制(C)", accelerator='Ctrl+C', underline=3, command=self.copy)
        self.text_menu.add_command(label="粘贴(P)", accelerator='Ctrl+V', underline=3, command=self.paste)
        self.text_menu.add_command(label="删除(L)", accelerator='Del', underline=3, command=self.delete)
    def init_menu_hierarchy_2(self): 
        self.text_menu.add_command(label="使用Bing搜索...", accelerator='Ctrl+E', underline=2, command=self.search_by_bing)
        
        # Tkinter中最狗屎的设计，区分大小写
        self._text.bind('<Control-E>', lambda event: self.search_by_bing())
        self._text.bind('<Control-e>', lambda event: self.search_by_bing())
    def init_menu_hierarchy_3(self): 
        self.text_menu.add_command(label="全选(A)", accelerator='Ctrl+A', underline=3, command=self.select_all)
        self.text_menu.add_command(label="时间/日期(D)", accelerator='F5', underline=6, command=self.insert_date)
        
        # 拦截原生的Ctrl+A是因为行为不一致，没有将插入光标移动到末尾
        self._text.bind('<Control-Key-a>', lambda event: self.select_all())
        self._text.bind('<Control-Key-A>', lambda event: self.select_all())
        self._text.bind('<F5>', lambda event: self.insert_date())
        
    def __init__(self, master:tk.Menu|tk.Toplevel, text:tk.Text|tk.Entry|ttk.Entry) -> None:
        self._master = master
        self._text = text
        
        self.text_menu = tk.Menu(master, tearoff=False, postcommand=self.prepare_popup)
        self.init_menu_hierarchy_1()
        self.text_menu.add_separator()
        self.init_menu_hierarchy_2()
        self.text_menu.add_separator()
        self.init_menu_hierarchy_3()
        
        # 右键菜单，用Release这样鼠标松开才会触发菜单
        self._text.bind("<ButtonRelease-3>", lambda event: self.__right_clicked(event))
        
class EntryContextMenu(EditContextMenu):
    def select_all(self):
        self._text.select_range(0, tk.END)
        self._text.icursor(tk.END)
class TextContextMenu(EditContextMenu):
    def select(self, begin, end, marker_pos_use_begin=False):
        # 将某段区间的文字加上tag
        self._text.tag_add(tk.SEL, begin, end)
        # 移动光标到开始的地方
        self._text.mark_set(tk.INSERT, begin if marker_pos_use_begin else end)
        # 滚到光标的地方
        self._text.see(tk.INSERT)
        
    def select_all(self):
        self.select('1.0', 'end-1c')
        return 'break'
    
    def prepare_popup(self):
        state = "normal" if is_text_being_selected(self._text) else "disabled"
        self.text_menu.entryconfig(3, state=state) # 剪切
        self.text_menu.entryconfig(4, state=state) # 复制
        self.text_menu.entryconfig(6, state=state) # 删除
        self.text_menu.entryconfig(8, state=state) # 使用Bing搜索
    
    def init_menu_hierarchy_1(self): 
        self.text_menu.add_command(label="撤销(U)", accelerator='Ctrl+Z', underline=3, command=self.undo)
        self.text_menu.add_command(label="重做(R)", accelerator='Ctrl+Y', underline=3, command=self.redo)
        self.text_menu.add_separator()
        
        super().init_menu_hierarchy_1()

def unpack(string:str, separator:str='x', func=int): return map(func, string.split(separator))
def index_to_tuple(index:str) -> tuple: return tuple(unpack(index if index else '0.0', '.'))
def tuple_to_index(index:tuple, offset:int = 0) -> str: return str(index[0]) + '.' + str(index[1] + offset)
def is_text_being_selected(text:tk.Text|tk.Entry|ttk.Entry) -> bool: return bool(text.tag_ranges('sel')) if isinstance(text, tk.Text) else text.select_present()
def is_text_empty(text:tk.Text|tk.Entry|ttk.Entry) -> bool: return bool(text.compare("end-1c", "==", "1.0"))  if isinstance(text, tk.Text) else not bool(text.index(tk.END))
def get_selection_begin_index(text:tk.Text) -> tuple: return index_to_tuple(text.index(tk.SEL_FIRST)) if is_text_being_selected(text) else None
def get_selection_end_index(text:tk.Text) -> tuple: return index_to_tuple(text.index(tk.SEL_LAST)) if is_text_being_selected(text) else None
def get_text_end_index(text:tk.Text) -> tuple: return index_to_tuple(text.index('end-1c'))
def get_selection_text(text:tk.Text|tk.Entry|ttk.Entry) -> str: return text.get(tk.SEL_FIRST, tk.SEL_LAST) if isinstance(text, tk.Text) else text.selection_get()
def get_insert_marker_index(text:tk.Text) -> tuple: return index_to_tuple(text.index('insert'))
def get_text_content(text:tk.Text|tk.Entry|ttk.Entry) -> str: return text.get('1.0', tk.END) if isinstance(text, tk.Text) else text.get()