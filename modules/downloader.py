from logging import getLogger
from os import makedirs, remove
from os.path import abspath, getsize, isdir, isfile, join
from shutil import rmtree
from subprocess import STDOUT, DEVNULL, run
from urllib.parse import unquote
from threading import Lock
from time import sleep
from bs4 import BeautifulSoup

from requests import RequestException, get, head, post

from modules import TYPE_RESPONSE, Cache, Config, Json, Thread, ThreadPool

logger = getLogger("main")

HEADERS = {
    "User-Agent": Config.download_setting.user_agent,
    "origin": "https://anime1.me"
}

MYSELF_URL = Config.myself_setting.url
ANIME1_URL = Config.anime1_setting.url

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

def _retouch_dir(name: str) -> str:
    """
    避免不正當名字出現導致資料夾或檔案無法創建。
    :param name: str 名字。
    :return: str
    """
    for char in BAN:
        if char != "\\" and char != "/":
            name = name.replace(char, REPLACE)
    return name

def _get_m3u8_url(url: str) -> str:
    """
    取得m3u8信息。

    url: :class:`str`
        Myself資料集網址。

    return: :class:`str`
    """
    # 取得檔案網址
    vpx_json: dict = get(url, headers=HEADERS).json()
    # 將主機依權重排序
    host_list = sorted(vpx_json["host"], key=lambda x: x.get("weight", -1), reverse=True)

    host: str = host_list[0]["host"]                   # 權重最高之主機
    video_url: str = vpx_json['video']['720p']         # 影片位置
    file_name = video_url.split("/")[-1]               # m3u8檔案名稱
    path = video_url.replace(f"/{file_name}", "")      # 資料夾位置
    return f"{host}{path}", path, f"{host}{video_url}" # 主機位址, 路徑, 網址

