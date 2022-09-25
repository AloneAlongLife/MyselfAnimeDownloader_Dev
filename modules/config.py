import logging
from datetime import timedelta as d_timedelta
from datetime import timezone as d_timezone
from os.path import getmtime, isfile
from threading import Lock
from time import sleep
from typing import Union

from modules.json import Json
from modules.threading import Thread

logger = logging.getLogger("main")
_FILE_PATH = "config.json"

_CONFIG: dict
modify_time = 0

_auto_update_lock = Lock()

def _gen_config():
    """
    如果沒有設置檔，則從範例中生成。
    """
    with open("config-example.json", mode="rb") as example_file:
        EXAMPLE_DATA = example_file.read()
    with open(_FILE_PATH, mode="wb") as config_file:
        config_file.write(EXAMPLE_DATA)
    Config.update()
    sleep(1)
    logger.critical("config.json not found.")
    logger.warning("Generate a new config.json from config-example.json.")
    Config._ready(False)
    # current_thread().stop()

def _config_patch():
    """
    設置檔完整度檢查。
    """
    EXAMPLE_DATA = Json.load("config-example.json")
    CONFIG_DATA = Json.load(_FILE_PATH)
    Json.dump(_FILE_PATH, __patch(EXAMPLE_DATA, CONFIG_DATA))

def __patch(example: dict, config: dict):
    """
    設置完整度修復。
    """
    example = example.copy()
    config = config.copy()
    for key, value in example.items():
        try:
            c_value = config[key]
            if type(c_value) == dict:
                c_value = __patch(value, c_value)
                config[key] = c_value
        except KeyError:
            config[key] = value
    return config

class _Str_Dict(dict):
    def to_str(self):
        return Json.dumps(self)

class _Web_Console(_Str_Dict):
    host: str
    port: int
    debug: bool
    def __init__(self, _config: dict) -> None:
        for item in _config.items():
            self[item[0]] = item[1]
        self.host = _config["host"]
        self.port = _config["port"]
        self.debug = _config["debug"]

class _Other_Setting(_Str_Dict):
    time_zone: d_timezone
    ffmpeg_args: str
    log_level: str
    version: str
    def __init__(self, _config: dict) -> None:
        for item in _config.items():
            self[item[0]] = item[1]
        self.time_zone = d_timezone(d_timedelta(hours=_config["time_zone"]))
        self.ffmpeg_args = _config["ffmpeg_args"]
        self.log_level = _config["log_level"]
        self.version = _config["version"]

class _Download_Setting(_Str_Dict):
    user_agent: str
    animate_classify: bool
    download_connection: int
    download_thread: int
    download_retry: int
    zerofile: int
    def __init__(self, _config: dict):
        for item in _config.items():
            self[item[0]] = item[1]
        self.user_agent = _config["user_agent"]
        self.animate_classify = _config["animate_classify"]
        self.download_connection = _config["download_connection"]
        self.download_thread = _config["download_thread"]
        self.download_retry = _config["download_retry"]
        self.zerofile = _config["zerofile"]

class _Animate_Setting(_Str_Dict):
    url: str
    check_animate_update: int
    customized_file_name: str
    customized_dir_name: str
    download_path: str
    def __init__(self, _config: dict):
        for item in _config.items():
            self[item[0]] = item[1]
        self.url = _config["url"]
        self.check_animate_update = _config["check_animate_update"]
        self.customized_file_name = _config["customized_file_name"]
        self.customized_dir_name = _config["customized_dir_name"]
        self.download_path = _config["download_path"]

class Config:
    web_console: _Web_Console
    download_setting: _Download_Setting
    myself_setting: _Animate_Setting
    anime1_setting: _Animate_Setting
    other_setting: _Other_Setting
    updated: bool = False
    readied: Union[bool, None] = None

    @classmethod
    def update(self):
        """
        從設置檔中更新當前設置。
        """
        global _CONFIG
        _config_patch()
        _CONFIG = Json.load(_FILE_PATH)

        self.config = _CONFIG.copy()
        self.web_console = _Web_Console(_CONFIG["web_console"])
        self.download_setting = _Download_Setting(_CONFIG["download_setting"])
        self.myself_setting = _Animate_Setting(_CONFIG["myself_setting"])
        self.anime1_setting = _Animate_Setting(_CONFIG["anime1_setting"])
        self.other_setting = _Other_Setting(_CONFIG["other_setting"])
        self.updated = True

    @classmethod
    def _ready(self, value: bool):
        self.readied = value
    
    @classmethod
    def save(self):
        global modify_time
        _auto_update_lock.acquire()
        data = {}
        data["web_console"] = self.web_console
        data["download_setting"] = self.download_setting
        data["myself_setting"] = self.myself_setting
        data["anime1_setting"] = self.anime1_setting
        data["other_setting"] = self.other_setting
        Json.dump(_FILE_PATH, data)
        modify_time = getmtime(_FILE_PATH)
        _auto_update_lock.release()
        Config.update()

def auto_update():
    """
    自動更新設置檔。
    """
    global modify_time
    # 檢查檔案是否存在
    if not isfile(_FILE_PATH):
        _gen_config()
    else:
        Config.update()
    # 準備完成
    Config._ready(True)
    while True:
        # 檢查設置檔修改時間
        _auto_update_lock.acquire()
        if getmtime(_FILE_PATH) != modify_time:
            Config.update()
            modify_time = getmtime(_FILE_PATH)
        _auto_update_lock.release()
        sleep(1)

auto_update_thread = Thread(target=auto_update, name="ConfigAutoUpdateThread")
auto_update_thread.start()
