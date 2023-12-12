# 主程序和入口点
# 主要与系统进行交互和进行相应适配
from text_editor import TextEditor
from ctypes import *
from ctypes import wintypes
import locale
import utils

class App(TextEditor):
    def get_dpi_scale_factor(self) -> float: return float(windll.shcore.GetScaleFactorForDevice(0) / 100)
    # 重写new_window方法，做缩放感知的适配
    def new_window(self): App()
    # 重写窗口大小更新
    def geometry(self, new_size:str):
        factor = self.get_dpi_scale_factor()
        width, height = tuple(utils.unpack(new_size))
        return TextEditor.geometry(self, str(round(width * factor)) + 'x' + str(round(height * factor)))
    # 重写字体大小更新
    def update_font_real_size(self, font_size:float):
        return TextEditor.update_font_real_size(self, font_size * self.get_dpi_scale_factor())
    
    def __init__(self) -> None:
        TextEditor.__init__(self, False, False, True)
        self.tk.call('tk', 'scaling', self.get_dpi_scale_factor() * 96 / 72)

if __name__ == '__main__':
    # 旨在解决在Windows10/11上因缩放问题导致的模糊
    # 开启每个显示器V2缩放感知
    # Windows 10 1703后可用
    windll.user32.SetProcessDpiAwarenessContext(wintypes.HANDLE(-4))
    # 开启系统级缩放感知
    # Windows 8.1后可用
    # 这里用作回退逻辑
    windll.shcore.SetProcessDpiAwareness(1)
    
    locale.setlocale(locale.LC_ALL, '')
    app = App()
    app.run()