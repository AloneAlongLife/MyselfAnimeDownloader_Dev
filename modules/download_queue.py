from os.path import join
from queue import Queue
from random import randint
from threading import Lock
from time import sleep, time
from typing import Union
from uuid import uuid4

from modules import Anime1, Config, Downloader, Myself, Thread

MYSELF_URL = Config.myself_setting.url
ANIME1_URL = Config.anime1_setting.url

UUID_QUEUE = []
DOWNLOAD_DATA = {}
ACTIVATE_UUID = []

FINISH_UUID = {}

def gen_name(from_: str, type_: str, episode: str, data: dict) -> str:
    if from_ == "myself":
        if type_ == "dir":
            name_format = Config.myself_setting.customized_dir_name
        else:
            name_format = Config.myself_setting.customized_file_name
    elif from_ == "anime1":
        if type_ == "dir":
            name_format = Config.anime1_setting.customized_dir_name
        else:
            name_format = Config.anime1_setting.customized_file_name
    episode_num = episode.split(" ")[1]
    if name_format == "": name_format = "$N $E"
    name_format = name_format.replace("$N", data["name"])
    name_format = name_format.replace("$E", episode.zfill(Config.download_setting.zerofile))
    name_format = name_format.replace("$T", data.get("animate_type", ""))
    name_format = name_format.replace("$D", data.get("premiere_date", ""))
    name_format = name_format.replace("$B", data.get("episode_number", ""))
    name_format = name_format.replace("$A", data.get("author", ""))
    return name_format

def download_job(thread_id: int):
    while True:
        if len(UUID_QUEUE) == 0:
            sleep(1)
            continue
        uuid = None
        legal_uuid_queue = UUID_QUEUE[:Config.download_setting.download_thread]
        if ACTIVATE_UUID[thread_id] == None:
            for _uuid in legal_uuid_queue:
                if _uuid not in ACTIVATE_UUID:
                    ACTIVATE_UUID[thread_id] = _uuid
                    uuid = _uuid
                    break
            if uuid == None:
                sleep(1)
                continue
        else:
            uuid = ACTIVATE_UUID[thread_id]
            if uuid not in legal_uuid_queue:
                ACTIVATE_UUID[thread_id] = None
            sleep(1)
            continue

        data = DOWNLOAD_DATA[uuid]
        downloader: Downloader = data["downloader"]
        if downloader.status() == "unstart": downloader.start()
        elif downloader.status() == "pause": downloader.resume()
        while not downloader.is_finish() and uuid in legal_uuid_queue:
            legal_uuid_queue = UUID_QUEUE[:Config.download_setting.download_thread]
            sleep(1)
        if downloader.is_finish():
            if downloader.download_exception:
                data["exception"] += 1
                if data["exception"] > Config.download_setting.download_retry:
                    downloader.clean_up()
                    data["fail"] = True
                    FINISH_UUID[uuid] = time()
                    UUID_QUEUE.remove(uuid)
                    ACTIVATE_UUID[thread_id] = None
                else:
                    downloader = Downloader(data["url"], data["file_name"], data["dir_path"])
                    data["downloader"] = downloader
            else:
                FINISH_UUID[uuid] = time()
                UUID_QUEUE.remove(uuid)
                ACTIVATE_UUID[thread_id] = None
        else:
            downloader.pause()

def auto_clear_job():
    while True:
        for key in FINISH_UUID.keys():
            if time() - FINISH_UUID[key] > 300:
                del FINISH_UUID[key]
                del DOWNLOAD_DATA[key]
        sleep(10)


class Download_Queue:
    @staticmethod
    def add(url: str, episode: str, video_url: str):
        download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"
        while download_uuid in DOWNLOAD_DATA.keys(): download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"

        video_data = {
            "url": url,
            "exception": 0,
            "fail": False
        }
        if MYSELF_URL in url:
            video_data["type"] = "myself"
            animate_data = Myself.animate_info_table(url)
            dir_path = Config.myself_setting.download_path
        elif ANIME1_URL in url:
            video_data["type"] = "anime1"
            animate_data = Anime1.animate_info_table(url)
            dir_path = Config.anime1_setting.download_path
        dir_name = gen_name(video_data["type"], "dir", episode, animate_data)
        if Config.download_setting.animate_classify:
            dir_path = join(dir_path, dir_name)
        file_name = gen_name(video_data["type"], "file", episode, animate_data)
        video_data["dir_path"] = dir_path
        video_data["file_name"] = file_name
        video_data["downloader"] = Downloader(video_url, file_name, dir_path)

        DOWNLOAD_DATA[download_uuid] = video_data
        UUID_QUEUE.append(download_uuid)
    
    @staticmethod
    def pause(uuid: str):
        if uuid not in DOWNLOAD_DATA.keys() or uuid in FINISH_UUID.keys():
            return
        DOWNLOAD_DATA[uuid]["downloader"].pause()
    
    @staticmethod
    def resume(uuid: str):
        if uuid not in DOWNLOAD_DATA.keys() or uuid in FINISH_UUID.keys():
            return
        DOWNLOAD_DATA[uuid]["downloader"].resume()
    
    @staticmethod
    def upper(uuid: str):
        global UUID_QUEUE
        if uuid not in DOWNLOAD_DATA.keys() or uuid in FINISH_UUID.keys():
            return
        origin_index = UUID_QUEUE.index(uuid)
        if origin_index == 0:
            return
        upper_uuid = UUID_QUEUE[origin_index - 1]
        cuuid_queue = UUID_QUEUE.copy()
        cuuid_queue[origin_index - 1] = uuid
        cuuid_queue[origin_index] = upper_uuid
        UUID_QUEUE = cuuid_queue.copy()
    
    @staticmethod
    def lower(uuid: str):
        global UUID_QUEUE
        if uuid not in DOWNLOAD_DATA.keys() or uuid in FINISH_UUID.keys():
            return
        origin_index = UUID_QUEUE.index(uuid)
        if origin_index == len(UUID_QUEUE) - 1:
            return
        lower_uuid = UUID_QUEUE[origin_index + 1]
        cuuid_queue = UUID_QUEUE.copy()
        cuuid_queue[origin_index + 1] = uuid
        cuuid_queue[origin_index] = lower_uuid
        UUID_QUEUE = cuuid_queue.copy()

    @staticmethod
    def gen_dict():
        sort_list = list(FINISH_UUID.keys()) + UUID_QUEUE
        data = {}
        for uuid in sort_list:
            downloader: Downloader = DOWNLOAD_DATA[uuid]["downloader"]
            temp_data = {
                "name": DOWNLOAD_DATA[uuid]["file_name"],
                "progress": format(min(100 * downloader.progress(), 100), ".2f"),
                "status": downloader.status(),
                "fail": DOWNLOAD_DATA[uuid]["fail"]
            }
            data[uuid] = temp_data
        return {
            "sort_list": sort_list,
            "data": data
        }

for i in range(Config.download_setting.download_thread):
    Thread(target=download_job, name=f"AnimateDownloadThread_{i}", args=(i,)).start()
    ACTIVATE_UUID.append("")
Thread(target=auto_clear_job, name=f"AnimateClearThread").start()