class Segment_Downloader():
    def __init__(
        self,
        url: str,
        file_name: str,
        out_path: str,
        temp_path: str,
        cookies=None,
        m3u8_source: str="",
        block_size: int=2048000
    ) -> None:
        """
        初始化。

        url: :class:`str`
            網址。(影音檔|m3u8檔)
        file_name: :class:`str`
            輸出檔案名稱。
        out_path: :class:`str`
            輸出路徑。
        temp_path: :class:`str`
            暫存路徑。
        cookies: :class:`Any`
            Cookies。
        m3u8_source: :class:`str`
            m3u8主機位置。
        block_size: :class:`int`
            分割檔大小。
        """
        self.download_exception = False                  # 發生例外
        self._cancel = False                             # 取消下載
        self._pause = False                              # 是否暫停
        self.args_list = []                              # 連接資料[(下載網址, 區塊編號, (起始位元, 結束位元)), ...]
        self.file_list: list[str] = []                   # 暫存檔清單
        self.file_name = _retouch_name(file_name)        # 輸出檔案名稱
        self.out_path = _retouch_dir(out_path)           # 輸出資料夾位置
        self.temp_dir_path = _retouch_dir(temp_path)     # 影片分割暫存位置
        self.progress_list: list[float]                  # 個別進度
        self.total_block = 0                             # 總區塊數
        self.url = url                                   # 影片連結
        self.cookies = cookies                           # Cookies
        self.m3u8 = self.url.endswith(".m3u8")           # 是否為m3u8檔
        self.thread_pool = ThreadPool(                   # 下載線程池
            Config.download_setting.download_connection,
            self._job
        )
        self.lock_list: list[Lock] = (                   # 線程鎖
            [Lock()] * Config.download_setting.download_connection
        )
        
        # 建立資料夾
        if not isdir(self.temp_dir_path): makedirs(self.temp_dir_path)
        if not isdir(self.out_path): makedirs(self.out_path)

        if self.m3u8:
            # URL修改
            if not m3u8_source.endswith("/"): m3u8_source += "/"
            # 取得m3u8資料
            raw_m3u8_data = get(url, headers=HEADERS, cookies=self.cookies).content.decode().split("\n")
            # 過濾內容，選取檔案名稱
            for line in raw_m3u8_data:
                if "#" in line or line == "":
                    continue
                self.total_block += 1
                # 新增至檔案清單
                self.file_list.append(line)
        else:
            # 取得檔案大小
            total_length = int(head(self.url, headers=HEADERS, cookies=self.cookies).headers.get("Content-length"))
            # 分割檔案長度
            self.total_block = total_length // block_size
            if total_length % block_size:
                self.total_block += 1
        
        # 新增合併文件
        with open(f"{self.temp_dir_path}/comp_in", mode="w") as comp_file:
            for i in range(self.total_block):
                if self.m3u8:
                    file_name = self.file_list[i]
                    source = f"{m3u8_source}{file_name}"
                    comp_file.write(f"file '{file_name}'\n")
                    b_start = 0
                    b_end = ""
                else:
                    source = self.url
                    b_start = block_size * i
                    b_end = min(b_start + block_size - 1, total_length)
                    # 新增至檔案清單
                    self.file_list.append(f"seg_{i}")
                self.args_list.append((source, i, (b_start, b_end)))
        self.progress_list = [0] * self.total_block
    
    def status(self):
        """
        當前狀態。

        return: :class:`str`
        "unstart"|"cancel"|"finish"|"pause"|"running"
        """
        if self.thread_pool.started == False:
            return "unstart"
        elif self._cancel:
            return "cancel"
        elif not self.thread_pool.is_alive():
            return "finish"
        elif self._pause:
            return "pause"
        return "running"
    
    def start(self):
        """
        開始下載。
        """
        self.thread_pool.start(self.args_list)

    def pause(self):
        """
        暫停下載。
        """
        if self._pause: return
        self._pause = True
        for lock in self.lock_list:
            lock.acquire()
    
    def resume(self):
        """
        恢復下載。
        """
        if self._pause == False: return
        self._pause = False
        for lock in self.lock_list:
            if lock.locked():
                lock.release()
    
    def clean_up(self):
        """
        清除暫存。
        """
        try: rmtree(self.temp_dir_path)
        except: pass

    def cancel(self):
        """
        取消下載。
        """
        if self._cancel: return
        self._cancel = True
        self.thread_pool.join()
        self.clean_up()
    
    def progress(self):
        """
        下載進度。

        return: :class:`float`
        0~1
        """
        return sum(self.progress_list) / self.total_block

    def _job(
        self,
        url: str,
        block_id: int,
        b_range: tuple,
        error_times: int=0,
        thread_id: int=-1
    ) -> None:
        """
        下載分支。

        url: :class:`str`
            檔案位置。(影音檔|ts檔)
        block_id: :class:`int`
            區塊ID。
        b_range: :class:`tuple`
            起始位元, 結束位元。
        error_times: :class:`int`
            錯誤次數。
        thread_id: :class:`int`
            線程ID, 供ThreadPool用。
        """
        file_name = self.file_list[block_id]                # 暫存檔名
        video_data = f"{self.temp_dir_path}/{file_name}"    # 暫存檔位置
        info_data = f"{self.temp_dir_path}/{file_name}.ifd" # 信息檔位置
        total_length = 0                                    # 檔案總大小
        download_length = 0                                 # 已下載大小
        headers = HEADERS.copy()                            # 標頭
        def write_file(_data):
            try:
                return open(video_data, mode="ab").write(_data)
            except PermissionError:
                sleep(1)
                return write_file(_data)

        # 嘗試獲取檔案信息
        try:
            # 取得檔案總大小
            total_length = Json.load(info_data)["total_length"]
            # 取得已下載大小
            download_length = getsize(video_data)
        except: pass

        # 檢查是否已完成下載
        if download_length >= total_length and total_length:
            self.progress_list[block_id] = 1
        
        # 如果未完成下載
        if not self.progress_list[block_id]:
            try:
                # 設定下載位元
                headers["Range"] = f"bytes={download_length+b_range[0]}-{b_range[1]}"
                with get(url, stream=True, headers=headers, cookies=self.cookies) as res:
                    # 如果檔案總大小為0
                    if not total_length:
                        total_length = int(res.headers.get('Content-length'))
                        Json.dump(info_data, {"total_length": total_length,})
                    
                    # 開始下載
                    self.lock_list[thread_id].acquire()
                    for data in res.iter_content(4096):
                        self.lock_list[thread_id].release()
                        # 寫入檔案
                        download_length += write_file(data)
                        # 更新進度
                        self.progress_list[block_id] = min(download_length / total_length, 1)
                        self.lock_list[thread_id].acquire()
                        # 檢查是否需要停止
                        if self._cancel or self.download_exception:
                            self.lock_list[thread_id].release()
                            return
                    self.lock_list[thread_id].release()
                    self.progress_list[block_id] = 1
            except RequestException as e:
                logger.error(f"Request Error: {e}")
                # 錯誤記數器
                if error_times >= Config.download_setting.download_retry:
                    self.download_exception = True
                    return
                # 移除發生錯誤之檔案
                remove(video_file)
                # 重新下載發生錯誤之檔案
                sleep(5)
                return self._job(url, block_id, b_range, thread_id, error_times+1)
        if block_id == self.total_block - 1:
            while self.progress() < 1:
                if self._cancel or self.download_exception:
                    return
                sleep(1)
            if self.m3u8:
                # 以FFmpeg輸出
                run(
                    f"ffmpeg {Config.other_setting.ffmpeg_args} -v error -f concat -i \"{self.temp_dir_path}/comp_in\" -c copy -y \"" + abspath(join(self.out_path, self.file_name)) + ".mp4\"",
                    shell=False,
                    stdout=DEVNULL,
                    stderr=STDOUT
                )
            else:
                # 讀取並輸出
                with open(abspath(join(self.out_path, self.file_name)) + ".mp4", mode="wb") as video_file:
                    for seg_file in self.file_list:
                        video_file.write(open(f"{self.temp_dir_path}/{seg_file}", mode="rb").read())
            # 清除暫存檔
            self.clean_up()

