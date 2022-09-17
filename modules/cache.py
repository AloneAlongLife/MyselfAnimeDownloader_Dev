from logging import getLogger
from os import makedirs
from os.path import isdir, isfile
from typing import Optional, Union
from urllib.parse import unquote

from requests import get
from requests.exceptions import RequestException, Timeout
from requests.models import Response

from modules import Config

logger = getLogger("main")

# 資料節不可包含之字元:\/:*?"<>|
BAN = "\\/:*?\"<>|"
# 替代用字元
REPLACE = "_"
# 網址
URL = Config.myself_setting.url

# 偽裝瀏覽器
HEADERS = {
    "User-Agent": Config.myself_setting.user_agent
}

def _retouch_url(name: str) -> str:
    """
    避免不正當名字出現導致資料夾或檔案無法創建。
    :param name: str 名字。
    :return: str
    """
    for char in BAN:
        if char == "/":
            continue
        name = name.replace(char, REPLACE)
    return name

TYPE_RESPONSE = 0
TYPE_BYTES = 1
TYPE_STR = 2

class Cache:
    @staticmethod
    def cahce_requests(url: str, timeout: int=5, return_type: int=TYPE_STR, read_from_cache=False, save_to_cache=True) -> Union[bytes, str, Response, None]:
        try:
            if read_from_cache:
                res = None
                content = Cache.read_from_cache(url)
            else:
                res = get(url=url, headers=HEADERS, timeout=timeout)
                if not res or not res.ok: return None
                content = res.content
                if save_to_cache: Cache.data_to_cache(content, url)
            if return_type == TYPE_STR:
                try: return content.decode("utf-8")
                except: pass
            if return_type == TYPE_BYTES:
                return content
            return res
        except Timeout:
            return Cache.read_from_cache(url, False)
        except RequestException as e:
            logger.error(f"Request Error: {e}")
            return None

    @staticmethod
    def url_to_cahce(url: str, timeout: int=5) -> None:
        try:
            Cache.data_to_cache(get(url=url, headers=HEADERS, timeout=timeout).content, url)
            return None
        except RequestException as e:
            logger.error(f"Request Error: {e}")
            return None

    @staticmethod
    def data_to_cache(data: Union[bytes, str], url: str="") -> None:
        if type(data) != bytes: data = data.encode()
        if URL in url:
            file = url.replace(URL, "cache")
        else:
            url_rep = url.replace("://", "").split("/")
            url_rep[0] = "cache"
            file = "/".join(url_rep)
        file = _retouch_url(file)
        path = "/".join(file.split("/")[:-1])
        if not isdir(path): makedirs(path)
        open(file, mode="wb").write(data)
        return None

    @staticmethod
    def read_from_cache(url: str="", auto_download=True) -> Optional[bytes]:
        if URL in url:
            file = url.replace(URL, "cache")
        else:
            url_rep = url.replace("://", "").split("/")
            url_rep[0] = "cache"
            file = "/".join(url_rep)
        file = _retouch_url(file)
        if not isfile(file):
            if auto_download:
                Cache.url_to_cahce(url)
                if isfile(file): return open(file, mode="rb").read()
            return None
        return open(file, mode="rb").read()
