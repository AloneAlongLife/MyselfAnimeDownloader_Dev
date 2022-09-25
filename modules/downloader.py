from logging import getLogger
from os import makedirs
from os.path import abspath, getsize, isdir, isfile, join
from shutil import rmtree
from subprocess import DEVNULL, run
from threading import Lock
from time import sleep

from requests import RequestException, get, head

from modules import TYPE_RESPONSE, Cache, Config, Json, Thread, ThreadPool

logger = getLogger("main")

HEADERS = {
    "User-Agent": Config.download_setting.user_agent
}

# 資料節不可包含之字元:\/:*?"<>|
BAN = "\\/:*?\"<>|"
# 替代用字元
REPLACE = "_"

def _retouch_name(name: str) -> str:
    """
    避免不正當名字出現導致資料夾或檔案無法創建。
    :param name: str 名字。
    :return: str
    """
    for char in BAN: name = name.replace(char, REPLACE)
    return name

def _get_m3u8_url(url: str) -> str:
    """
    取得檔案位置

    url: :class:`str`
        資料集網址。

    return: :class:`str`
    """
    vpx_json: dict = Cache.cahce_requests(url, return_type=TYPE_RESPONSE).json() # 取得檔案網址
    host: str = sorted(vpx_json["host"], key=lambda x: x.get("weight"), reverse=True)[0]["host"] # 將主機依權重排序
    video_url: str = vpx_json['video']['720p']
    file_name = video_url.split("/")[-1]
    path = video_url.replace(f"/{file_name}", "")
    return f"{host}{path}", path, f"{host}{video_url}" # 主機位址, 路徑, 網址

class M3U8:
    def __init__(self, url: str, file_name: str, out_path: str) -> None:
        """
        url: :class:`str`
            VPX網址。
        file_name: :class:`str`
            輸出檔案名稱。
        out_path: :class:`str`
            輸出路徑。
        """
        self.download_exception = False # 發生例外
        self._cancel = False # 取消下載
        self._pause = False # 是否暫停
        self.total_block = 0 # 總分割檔案數
        self.progress_list = [] # 個別進度
        self.args_list = [] # (下載網址, 標號)
        self.lock_list: list[Lock] = [] # 線程鎖
        self.file_name = _retouch_name(file_name) # 輸出檔案
        self.out_path = _retouch_name(out_path) # 輸出資料夾
        if not isdir(self.out_path):
            makedirs(self.out_path)
        self.host, path, m3u8_url = _get_m3u8_url(url)

        m3u8_data = Cache.cahce_requests(m3u8_url)

        self.temp_dir_path = f"temp/{path}" # 片段資料夾
        if not isdir(self.temp_dir_path): # 建立資料夾
            makedirs(self.temp_dir_path)

        with open(f"{self.temp_dir_path}/ffmpeg_in", mode="w") as ffmpeg_file:
            total_block = 0
            for file_name in m3u8_data.split("\n"):
                if "#" in file_name or file_name == "":
                    continue
                ffmpeg_file.write(f"file '{file_name}'\n")

                self.args_list.append((file_name, total_block))
                self.progress_list.append(0)
                total_block += 1
            self.total_block = total_block
        
        self.thread_pool = ThreadPool(Config.download_setting.download_connection, self._job)
        for _ in range(Config.download_setting.download_connection):
            self.lock_list.append(Lock())
        
    def start(self):
        self.thread_pool.start(self.args_list)

    def pause(self):
        if self._pause == True: return
        self._pause = True
        for lock in self.lock_list:
            lock.acquire()
    
    def resume(self):
        if self._pause == False: return
        self._pause = False
        for lock in self.lock_list:
            if lock.locked():
                lock.release()
    
    def clean_up(self):
        try: rmtree(self.temp_dir_path)
        except: pass

    def cancel(self):
        self._cancel = True
        self.thread_pool.join()
        self.clean_up()
    
    def progress(self):
        return sum(self.progress_list) / self.total_block
    
    def is_finish(self):
        return not self.thread_pool.is_alive()

    def _job(self, file_name, block_id, thread_id) -> None:
        info_data = f"{self.temp_dir_path}/{file_name}.ifd"
        video_data = f"{self.temp_dir_path}/{file_name}"
        total_length = None
        download_length = 0
        headers = HEADERS.copy()
        headers["Range"] = f"bytes={download_length}-"
        if isfile(info_data):
            info: dict = Json.load(info_data)
            total_length = info["total_length"]
            download_length = getsize(video_data)
            if total_length <= download_length:
                self.progress_list[block_id] = 1
        if self.progress_list[block_id] != 1:
            try:
                with get(f"{self.host}/{file_name}", stream=True, headers=headers) as res:
                    if total_length == None:
                        total_length = int(res.headers.get('Content-length'))
                        info = {
                            "total_length": total_length,
                        }
                        Json.dump(info_data, info)
                    self.lock_list[thread_id].acquire()
                    for data in res.iter_content(1024):
                        self.lock_list[thread_id].release()
                        download_length += open(video_data, mode="ab").write(data)
                        self.progress_list[block_id] = download_length / total_length
                        self.lock_list[thread_id].acquire()
                        if self._cancel or self.download_exception: break
                    self.lock_list[thread_id].release()                
            except RequestException as e:
                logger.error(f"Request Error: {e}")
                self.download_exception = True
                return
        if block_id == self.total_block - 1:
            while sum(self.progress_list) < self.total_block: sleep(1)
            run(f"ffmpeg {Config.other_setting.ffmpeg_args} -v error -f concat -i \"{self.temp_dir_path}/ffmpeg_in\" -c copy -y \"" + abspath(join(self.out_path, self.file_name)) + ".mp4\"", shell=False, stdout=DEVNULL, stderr=DEVNULL)