def downloader_generator(
    url: str,
    file_name: str,
    out_path: str
) -> Segment_Downloader:
    """
    url: :class:`str`
        網址。
        Myself: VPX網址
        Anime1: 頁面網址
    file_name: :class:`str`
        輸出檔案名稱。
    out_path: :class:`str`
        輸出路徑。
    """
    if ANIME1_URL in url:
        # 取得加密資料
        page = BeautifulSoup(get(url).content.decode(), features="html.parser")
        data_apireq = unquote(page.select_one("video[data-apireq*=\"\"]").get("data-apireq"))
        req_data = Json.loads(data_apireq)        # 解密資料
        path = f"{req_data['c']}/{req_data['e']}" # 取得路徑

        # 從API獲取資料
        res = post("https://v.anime1.me/api", data={"d": data_apireq})
        cookies = res.cookies                            # Cookies
        video_url = f"https:{res.json()['s'][0]['src']}" # 影片網址(影片檔|m3u8清單)

        # 檢查是否為m3u8檔
        host_index = video_url.find(".me")
        m3u8_source = video_url[:host_index+4]
        if video_url.endswith("playlist.m3u8"):
            m3u8_list = get(video_url, cookies=cookies).content.decode().split("\n")
            best_source = m3u8_list[-2]
            video_url = video_url.replace("playlist.m3u8", best_source)
    else:
        m3u8_source, path, video_url = _get_m3u8_url(url)
        cookies = None
    temp_path = f"temp/{path}"

    return Segment_Downloader(
        video_url,
        file_name,
        out_path,
        temp_path,
        cookies,
        m3u8_source
    )

