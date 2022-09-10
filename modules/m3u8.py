from logging import getLogger
from os import makedirs
from os.path import getsize, isdir, isfile, join
from queue import Queue
from subprocess import DEVNULL, run
from typing import Union

from requests import RequestException, get
from requests.models import Response

from modules import Thread

logger = getLogger("MySelf")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 OPR/89.0.4447.64 (Edition GX-CN)",
}

class M3U8:
    progress = 0
    @staticmethod
    def _req(url: str, timeout: int=5) -> Union[Response, None]:
        try:
            r = get(url=url, headers=HEADERS, timeout=timeout)
            if r and r.ok:
                return r
            return None
        except RequestException as e:
            logger.error(f"Request Error: {e}")
            return None

    @staticmethod
    def _job(i, download_queue: Queue, progress: list, path: str) -> None:
        finish = 0
        while not download_queue.empty():
            url: str = download_queue.get()
            name = url.split("/")[-1]
            res = get(url, stream=True)
            total_length = int(res.headers.get('content-length'))
            if isfile(f"{path}/{name}"):
                if getsize(f"{path}/{name}") == total_length:
                    finish += 1
                    progress[i] = int(100 * finish)
                    continue
            with open(f"{path}/{name}", mode="wb") as video_file:
                download_length = 0
                for data in res.iter_content(40960):
                    video_file.write(data)
                    download_length += len(data)
                    progress[i] = int(100 * finish + 100 * download_length / total_length)
            finish += 1
            progress[i] = int(100 * finish)

    @classmethod
    def _get_m3u8_url(self, url: str) -> str:
        """
        取得檔案位置

        url: :class:`str`
            資料集網址。

        return: :class:`str`
        """
        vpx_json = self._req(url).json() # 取得檔案網址
        hosts = sorted(vpx_json["host"], key=lambda x: x.get("weight"), reverse=True) # 將主機依權重排序
        return f"{hosts[0]['host']}{vpx_json['video']['720p']}" # 組合網址

    def download(self, url: str, out_path: str="", name: str="", thread_number: int=6) -> None:
        """
        下載影片

        url: :class:`str`
            網址。

        return: :class:`str`
        """
        download_queue = Queue()
        progress = []
        thread_list = []
        self.progress = 0
        if ".m3u8" not in url:
            url = self._get_m3u8_url(url)
        m3u8_data = get(url).content.decode() # 取得檔案名稱

        host_url = "/".join(url.split("/")[:-1])
        video_id = url.split("/")[-3] # 取得影片id
        temp_path = f"temp/{video_id}" # 暫存路徑
        if not isdir(temp_path): makedirs(temp_path) # 建立資料夾
        open(f"{temp_path}/ffmpeg_in", mode="w") # 清空FFmpeg合成檔
        
        total_block = 0
        for file_name in m3u8_data.split("\n"):
            if "#" not in file_name and file_name != "":
                open(f"{temp_path}/ffmpeg_in", mode="a").write(f"file '{file_name}'\n")
                download_queue.put(f"{host_url}/{file_name}")
                total_block += 1
        for i in range(thread_number):
            progress.append(0)
            thread_list.append(Thread(target=self._job, args=(i, download_queue, progress, temp_path)))
            thread_list[-1].start()

        temp_progress = sum(progress)
        while temp_progress < 100 * total_block: # 更改進度
            temp_progress = sum(progress)
            self.progress = temp_progress / total_block

        for thread in thread_list:
            thread.join()
        
        run(f"ffmpeg -f concat -i \"{temp_path}/ffmpeg_in\" -c copy \"" + join(out_path, name) + ".mp4\"", shell=False, stdout=DEVNULL, stderr=DEVNULL)
    
if __name__ == "__main__":
    M3U8().download("https://v.myself-bbs.com/vpx/48642/001", name="test")
