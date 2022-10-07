from logging import getLogger
from os import makedirs
from os.path import abspath, getsize, isdir, isfile, join
from shutil import rmtree
from subprocess import DEVNULL, run
from urllib.parse import unquote
from threading import Lock
from time import sleep
from bs4 import BeautifulSoup

from requests import RequestException, get, head, post

from modules import TYPE_RESPONSE, Cache, Config, Json, Thread, ThreadPool

logger = getLogger("main")

HEADERS = {
    "User-Agent": Config.download_setting.user_agent
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
    取得檔案位置

    url: :class:`str`
        資料集網址。

    return: :class:`str`
    """
    if ".m3u8" in url:
        video_url = "/".join(url.split("/")[-3:])
        host = url.replace(video_url, "")
    else:
        vpx_json: dict = Cache.cache_requests(url, return_type=TYPE_RESPONSE, read_from_cache=False).json() # 取得檔案網址
        host: str = sorted(vpx_json["host"], key=lambda x: x.get("weight"), reverse=True)[0]["host"] # 將主機依權重排序
        video_url: str = vpx_json['video']['720p']
    file_name = video_url.split("/")[-1]
    path = video_url.replace(f"/{file_name}", "")
    return f"{host}{path}", path, f"{host}{video_url}" # 主機位址, 路徑, 網址

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