class Downloader():
    def __init__(self, url: str, file_name: str, out_path: str, cookies=None) -> None:
        """
        url: :class:`str`
            VPX網址。
        file_name: :class:`str`
            輸出檔案名稱。
        out_path: :class:`str`
            輸出路徑。
        """
        # logger.debug(f"Downloader Reveive: {url} {file_name} {out_path}")
        self.download_exception = False # 發生例外
        self._cancel = False # 取消下載
        self._pause = False # 是否暫停
        self.total_block = 0 # 總分割檔案數
        self.progress_list = [] # 個別進度
        self.args_list = [] # (下載網址, 標號)
        self.lock_list: list[Lock] = [] # 線程鎖
        self.file_name = _retouch_name(file_name) # 輸出檔案
        self.out_path = _retouch_dir(out_path) # 輸出資料夾
        self.finish_block = 0

        self.url = url

        if ANIME1_URL in self.url: self.type = "anime1"
        else: self.type = "myself"

        if self.type == "myself":
            self.cookies = cookies
        elif self.type == "anime1":
            data_apireq = BeautifulSoup(get(self.url).content.decode(), features="html.parser").select_one("video[data-apireq*=\"\"]").get("data-apireq")
            req_data = Json.loads(unquote(data_apireq))
            res = post("https://v.anime1.me/api", data={"d": unquote(data_apireq)})
            self.cookies = res.cookies

            self.url = f"https:{res.json()['s'][0]['src']}"
            if self.url.split("/")[-1] == "playlist.m3u8":
                _file_name = get(url, cookies=self.cookies).content.decode().split("\n")[-2]
                self.url = self.url.replace("playlist.m3u8", _file_name)
                self.type = "myself"
        
        if self.type == "myself":
            self.host, path, m3u8_url = _get_m3u8_url(self.url)
            m3u8_data = Cache.cache_requests(m3u8_url, cookies=self.cookies, read_from_cache=True)
        elif self.type == "anime1":
            path = f"{req_data['c']}/{req_data['e']}"
            total_length = int(head(self.url, headers=HEADERS, cookies=self.cookies).headers.get("Content-length"))
            block_length = 2048000
            block_num = total_length // block_length
            if block_length * block_num < total_length: block_num += 1
        
        self.temp_dir_path = f"temp/{path}" # 片段資料夾
        if not isdir(self.temp_dir_path): # 建立資料夾
            makedirs(self.temp_dir_path)

        if not isdir(self.out_path):
            makedirs(self.out_path)

        with open(f"{self.temp_dir_path}/comp_in", mode="w") as comp_file:
            total_block = 0
            if self.type == "myself": _range_num = m3u8_data.split("\n")
            elif self.type == "anime1": _range_num = range(block_num)
            for content in _range_num:
                if self.type == "myself":
                    file_name = content
                    if "#" in file_name or file_name == "":
                        continue
                    comp_file.write(f"file '{file_name}'\n")
                    self.args_list.append((file_name, total_block))
                elif self.type == "anime1":
                    file_name = f"seg_{content}"
                    comp_file.write(f"{file_name}\n")
                    range_start = block_length * content
                    range_end = block_length * (content + 1) - 1
                    if content == block_num - 1:
                        range_end = total_length
                    self.args_list.append((file_name, total_block, (range_start, range_end)))
                self.progress_list.append(0)
                total_block += 1
            self.total_block = total_block
        
        self.thread_pool = ThreadPool(Config.download_setting.download_connection, self._job)
        for _ in range(Config.download_setting.download_connection):
            self.lock_list.append(Lock())
    
    def status(self):
        if self.thread_pool.started == False:
            return "unstart"
        elif self._cancel:
            return "cancel"
        elif self.is_finish():
            return "finish"
        elif self._pause:
            return "pause"
        return "running"
    
    def start(self):
        self.thread_pool.start(self.args_list)

    def pause(self):
        if self._pause: return
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
        if self._cancel: return
        self._cancel = True
        self.thread_pool.join()
        self.clean_up()
    
    def progress(self):
        "0~1"
        return sum(self.progress_list) / self.total_block
    
    def is_finish(self):
        return not self.thread_pool.is_alive()

    def _job(self, file_name, block_id, target_range=None, thread_id=-1) -> None:
        info_data = f"{self.temp_dir_path}/{file_name}.ifd"
        video_data = f"{self.temp_dir_path}/{file_name}"
        total_length = None
        download_length = 0
        headers = HEADERS.copy()
        if isfile(info_data):
            info: dict = Json.load(info_data)
            total_length = info["total_length"]
            try:
                download_length = getsize(video_data)
            except:
                download_length = 0
            if total_length <= download_length:
                self.progress_list[block_id] = 1
        if self.progress_list[block_id] != 1:
            try:
                if self.type == "myself":
                    headers["Range"] = f"bytes={download_length}-"
                elif self.type == "anime1":
                    headers["Range"] = f"bytes={download_length+target_range[0]}-{target_range[1]}"
                if self.type == "myself":
                    req_url = f"{self.host}/{file_name}"
                elif self.type == "anime1":
                    req_url = self.url
                with get(req_url, stream=True, headers=headers, cookies=self.cookies) as res:
                    if total_length == None:
                        total_length = int(res.headers.get('Content-length'))
                        info = {
                            "total_length": total_length,
                        }
                        Json.dump(info_data, info)
                    self.lock_list[thread_id].acquire()
                    for data in res.iter_content(4096):
                        self.lock_list[thread_id].release()
                        download_length += open(video_data, mode="ab").write(data)
                        self.progress_list[block_id] = min(download_length / total_length, 1)
                        self.lock_list[thread_id].acquire()
                        if self._cancel or self.download_exception:
                            self.lock_list[thread_id].release()
                            return
                    self.lock_list[thread_id].release()
            except RequestException as e:
                logger.error(f"Request Error: {e}")
                self.download_exception = True
                return
        self.finish_block += 1
        if block_id == self.total_block - 1:
            while self.finish_block < self.total_block:
                if self.download_exception or self._cancel:
                    return
                sleep(0.2)
            if self.type == "myself":
                run(f"ffmpeg {Config.other_setting.ffmpeg_args} -v error -f concat -i \"{self.temp_dir_path}/comp_in\" -c copy -y \"" + abspath(join(self.out_path, self.file_name)) + ".mp4\"", shell=False, stdout=DEVNULL, stderr=DEVNULL)
            elif self.type == "anime1":
                seg_list = open(f"{self.temp_dir_path}/comp_in").read().split("\n")[:-1]
                with open(abspath(join(self.out_path, self.file_name)) + ".mp4", mode="wb") as video_file:
                    for seg_file in seg_list:
                        video_file.write(open(f"{self.temp_dir_path}/{seg_file}", mode="rb").read())
            self.clean_up()

# https://shiro.v.anime1.me/1055/23.mp4
# if __name__ == "__main__":
#     M3U8().download("https://v.myself-bbs.com/vpx/48642/001", name="test")
