import ctypes
from queue import Queue
import threading
from os import system
from time import sleep
from typing import Optional

class Thread(threading.Thread):
    """
    可停止式線程。
    新增:
     - stop(): 強制停止線程。
     - get_return(): 取得函數回傳值。
    """
    # def __init__(self, group=None, target=..., name: Optional[str]=None, args: Optional[None]=(), kwargs: Optional[None]={}, *, daemon: Optional[bool]=None) -> None:
    #     self._args = args
    #     self._kwargs = kwargs
    #     super().__init__(group, target, name, args, kwargs, daemon=daemon)
    _return = None
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def get_return(self):
        return self._return

    def stop(self):
        if not self.is_alive() or self.ident == None: raise threading.ThreadError("The thread is not active.")
        elif ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(SystemExit)) == 1: return
        ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")

class ThreadPool():
    def __init__(self, num: int, job) -> None:
        self.num = num
        self.job = job
        
    def _job(self):
        while not self.input_queue.empty():
            args = self.input_queue.get()
            answer_index = self.index
            self.index += 1
            self.answer_list[answer_index] = self.job(*args)

    def start(self, args_list: Optional[list]=None):
        self.thread_list = []
        self.answer_list = []
        self.input_queue = Queue()
        self.index = 0
        for _ in range(len(args_list)):
            self.answer_list.append(None)
            self.input_queue.put(args_list.pop(0))
        for _ in range(self.num):
            self.thread_list.append(Thread(target=self._job))
            self.thread_list[-1].start()
    
    def stop(self):
        for thread in self.thread_list:
            if thread.is_alive(): thread.stop()

    def join(self):
        for thread in self.thread_list:
            thread.join()
        return self.answer_list

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