class M3U8:
    def __init__(self, url: str, file_name: str, out_path: str) -> None:
        """
        url: :class:`str`
            VPX網址。
        file_name: :class:`str`
            輸出檔案名稱。
        out_path: :class:`str`
            輸出路徑。
        """
        self.download_exception = False # 發生例外
        self._cancel = False # 取消下載
        self._pause = False # 是否暫停
        self.total_block = 0 # 總分割檔案數
        self.progress_list = [] # 個別進度
        self.args_list = [] # (下載網址, 標號)
        self.lock_list: list[Lock] = [] # 線程鎖
        self.file_name = _retouch_name(file_name) # 輸出檔案
        self.out_path = _retouch_name(out_path) # 輸出資料夾
        if not isdir(self.out_path):
            makedirs(self.out_path)
        path = f"anime1/{url.split('/')[-2]}"

        self.temp_dir_path = f"temp/{path}" # 片段資料夾
        if not isdir(self.temp_dir_path): # 建立資料夾
            makedirs(self.temp_dir_path)
        
        total_length = int(head(url, headers=HEADERS).headers.get("Content-length"))

        with open(f"{self.temp_dir_path}/ffmpeg_in", mode="w") as ffmpeg_file:
            total_block = 0
            for file_name in m3u8_data.split("\n"):
                if "#" in file_name or file_name == "":
                    continue
                ffmpeg_file.write(f"file '{file_name}'\n")

                self.args_list.append((file_name, total_block))
                self.progress_list.append(0)
                total_block += 1
            self.total_block = total_block
        
        self.thread_pool = ThreadPool(Config.download_setting.download_connection, self._job)
        for _ in range(Config.download_setting.download_connection):
            self.lock_list.append(Lock())
        
    def start(self):
        self.thread_pool.start(self.args_list)

    def pause(self):
        if self._pause == True: return
        self._pause = True
        for lock in self.lock_list:
            lock.acquire()
    
    def resume(self):
        if self._pause == False: return
        self._pause = False
        for lock in self.lock_list:
            if lock.locked():
                lock.release()
    
    def clean_up(self):
        try: rmtree(self.temp_dir_path)
        except: pass

    def cancel(self):
        self._cancel = True
        self.thread_pool.join()
        self.clean_up()
    
    def progress(self):
        return sum(self.progress_list) / self.total_block
    
    def is_finish(self):
        return not self.thread_pool.is_alive()

    def _job(self, file_name, block_id, thread_id) -> None:
        info_data = f"{self.temp_dir_path}/{file_name}.ifd"
        video_data = f"{self.temp_dir_path}/{file_name}"
        total_length = None
        download_length = 0
        headers = HEADERS.copy()
        headers["Range"] = f"bytes={download_length}-"
        if isfile(info_data):
            info: dict = Json.load(info_data)
            total_length = info["total_length"]
            download_length = getsize(video_data)
            if total_length <= download_length:
                self.progress_list[block_id] = 1
        if self.progress_list[block_id] != 1:
            try:
                with get(f"{self.host}/{file_name}", stream=True, headers=headers) as res:
                    if total_length == None:
                        total_length = int(res.headers.get('Content-length'))
                        info = {
                            "total_length": total_length,
                        }
                        Json.dump(info_data, info)
                    self.lock_list[thread_id].acquire()
                    for data in res.iter_content(1024):
                        self.lock_list[thread_id].release()
                        download_length += open(video_data, mode="ab").write(data)
                        self.progress_list[block_id] = download_length / total_length
                        self.lock_list[thread_id].acquire()
                        if self._cancel or self.download_exception: break
                    self.lock_list[thread_id].release()                
            except RequestException as e:
                logger.error(f"Request Error: {e}")
                self.download_exception = True
                return
        if block_id == self.total_block - 1:
            while sum(self.progress_list) < self.total_block: sleep(1)
            run(f"ffmpeg {Config.other_setting.ffmpeg_args} -v error -f concat -i \"{self.temp_dir_path}/ffmpeg_in\" -c copy -y \"" + abspath(join(self.out_path, self.file_name)) + ".mp4\"", shell=False, stdout=DEVNULL, stderr=DEVNULL)

# https://shiro.v.anime1.me/1055/23.mp4
# if __name__ == "__main__":
#     M3U8().download("https://v.myself-bbs.com/vpx/48642/001", name="test")
