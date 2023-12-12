import os
import sys
import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import filedialog
from chardet import detect
from text import TextEx
import utils

class File: 
    def __get_file_display_name(self):
        return os.path.basename(self._current_file_path.get()) if self._current_file_path.get() else "无标题"
    def __get_file_path_name(self):
        return self._current_file_path.get() if self._current_file_path.get() else "无标题"
    def __on_saved_state_changed(self, var, index, mode):
        self.update_root_title()
    
    def update_root_title(self):
        self._root.title(
            ('*' if not self._saved.get() else '') +
            self.__get_file_display_name() +
            ' - ' +
            "文本编辑器"
        )
    def __on_modification(self):
        self._saved.set(False)
        # 如果只是新建了一个文件，但又什么内容都没有
        # 压根没必要保存
        if not self._current_file_path.get() and utils.is_text_empty(self._text):
            self._saved.set(True)
        # 重设更改标志，否则不会收到下一次更改的事件通知
        self._text.edit_modified(False)
    # 返回是否执行了保存工作
    def __save(self, force_new_file_path=False) -> bool: 
        new_file_path = self._current_file_path.get()
        if not self._current_file_path.get() or force_new_file_path:
            new_file_path = filedialog.asksaveasfilename(
                master=self._root, 
                initialfile=os.path.basename(self._current_file_path.get()),
                defaultextension=os.path.splitext(self._current_file_path.get())[-1],
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if not new_file_path:
                return False
        
        # 将更改写入到文件
        try:
            # 为什么这里处理文本的逻辑要在写入前面？
            # 因为一旦触发异常，文件内容就直接丢失了，原来的文件被直接置空
            content = utils.get_text_content(self._text)
            if self._line_ending.get() == utils.CRLF:
                content = content.replace(b'\n'.decode(errors='replace'), b'\r\n'.decode(errors='replace'))
            if self._line_ending.get() == utils.CR:
                content = content.replace(b'\n'.decode(errors='replace'), b'\r'.decode(errors='replace'))
            content = bytes(content, encoding=self._encoding.get())
            
            with open(new_file_path, 'wb') as file:
                file.write(content)
        except UnicodeEncodeError as exception:
            msgbox.showerror(
                    title="错误的文件保存编码",
                    message=str(exception) + '\n' + "请尝试以别的编码保存该文件，现已自动为你回退到原始文件编码。",
                    master=self._root
                )
            # 回退到文件的原始编码
            self._encoding.set(self._raw_encoding)
            return None
        else:
            self._current_file_path.set(new_file_path)
            self._saved.set(True)
        return True
    # 执行清理工作，询问用户是否保存
    # 返回True如果操作能继续进行
    def __clean_up(self) -> bool:
        if self._saved.get() == False:
            answer = msgbox.askyesnocancel(
                "文本编辑器", 
                "你想将更改保存到 " + self.__get_file_path_name() + " 吗？",
                master=self._root
            )
            if answer is None:
                return False
            if answer == True: 
                result = self.__save()
                # 发生错误
                if result is None: 
                    return False
                # 选择了保存，但是又在文件保存对话框那取消了，这都什么人啊
                if result == False:
                    return False
            if answer == False: pass
            
        return True
    # 丢弃旧的，重设为新的内容
    # new_file_path为None时，不改变现有的路径
    def __reset(self, new_file_path='', new_content=None):
        # 删除并替换文本编辑框的所有内容
        # Text不做其他处理的情况下用replace，会使View的高亮失效
        if new_content is not None:
            self._text.replace(
                '1.0', tk.END,
                new_content
            )
        else:
            self._text.delete('1.0', tk.END)
        
        # 将插入符号放回最开始的地方
        self._text.mark_set(tk.INSERT, '1.0')
        self._text.see('1.0')
        
        if new_file_path is not None:
            self._current_file_path.set(new_file_path)
        # 新建文件，重设编码/保存状态
        if new_file_path == '':
            # 清除撤回和重做的所有记录
            self._text.edit_reset()
            self._text.update()
            
            self._encoding.set('UTF-8')
            self._raw_encoding = self._encoding.get()
            self._line_ending.set(utils.CRLF)
        
        # 立即更新，产生<<Modified>>事件
        self._text.update()
        self._saved.set(True)
    def __destroy(self):
        if self.__clean_up():
            tk.Tk.destroy(self._root)
    def __handle_encoding(self, content):
        result = detect(content)
        encoding = result["encoding"]
        
        # 无法识别...
        if encoding is None:
            default_encoding = sys.getdefaultencoding().upper()
            answer = msgbox.askyesno(
                title="无法识别文件的编码",
                message="选择“是”以GB2312编码打开，选择“否”以区域默认的{}编码打开。".format(default_encoding),
                master=self._root,
                icon=msgbox.WARNING
            )
            
            if answer:
                encoding = 'GB2312'
            else:
                encoding = default_encoding
        else:
            encoding = str(encoding).upper()
            
            # 把握不太大，询问一下用户
            if result['confidence'] <= 0.6:
                default_encoding = sys.getdefaultencoding().upper()
                answer = msgbox.askyesnocancel(
                    title="无法准确识别文件的编码",
                    message="当前识别到的文件编码为" + encoding + "，可能含有乱码。\n选择“是”以GB2312编码打开，选择“否”以区域默认的{}编码打开。\n如果你希望保持现状，请选择“取消”。".format(default_encoding),
                    master=self._root,
                    icon=msgbox.WARNING
                )
                
                if answer:
                    encoding = 'GB2312'
                elif answer is not None:
                    encoding = default_encoding
                    
        print(result)
        return encoding
    
    # 公开的方法    
    def is_saved(self): return self._saved.get()
    def get_saved_state(self): return self._saved
    def get_encoding(self): return self._encoding
    def get_line_ending(self): return self._line_ending
    def get_opened_file_path(self): return self._current_file_path
    
    def request_encoding(self, encoding):
        self._encoding.set(encoding)
        if (self._current_file_path.get() or not utils.is_text_empty(self._text)):
            self._saved.set(False)
    def request_line_ending(self, line_ending):
        self._line_ending.set(line_ending)
        if (self._current_file_path.get() or not utils.is_text_empty(self._text)):
            self._saved.set(False)
    # 文件(F)的菜单项对应的方法
    def new(self): 
        if self.__clean_up():
            self.__reset()
    def new_window(self): 
        if self._new_window_func is not None: self._new_window_func()
    def reopen(self, encoding):
        if self.__clean_up():
            try:
                with open(self._current_file_path.get(), "rb") as file:
                    # 先读取第一行确认行尾
                    line = file.readline()
                    if line.endswith(b'\r\n'):
                        self._line_ending.set(utils.CRLF)
                    elif line.endswith(b'\n'):
                        self._line_ending.set(utils.LF)
                    elif line.endswith(b'\r'):
                        self._line_ending.set(utils.CR)
                    file.seek(0)
                    
                    content = file.read()
                    # 这一步永远不会发生，但为了严谨起见进行保留
                    if encoding is None:
                        encoding = self.__handle_encoding(content)
                    
                    # tkinter.Text使用的是Unix的方式显示文本，因此是其它行尾类型的文件需要进行一次转换
                    # 否则你会在部件里每一行的末尾发现多余且不可见的字符
                    if self._line_ending.get() == utils.CRLF:
                        content = content.replace(b'\r\n', b'\n')
                    if self._line_ending.get() == utils.CR:
                        content = content.replace(b'\r', b'\n')
                    
                    content = content.decode(encoding)
            except UnicodeDecodeError as exception:
                msgbox.showerror(
                    title="错误的文件打开编码",
                    message=str(exception) + '\n' + "请尝试以别的编码打开该文件。",
                    master=self._root
                )
            else:
                self._raw_encoding = encoding
                self._encoding.set(encoding)
                self.__reset(None, content)
            
    def open(self):
        if self.__clean_up():
            new_file_path = filedialog.askopenfilename(
                master=self._root, 
                initialfile=os.path.basename(self._current_file_path.get()),
                defaultextension=os.path.splitext(self._current_file_path.get())[-1],
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if new_file_path:
                try:
                    with open(new_file_path, "rb") as file:
                        # 先读取第一行确认行尾
                        line = file.readline()
                        if line.endswith(b'\r\n'):
                            self._line_ending.set(utils.CRLF)
                        elif line.endswith(b'\n'):
                            self._line_ending.set(utils.LF)
                        elif line.endswith(b'\r'):
                            self._line_ending.set(utils.CR)
                        file.seek(0)
                        
                        content = file.read()
                        encoding = self.__handle_encoding(content)
                        
                        # tkinter.Text使用的是Unix的方式显示文本，因此是其它行尾类型的文件需要进行一次转换
                        # 否则你会在部件里每一行的末尾发现多余且不可见的字符
                        if self._line_ending.get() == utils.CRLF:
                            content = content.replace(b'\r\n', b'\n')
                        if self._line_ending.get() == utils.CR:
                            content = content.replace(b'\r', b'\n')
                        
                        content = content.decode(encoding)
                except UnicodeDecodeError as exception:
                    msgbox.showwarning(
                        title="无法识别文件的编码",
                        message="解码过程中出现错误，文本可能含有乱码，如有需要请在状态栏的编码选项选择最有可能的编码重新打开。",
                        master=self._root
                    )
                    content = content.decode(encoding, errors='replace')
                finally:
                    self._raw_encoding = encoding
                    self._encoding.set(encoding)
                    self.__reset(new_file_path, content)
                
    def save(self): self.__save()
    def save_as(self): self.__save(True)
    def exit(self): self._root.destroy()
    
    def __init__(self, root:tk.Tk, menu_bar:tk.Menu, text:TextEx, new_window_func=None) -> None:
        self._root = root
        self._text = text
        self._new_window_func = new_window_func
        self._current_file_path = tk.StringVar(self._root)
        self._saved = tk.BooleanVar(self._root, True)
        self._saved.trace_add("write", self.__on_saved_state_changed)
        self._encoding = tk.StringVar(self._root, 'UTF-8')
        self._line_ending = tk.StringVar(self._root, utils.CRLF)
        # 用于回退逻辑
        self._raw_encoding = self._encoding.get()
        self.update_root_title()
        
        # 初始化文件(F)菜单项
        self.file_menu = tk.Menu(menu_bar, tearoff=False)
        self.file_menu.add_command(label="新建(N)", accelerator='Ctrl+N', command=self.new, underline=3)
        self.file_menu.add_command(label="新窗口(W)", accelerator='Ctrl+Shift+N', command=self.new_window, underline=4)
        self.file_menu.add_command(label="打开(O)...", accelerator='Ctrl+O', command=self.open, underline=3)
        self.file_menu.add_command(label="保存(S)", accelerator='Ctrl+S', command=self.save, underline=3)
        self.file_menu.add_command(label="另存为(A)...", accelerator='Ctrl+Shift+S', command=self.save_as, underline=4)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="页面设置(U)...", underline=5, state=tk.DISABLED)
        self.file_menu.add_command(label="打印(P)", accelerator='Ctrl+P', underline=3, state=tk.DISABLED)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="退出(X)", command=self.exit, underline=3)
        # Tkinter中最狗屎的设计，区分大小写
        self._text.bind_all('<Control-N>', lambda event: self.new())
        self._text.bind_all('<Control-n>', lambda event: self.new())
        self._text.bind_all('<Control-Shift-N>', lambda event: self.new_window())
        self._text.bind_all('<Control-Shift-n>', lambda event: self.new_window())
        self._text.bind_all('<Control-O>', lambda event: self.open())
        self._text.bind_all('<Control-o>', lambda event: self.open())
        self._text.bind_all('<Control-S>', lambda event: self.save())
        self._text.bind_all('<Control-s>', lambda event: self.save())
        self._text.bind_all('<Control-Shift-S>', lambda event: self.save_as())
        self._text.bind_all('<Control-Shift-s>', lambda event: self.save_as())
        # 更改回调
        self._text.bind("<<Modified>>", lambda event: self.__on_modification())
        # 重写关闭窗口的例程
        self._root.protocol("WM_DELETE_WINDOW", self.__destroy)
        
        menu_bar.add_cascade(label="文件(F)", menu=self.file_menu, underline=3)