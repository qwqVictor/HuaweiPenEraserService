import ctypes
import keyboard
import threading
import pystray
import tendo.singleton
import os.path
import sys
from PIL import Image

me = tendo.singleton.SingleInstance("HuaweiPenEraserService")

class Pen:
    PenService: ctypes.CDLL
    eraser_mode: bool
    log: "function"

    def __init__(self, lib_paths: str=[
                 r"C:\Program Files\Huawei\PCManager\components\accessories_center\accessories_app\AccessoryApp\Lib\Plugins\Depend\PenService.dll",
                 r"C:\Program Files\WindowsApps\HuaweiPC.HuaweiPenAPP_1.0.1.0_x64__amfdc1pkdnmaa\HuaweiPenAPP\PenService.dll"
                 r"C:\Windows\PenService.dll"
                ],
                 logger: "function"=print) -> None:
        # 加载笔函数库
        self.PenService = None
        self.log = logger
        for lib_path in lib_paths:
            try:
                self.PenService = ctypes.cdll.LoadLibrary(lib_path)
            except: pass
            if self.PenService: break
        if self.PenService:
            self.pen()
        else:
            raise Exception(r"无法加载华为笔服务函数库，请安装华为电脑管家或者 HuaweiPenApp，或者将提取的 PenService.dll 放置于 C:\Windows\PenService.dll")
    # 切换笔事件监听器为 Ink 工作区        
    def init_ink_workspace_handler(self) -> None:
        self.PenService.CommandSendSetPenKeyFunc(2)
    
    # 切换笔模式为橡皮擦
    def eraser(self) -> bool:
        self.log('切换为橡皮擦')
        if self.PenService.CommandSendPenCurrentFunc(1) != 0:
            self.eraser_mode = True
            return True
        else: return False
    
    # 切换笔模式为笔
    def pen(self) -> bool:
        self.log('切换为笔')
        if self.PenService.CommandSendPenCurrentFunc(0) != 0:
            self.eraser_mode = False
            return True
        else: return False

    def switch_mode(self, callback=None) -> bool:
        if [self.eraser, self.pen][int(self.eraser_mode)]():
            if callback:
                callback(self.eraser_mode)
            return True
        else: return False

def double_click_gen(pen):
    def _onhotkey():
        print("触发双击")
        pen.switch_mode(callback=icon_change)
    return _onhotkey

def kbd_thread_gen(pen):
    def _func():
        double_click = double_click_gen(pen)
        keyboard.add_hotkey('win+f19', double_click)
        keyboard.wait()
    return _func

Pen_Icon = Image.open(os.path.join(os.path.dirname(__file__), "res", "Designcontest-Vintage-Pen.ico"))
Eraser_Icon = Image.open(os.path.join(os.path.dirname(__file__), "res", "Designcontest-Vintage-Eraser.ico"))

def icon_change(eraser_mode: bool):
    global icon
    if eraser_mode:
        icon.icon = Eraser_Icon
        icon.title = "橡皮模式"
    else:
        icon.icon = Pen_Icon
        icon.title = "笔输入模式"

def stop():
    global icon
    icon.stop()

menu = (pystray.MenuItem(text='退出', action=stop),)
icon = pystray.Icon("Eraser Service", menu=menu)


if __name__ == "__main__":
    try:
        global pen
        pen = Pen()
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(None, e.args[0], "错误", 0x00000010)
        sys.exit(1)
    kbd_thread = threading.Thread(target=kbd_thread_gen(pen), daemon=True)
    kbd_thread.start()
    icon_change(False)
    icon_thread = threading.Thread(target=icon.run)
    icon_thread.start()
    icon_thread.join()


    