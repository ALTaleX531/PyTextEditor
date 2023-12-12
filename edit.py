import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as sd
import tkinter.messagebox as msgbox
import utils
import regex as re
from text import TextEx

class FindDialog(utils.NonModalDialog):
    def dummy_find(self, parent): pass
    # 查找对话框
    def __init__(
        self,
        master:tk.Tk, 
        text:TextEx,
        title:str=None,
        dialog_opened:tk.BooleanVar = None,
        last_find_text:tk.StringVar = None,
        direction:tk.BooleanVar = None,
        match_whole_word_only:tk.BooleanVar = None,
        match_case:tk.BooleanVar = None,
        wrap_around:tk.BooleanVar = None,
        use_regex:tk.BooleanVar = None,
        find_func=None
    ):
        # 如果用户有选中文本，那就用它来替换掉上次的搜索文本
        # 已经打开了对话框，那就替换掉其中的搜索文本
        find_text = utils.get_selection_text(text) if text is not None and utils.is_text_being_selected(text) else None
        if find_text is not None and last_find_text is not None: last_find_text.set(find_text)
        
        if dialog_opened is not None and dialog_opened.get() == True:
            return
        
        self.edit = text
        self._dialog_opened = dialog_opened if find_func is not None else tk.BooleanVar(master)
        self._dialog_opened.set(True)
        self.last_find_text_var = last_find_text if last_find_text is not None else tk.StringVar(master)
        self.direction_var = direction if direction is not None else tk.BooleanVar(master)
        self.match_whole_word_only_var = match_whole_word_only if match_whole_word_only is not None else tk.BooleanVar(master)
        self.match_case_var =  match_case if match_case is not None else tk.BooleanVar(master)
        self.wrap_around_var =  wrap_around if wrap_around is not None else tk.BooleanVar(master)
        self.use_regex_var =  use_regex if use_regex is not None else tk.BooleanVar(master)
        self.find_func =  find_func if find_func is not None else self.dummy_find
        
        self.entry_find_row = 0
        self.other_options_row = 1
        self.direction_row = 1
        
        # 重写文本编辑框非激活状态下选中的背景颜色
        self._inactiveselect_old_color = self.edit['inactiveselect']
        self.edit['inactiveselect'] = self.edit['selectbackground']
        
        utils.NonModalDialog.__init__(self, master, "查找" if title is None else title)
    
    def destroy(self):
        # 恢复文本编辑框非激活状态下选中的背景颜色
        self.edit['inactiveselect'] = self._inactiveselect_old_color
        self.entry_find.unbind_all('<Return>')
        
        self.entry_find = None
        self.group_direction = None
        self.up = None
        self.down = None
        self.group_other = None
        self.match_whole_word_only = None
        self.match_case = None
        self.wrap_around = None
        self._dialog_opened.set(False)
        sd.Dialog.destroy(self)
        self.edit.focus()
    
    def update_regex_option(self):
        if self.use_regex_var.get():
            self.match_whole_word_only.config(state="disabled")
            self.match_whole_word_only_var.set(False)
        else:
            self.match_whole_word_only.config(state="normal")
    def update_match_whole_word(self):
        if self.match_whole_word_only_var.get():
            self.use_regex.config(state="disabled")
            self.use_regex_var.set(False)
        else:
            self.use_regex.config(state="normal")
            
    def initialize_entries(self, master):
        w = ttk.Label(master, text="查找内容(N): ", justify=tk.LEFT)
        w.grid(row=self.entry_find_row, column=0, padx=6, pady=6, sticky=tk.W)

        self.entry_find = ttk.Entry(master, name="entry_find", width=20, justify=tk.LEFT, textvariable=self.last_find_text_var)
        self.entry_find.grid(row=0, column=1, padx=6, sticky=tk.W+tk.E)
        self.entry_find_menu = utils.EntryContextMenu(master, self.entry_find)
        self.bind("<N>", lambda event: self.entry_find.focus())
        self.bind("<n>", lambda event: self.entry_find.focus())
        
        # 如果上一次搜索过了就让输入框全选
        if self.last_find_text_var.get():
            self.entry_find.select_range(0, tk.END)
            
    def body(self, master):
        tk.Misc.grab_release(self)
        master.pack(side=tk.LEFT)
        
        self.initialize_entries(master)
        # 方向
        self.group_direction = ttk.Labelframe(master, text="方向", width=230, height=80)
        self.group_direction.grid(row=self.direction_row, column=1, padx=6, pady=6)
        
        self.up = ttk.Radiobutton(self.group_direction, text="向上(U)", variable=self.direction_var, value=True)
        self.down = ttk.Radiobutton(self.group_direction, text="向下(D)", variable=self.direction_var, value=False)
        self.up.pack(side=tk.LEFT, padx=6, pady=6)
        self.down.pack(side=tk.LEFT, padx=6, pady=6)
        # 其它选项
        self.group_other = ttk.Frame(master)
        self.group_other.grid(row=self.other_options_row, column=0, padx=6, pady=6)
        
        self.use_regex = ttk.Checkbutton(self.group_other, text="使用正则表达式(R)", variable=self.use_regex_var, command=self.update_regex_option)
        self.match_whole_word_only = ttk.Checkbutton(self.group_other, text="全字匹配(W)", variable=self.match_whole_word_only_var, command=self.update_match_whole_word)
        self.match_case = ttk.Checkbutton(self.group_other, text="区分大小写(C)", variable=self.match_case_var)
        self.wrap_around = ttk.Checkbutton(self.group_other, text="循环(R)", variable=self.wrap_around_var)
        self.use_regex.pack(side=tk.TOP, anchor=tk.NW)
        self.match_whole_word_only.pack(side=tk.TOP, anchor=tk.NW)
        self.match_case.pack(side=tk.TOP, anchor=tk.NW)
        self.wrap_around.pack(side=tk.TOP, anchor=tk.NW)
        
        self.update_regex_option()
        self.update_match_whole_word()
        
        self.bind("<U>", lambda event: self.up.invoke())
        self.bind("<u>", lambda event: self.up.invoke())
        self.up.bind("<Return>", lambda event: self.up.invoke())
        self.bind("<D>", lambda event: self.down.invoke())
        self.bind("<d>", lambda event: self.down.invoke())
        self.down.bind("<Return>", lambda event: self.down.invoke())
        
        self.use_regex.bind("<Return>", lambda event: self.use_regex.invoke())
        self.match_whole_word_only.bind("<Return>", lambda event: self.match_whole_word_only.invoke())
        self.match_case.bind("<Return>", lambda event: self.match_case.invoke())
        self.wrap_around.bind("<Return>", lambda event: self.wrap_around.invoke())
        
        self.resizable(False, False)
        return self.entry_find
    
    def initialize_buttons(self, master):
        self.button_search = ttk.Button(master, text="查找下一个(F)", width=12, command=lambda: self.find_func(self), default=tk.ACTIVE)
        self.button_search.pack(side=tk.TOP, padx=6, pady=6, anchor=tk.NW)
        self.bind("<F>", lambda event: self.button_search.invoke())
        self.button_search.bind("<Return>", lambda event: self.button_search.invoke())
    def buttonbox(self):
        box = ttk.Frame(self)

        self.initialize_buttons(box)
        w = ttk.Button(box, text="取消", width=12, command=self.cancel)
        w.pack(side=tk.TOP, padx=6, pady=6, anchor=tk.NW)

        w.bind("<Return>", lambda event: w.invoke())
        self.entry_find.bind_all("<Return>", lambda event: self.button_search.invoke())
        self.bind_all("<Escape>", self.cancel)

        box.pack(side=tk.LEFT)
        
