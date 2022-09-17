import ctypes
import threading
from os import system
from time import sleep

class Thread(threading.Thread):
    """
    可停止式線程。
    新增:
     - stop(): 強制停止線程。
    """
    def stop(self):
        if not self.is_alive() or self.ident == None: raise threading.ThreadError("The thread is not active.")
        elif ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(SystemExit)) == 1: return
        ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")

def _auto_kill():
    while threading.main_thread().is_alive():
        sleep(0.1)
    for thread in threading.enumerate():
        if thread.ident != threading.current_thread().ident and thread.is_alive():
            thread.stop()
            thread.join()
    threading.current_thread()

def restart():
    thr = threading.main_thread()
    system("start cmd /c \"Start.cmd\"")
    if not thr.is_alive() or thr.ident == None: raise threading.ThreadError("The thread is not active.")
    elif ctypes.pythonapi.PyThreadState_SetAsyncExc(thr.ident, ctypes.py_object(SystemExit)) == 1: return
    ctypes.pythonapi.PyThreadState_SetAsyncExc(thr.ident, 0)
    raise SystemError("PyThreadState_SetAsyncExc failed")

def stop():
    thr = threading.main_thread()
    if not thr.is_alive() or thr.ident == None: raise threading.ThreadError("The thread is not active.")
    elif ctypes.pythonapi.PyThreadState_SetAsyncExc(thr.ident, ctypes.py_object(SystemExit)) == 1: return
    ctypes.pythonapi.PyThreadState_SetAsyncExc(thr.ident, 0)
    raise SystemError("PyThreadState_SetAsyncExc failed")

_auto_kill_thread = Thread(target=_auto_kill, name="AutoKillThread")
_auto_kill_thread.start()
