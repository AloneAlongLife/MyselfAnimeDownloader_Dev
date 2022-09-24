from queue import Queue
from random import randint
from threading import Lock
from time import sleep, time
from typing import Union
from uuid import uuid4

from modules import M3U8, Config, Thread, Json

MYSELF_URL = Config.myself_setting.url
ANIME1_URL = Config.anime1_setting.url

UUID_QUEUE = []
DOWNLOAD_DATA = {}

FINISH_UUID = {}

def download_job():
    while True:
        if len(UUID_QUEUE) == 0:
            sleep(1)
            continue
        uuid = UUID_QUEUE.pop(0)
        data = DOWNLOAD_DATA[uuid]
        if MYSELF_URL in data["url"]:
            from_ = "myself"
        elif ANIME1_URL in data["url"]:
            from_ = "anime1"

class Download_Queue:
    @staticmethod
    def add(url: str, episode: str, video_url: str):
        download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"
        while download_uuid in DOWNLOAD_DATA.keys(): download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"
        video_data = {
            "url": url,
            "episode": episode,
            "video_url": video_url,
            "status": "not_start",
            "progress": 0
        }
        DOWNLOAD_DATA[download_uuid] = video_data
        UUID_QUEUE.append((download_uuid, len(UUID_QUEUE)))
    
    @staticmethod
    def pause(uuid: str):
        if uuid in DOWNLOAD_DATA.keys() and uuid not in FINISH_UUID.keys():
            return
        DOWNLOAD_DATA[uuid]["status"] = "pause"
    
    @staticmethod
    def resume(uuid: str):
        if uuid in DOWNLOAD_DATA.keys() and uuid not in FINISH_UUID.keys():
            return
        DOWNLOAD_DATA[uuid]["status"] = "start"
    
    @staticmethod
    def update_sort():
        sort_data = sorted(UUID_QUEUE, key=lambda x: x[1])
        offset = 0 - UUID_QUEUE[0][1]
        UUID_QUEUE = list(map(lambda x: (x[0], x[1] + offset), UUID_QUEUE))

for i in range(Config.download_setting.download_thread):
    Thread(target=download_job, name=f"AnimateDownloadThread_{i}").start()