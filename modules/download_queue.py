from queue import Queue
from random import randint
from threading import Lock
from time import sleep, time
from typing import Union
from uuid import uuid4

from modules import M3U8, Config, Thread, Json

download_uuid = f"{chr(randint(97, 122))}-{uuid4().hex}"

class Download_Queue():
    def __init__(self) -> None:
        self._data = {}
        self._sort = []
        self._queue_sort = []

    def put(self, uuid: str, data: dict) -> None:
        self._data[uuid] = data
        sort_data = (uuid, len(self._sort) + 1)
        self._sort.append(sort_data)
        self._queue_sort.append(sort_data)

    def get(self) -> dict:
        uuid = self._queue_sort.pop(0)[0]
        return self._data[uuid]
    
    def up_order(self, uuid: str) -> None:
        origin_index = self.