class ReplaceDialog(FindDialog):
    def dummy_replace(self, parent): pass
    def dummy_replace_all(self, parent): pass
    # 查找对话框
    def __init__(
        self,
        master:tk.Tk, 
        text:TextEx,
        title:str=None,
        dialog_opened:tk.BooleanVar = None,
        last_find_text:tk.StringVar = None,
        last_replace_text:tk.StringVar = None,
        direction:tk.BooleanVar = None,
        match_whole_word_only:tk.BooleanVar = None,
        match_case:tk.BooleanVar = None,
        wrap_around:tk.BooleanVar = None,
        use_regex:tk.BooleanVar = None,
        find_func=None,
        replace_func=None,
        replace_all_func=None,
    ):
        self.last_replace_text_var = last_replace_text if last_replace_text is not None else tk.StringVar(master)
        self.replace_func =  replace_func if replace_func is not None else self.dummy_replace
        self.replace_all_func =  replace_all_func if replace_all_func is not None else self.dummy_replace_all
        
        return FindDialog.__init__(
            self,
            master,
            text,
            "替换" if title is None else title,
            dialog_opened,
            last_find_text,
            direction,
            match_whole_word_only,
            match_case,
            wrap_around,
            use_regex,
            find_func
        )
    
    def initialize_entries(self, master):
        # 移到下一行，不然放不下替换的那一行的部件
        self.other_options_row = self.direction_row =  2
        FindDialog.initialize_entries(self, master)
        
        w = ttk.Label(master, text="替换为(P): ", justify=tk.LEFT)
        w.grid(row=1, column=0, padx=6, pady=6, sticky=tk.W)

        self.entry_replace = ttk.Entry(master, name="entry_replace", width=20, justify=tk.LEFT, textvariable=self.last_replace_text_var)
        self.entry_replace.grid(row=1, column=1, padx=6, pady=6, sticky=tk.W+tk.E)
        self.entry_replace_menu = utils.EntryContextMenu(master, self.entry_replace)
        self.bind("<P>", lambda event: self.entry_replace.focus())
        self.bind("<p>", lambda event: self.entry_replace.focus())
        
    def initialize_buttons(self, master):
        FindDialog.initialize_buttons(self, master)

        self.button_replace = ttk.Button(master, text="替换(R)", width=12, command=lambda: self.replace_func(self))
        self.button_replace_all = ttk.Button(master, text="全部替换(A)", width=12, command=lambda: self.replace_all_func(self))
        self.button_replace.pack(side=tk.TOP, padx=6, pady=6, anchor=tk.NW)
        self.button_replace_all.pack(side=tk.TOP, padx=6, pady=6, anchor=tk.NW)
        
        self.bind("<R>", lambda event: self.button_replace.invoke())
        self.bind("<A>", lambda event: self.button_replace_all.invoke())
        self.button_replace.bind("<Return>", lambda event: self.button_replace.invoke())
        self.button_replace_all.bind("<Return>", lambda event: self.button_replace_all.invoke())

