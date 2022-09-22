from queue import Queue
from random import randint
from threading import Lock
from time import sleep, time
from typing import Union
from uuid import uuid4

from modules import M3U8, Config, Thread, Json

_ATD_QUEUE = Queue()

_PROGRESS_DICT = {}
_LOCK_DICT = {}
_FINISH_DICT = {}

_CANCEL_LIST = []

_ACTIVATE_THREAD = 0

def _download(uuid: str, retry: int=0, max_retry: int=Config.download_setting.download_retry):
    data = _PROGRESS_DICT[uuid]
    if data["from"] == "Myself":
        downloader = M3U8()
    args = (
        data["url"],
        _LOCK_DICT[uuid],
        data["out_path"],
        data["name"],
        data["connect_number"]
    )
    download_thread = Thread(target=downloader.download, args=args)
    download_thread.start()
    while download_thread.is_alive():
        if uuid in _CANCEL_LIST:
            _CANCEL_LIST.remove(uuid)
            if _LOCK_DICT[uuid].locked(): _LOCK_DICT[uuid].release()
            download_thread.stop()
            _PROGRESS_DICT[uuid]["cancel"] = True
            break
        data["progress"] = downloader.progress
        sleep(1)
    download_thread.join()
    downloader.clean_up()
    if _PROGRESS_DICT[uuid]["cancel"] == True:
        _FINISH_DICT[uuid] = time()
        return
    if download_thread.get_return() == True:
        _FINISH_DICT[uuid] = time()
        return
    if retry < max_retry:
        return _download(uuid, retry, max_retry)
    _PROGRESS_DICT[uuid]["error"] == True
    _FINISH_DICT[uuid] = time()
    return


def _auto_download_job(id: int):
    global _ACTIVATE_THREAD
    _ACTIVATE_THREAD += 1
    while id < Config.download_setting.auto_download_thread:
        if _ATD_QUEUE.empty():
            sleep(1)
            continue
        uuid = _ATD_QUEUE.get()
        _download(uuid)
    _ACTIVATE_THREAD -= 1

def _download_job(total_queue: Queue):
    while not total_queue.empty():
        uuid = total_queue.get()
        _download(uuid)

class Download_Queue:
    @staticmethod
    def add(
        url: Union[str, list],
        name: Union[str, list],
        out_path: str,
        from_: str,
        thread_number: int=Config.download_setting.auto_download_thread,
        connect_number: int=Config.download_setting.auto_download_connection,
        type_: int=1
    ) -> None:
        """
        新增至下載貯列。

        url: :class:`str|list`
            VPX連結。
        name: :class:`str`
            名稱。
        out_path: :class:`str`
            輸出路徑。
        from_: :class:`str`
            Myself或Anime1
        thread_number: :class:`int`
            線程數。
        connect_number: :class:`int`
            連接數。
        type_: :class:`int`
            下載類型。
            0=自動下載
            1=使用者下載
        """
        DOWNLOAD_DATA = {
            "url": "",
            "name": "",
            "progress": 0,
            "out_path": out_path,
            "from": from_,
            "connect_number": connect_number,
            "start": False,
            "pause": False,
            "cancel": False,
            "error": False
        }
        if type_ == 0:
            download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"
            while download_uuid in _PROGRESS_DICT.keys() or download_uuid in _FINISH_DICT.keys():
                download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"
            download_data = DOWNLOAD_DATA.copy()
            download_data["url"] = url
            download_data["name"] = name
            _PROGRESS_DICT[download_uuid] = download_data
            _LOCK_DICT[download_uuid] = Lock()
            _ATD_QUEUE.put(download_uuid)
        else:
            user_queue = Queue()
            for i in range(len(url)):
                download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"
                while download_uuid in _PROGRESS_DICT.keys() or download_uuid in _FINISH_DICT.keys():
                    download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"
                download_data = DOWNLOAD_DATA.copy()
                download_data["url"] = url[i]
                download_data["name"] = name[i]
                _PROGRESS_DICT[download_uuid] = download_data
                _LOCK_DICT[download_uuid] = Lock()
                user_queue.put(download_uuid)
            for _ in range(thread_number):
                Thread(target=_download_job, args=(user_queue)).start()
    
    @staticmethod
    def cancel(uuid: str) -> None:
        """
        取消下載。

        uuid: :class:`str`
            UUID。
        """
        if not _PROGRESS_DICT.get(uuid):
            return None
        _CANCEL_LIST.append(uuid)
    
    @staticmethod
    def pause(uuid: str) -> None:
        """
        暫停下載。

        uuid: :class:`str`
            UUID。
        """
        data = _PROGRESS_DICT.get(uuid)
        if not data:
            return None
        if data["start"] and not data["pause"] and not data["error"]:
            lock: Lock = _LOCK_DICT[uuid]
            lock.acquire()
            data["pause"] = True
    
    @staticmethod
    def resume(uuid: str) -> None:
        """
        恢復下載。

        uuid: :class:`str`
            UUID。
        """
        data = _PROGRESS_DICT.get(uuid)
        if not data:
            return None
        if data["start"] and data["pause"] and not data["error"]:
            lock: Lock = _LOCK_DICT[uuid]
            if lock.locked(): lock.release()
            data["pause"] = False

    @staticmethod
    def get_dict() -> str:
        return Json.dumps(_PROGRESS_DICT)

def auto_queue_update():
    """
    自動更新下載線程、貯列。
    """
    global _ACTIVATE_THREAD, _PROGRESS_DICT, _LOCK_DICT, _FINISH_DICT
    while True:
        if _ACTIVATE_THREAD < Config.download_setting.auto_download_thread:
            Thread(target=_auto_download_job, args=(_ACTIVATE_THREAD,), name=f"AutoDownloader_{_ACTIVATE_THREAD}").start()
        for uuid, f_time in _FINISH_DICT:
            if time() - f_time > 300:
                del _PROGRESS_DICT[uuid]
                del _LOCK_DICT[uuid]
                del _FINISH_DICT[uuid]
        sleep(1)

queue_update_thread = Thread(target=auto_queue_update, name="AutoThreadUpdateThread")
queue_update_thread.start()