class Edit(utils.TextContextMenu): 
    # 公开的方法
    # 返回搜索到的索引，如果没找到返回None
    # 索引永远在查找文本的第一个字母处
    def search(self, start_index, no_loop=False) -> tuple:
        
        count_variable = tk.StringVar(self._text)
        # 如果向上搜索，则结束索引在开始处
        stop_index = '1.0' if self._direction.get() else 'end-1c'   # end-1c 忽略末尾换行符
        pos = self._text.search(
                self._last_find_text.get() if not self._match_whole_word_only.get() else rf"\m{self._last_find_text.get()}\M",
                index=start_index,
                stopindex=stop_index,
                backwards=self._direction.get(),
                forwards=not self._direction.get(),
                regexp=self._use_regex.get() or self._match_whole_word_only.get(),
                nocase=not self._match_case.get(),
                count=count_variable
            )
        # 循环搜索
        if not pos and self._wrap_around.get() and not no_loop: 
            pos = self._text.search(
                self._last_find_text.get() if not self._match_whole_word_only.get() else rf"\m{self._last_find_text.get()}\M",
                index='end-1c' if self._direction.get() else '1.0',
                stopindex=stop_index,
                backwards=self._direction.get(),
                forwards=not self._direction.get(),
                regexp=self._use_regex.get() or self._match_whole_word_only.get(),
                nocase=not self._match_case.get(),
                count=count_variable
            )
        
        length = int(count_variable.get()  if count_variable.get() else 0)
        return (utils.index_to_tuple(pos) if pos else None, length)
    # 执行搜索，找到就选中对应的文本
    # 失败则使用MessageBox告诉用户没找到
    # 默认情况下，如果向下搜索则在用户当前选中的文本（如果有）后开始搜索，反之亦然
    # reverse为True时允许你反转这一行为
    def do_search(self, parent, reverse=False, action=None):
        # 查找文本不为空
        find_text = self._last_find_text.get()
        if not find_text:
            return
        # 检查正则表达式
        if self._use_regex.get():
            try: re.compile(find_text)
            except: msgbox.showerror(parent=parent, title="文本编辑器", message="正则表达式编译失败！请检查你的输入！"); return
        
        pos, length = self.search(
            tk.INSERT # 如果此时没有文本选中，那么就从插入符的位置开始搜索
            if not utils.is_text_being_selected(self._text) 
            else 
            utils.tuple_to_index(utils.get_selection_begin_index(self._text) if not reverse else utils.get_selection_end_index(self._text)) # 如果向上搜索，那么从选中的起始索引开始（reverse为False时）
            if self._direction.get() 
            else 
            utils.tuple_to_index(utils.get_selection_end_index(self._text) if not reverse else utils.get_selection_begin_index(self._text)) # 如果向下搜索，那么从选中的结束索引开始（reverse为False时）
        )
        self._text.tag_remove(tk.SEL, '1.0', 'end-1c')
        if length:
            row, column = pos
            if action is not None: action(row, column, length) 
            else: self.select(
                utils.tuple_to_index(pos), 
                utils.tuple_to_index(pos, length),
                True
            )
        else:
            msgbox.showinfo(parent=parent, title="文本编辑器", message="找不到" + '"' + find_text + '"')
    def do_replace(self, parent):
        replace_text = self._last_replace_text.get()
        def replace(row, column, length):
            pos = (row, column)
            # 分割上一次更改
            self._text.edit_separator()
            # 替换旧的，选中新的替换文本来提示用户
            self._text.replace(
                utils.tuple_to_index(pos),
                utils.tuple_to_index(pos, length),
                replace_text
            )
            self.select(
                utils.tuple_to_index(pos), 
                utils.tuple_to_index(pos, len(replace_text)),
                True
            )
            # 替换视为一次更改
            self._text.edit_separator()
        self.do_search(parent, True, replace)
    def do_replace_all(self, parent):
        # 查找文本不为空
        find_text = self._last_find_text.get()
        if not find_text:
            return
        replace_text = self._last_replace_text.get()
        # 检查正则表达式
        if self._use_regex.get():
            try: re.compile(find_text)
            except: msgbox.showerror(parent=parent, title="文本编辑器", message="正则表达式编译失败！请检查你的输入！"); return
        
        start_index = '1.0'
        replaced = False
        while True:
            pos, length = self.search(
                start_index,
                True
            )
            # 没找到，那就是没有要替换的目标了
            if pos is None:
                if replaced:
                    # 替换视为一次更改
                    self._text.edit_separator()
                break
            if not replaced:
                replaced = True
                # 分割上一次更改
                self._text.edit_separator()
            row, column = pos
            self._text.replace(
                utils.tuple_to_index(pos),
                utils.tuple_to_index(pos, length),
                replace_text
            )
            # 将下一次搜寻开始的列设到被替换的文本后面
            column += len(replace_text)
            start_index = utils.tuple_to_index((row, column))
    # 编辑(E)的菜单项对应的方法
    
    def find(self):
        if utils.is_text_empty(self._text):
            return
        
        # 非模态对话框需要防止对话框被打开多次
        FindDialog(
            self._root,
            self._text,
            None,
            self._dialog_opened,
            self._last_find_text,
            self._direction,
            self._match_whole_word_only,
            self._match_case,
            self._wrap_around,
            self._use_regex,
            self.do_search
        )
        
    def find_next(self):
        if utils.is_text_empty(self._text):
            return
        if not self._last_find_text.get():
            self.find()
            return
        self._direction.set(False)
        self.do_search(self._root)
    def find_previous(self):
        if utils.is_text_empty(self._text):
            return
        if not self._last_find_text.get():
            self.find()
            return
        self._direction.set(True)
        self.do_search(self._root)
    def replace(self):
        # 非模态对话框需要防止对话框被打开多次
        ReplaceDialog(
            self._root,
            self._text,
            None,
            self._dialog_opened,
            self._last_find_text,
            self._last_replace_text,
            self._direction,
            self._match_whole_word_only,
            self._match_case,
            self._wrap_around,
            self._use_regex,
            self.do_search,
            self.do_replace,
            self.do_replace_all
        )
        return 'break'
        
    def jump_to(self):
        class QueryInteger(sd._QueryInteger):
            def body(self, master):

                w = ttk.Label(master, text=self.prompt, justify=tk.LEFT)
                w.grid(row=0, padx=6, sticky=tk.W)

                self.entry = ttk.Entry(master, name="entry")
                self.entry.grid(row=1, padx=6, sticky=tk.W+tk.E)

                if self.initialvalue is not None:
                    self.entry.insert(0, self.initialvalue)
                    self.entry.select_range(0, tk.END)

                self.bind("<L>", lambda: self.entry.focus())
                self.bind("<l>", lambda: self.entry.focus())
                self.resizable(False, False)
                return self.entry
            def buttonbox(self):
                box = ttk.Frame(self)
                
                w = ttk.Button(box, text="转到", width=10, command=self.ok, default=tk.ACTIVE)
                w.pack(side=tk.LEFT, padx=6, pady=6)
                w = ttk.Button(box, text="取消", width=10, command=self.cancel)
                w.pack(side=tk.LEFT, padx=6, pady=6)

                self.bind("<Return>", self.ok)
                self.bind("<Escape>", self.cancel)

                box.pack()
        def askinteger(title, prompt, **kw):
            d = QueryInteger(title, prompt, **kw)
            return d.result
        
        line = askinteger(parent=self._root, title="转到指定行", prompt="行号(L)", initialvalue=utils.get_insert_marker_index(self._text)[0])
        if line != None:
            max_line = utils.get_text_end_index(self._text)[0]
            pos = utils.tuple_to_index(tuple([min(max_line, line), 0]))
            self._text.focus()
            self.select(pos, pos)
    
    def prepare_popup(self):
        utils.TextContextMenu.prepare_popup(self)
        state = "normal" if not utils.is_text_empty(self._text) else "disabled"
        self.text_menu.entryconfig(9, state=state) # 查找
        self.text_menu.entryconfig(10, state=state) # 查找下一个
        self.text_menu.entryconfig(11, state=state) # 查找上一个
    
    def __key_pressed(self, event):
        if event.char == ' ' or event.char == '\t' and self._space_pressed == False:
            self._space_pressed = True
            self._text.edit_separator()
        elif self._space_pressed == True:
            self._space_pressed = False
            self._text.edit_separator()
            
    def init_menu_hierarchy_2(self): 
        utils.TextContextMenu.init_menu_hierarchy_2(self)
        
        self.text_menu.add_command(label="查找(F)...", accelerator='Ctrl+F', underline=3, command=self.find)
        self.text_menu.add_command(label="查找下一个(N)...", accelerator='F3', underline=6, command=self.find_next)
        self.text_menu.add_command(label="查找上一个(V)...", accelerator='Shift+F3', underline=6, command=self.find_previous)
        self.text_menu.add_command(label="替换(H)...", accelerator='Ctrl+H', underline=3, command=self.replace)
        self.text_menu.add_command(label="转到(G)...", accelerator='Ctrl+G', underline=3, command=self.jump_to)
        
         # Tkinter中最狗屎的设计，区分大小写
        self._text.bind_all('<Control-E>', lambda event: self.search_by_bing())
        self._text.bind_all('<Control-e>', lambda event: self.search_by_bing())
        self._text.bind_all('<Control-F>', lambda event: self.find())
        self._text.bind_all('<Control-f>', lambda event: self.find())
        self._text.bind_all('<F3>', lambda event: self.find_next())
        self._text.bind_all('<Shift-F3>', lambda event: self.find_previous())
        self._text.bind('<Control-H>', lambda event: self.replace())
        self._text.bind('<Control-h>', lambda event: self.replace())
        self._text.bind_all('<Control-g>', lambda event: self.jump_to())
        self._text.bind_all('<Control-G>', lambda event: self.jump_to())
    def __init__(self, root:tk.Tk, menu_bar:tk.Menu, text:TextEx) -> None:
        self._root = root
        self._text = text
        # 查找/替换对话框还没有打开
        self._dialog_opened = tk.BooleanVar(root, False)
        self._last_find_text = tk.StringVar(root)
        self._last_replace_text = tk.StringVar(root)
        # True为向上寻找，False为向下寻找（默认值）
        self._direction = tk.BooleanVar(root)
        self._match_whole_word_only = tk.BooleanVar(root)
        self._match_case = tk.BooleanVar(root)
        self._wrap_around = tk.BooleanVar(root)
        self._use_regex = tk.BooleanVar(root)
            
        utils.TextContextMenu.__init__(self, menu_bar, self._text)
        
        # 默认情况下，每一次完整的操作将会放入栈中
        # 每次焦点切换、用户按下 Enter 键、删除/插入操作的转换等之前的操作算是一次完整的操作
        # 我们希望输入空格或Tab就视为一次完整的操作
        self._space_pressed = False
        self._modified = True
        self._text.bind('<Key>', self.__key_pressed)
        # 其它的不需要bind，因为Text控件本身就已经处理了这些加速键
        menu_bar.add_cascade(label="编辑(E)", menu=self.text_menu, underline=3)