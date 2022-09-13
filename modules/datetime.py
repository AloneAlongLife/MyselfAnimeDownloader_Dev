from datetime import datetime, time, timedelta
from time import sleep
from modules.config import Config

class My_Datetime:
    def now() -> datetime:
        """
        取得當前時間。
        
        return: :class:`datetime`
        """
        while not Config.updated: sleep(0.1)
        return datetime.now(Config.other_setting.time_zone).replace(tzinfo=None)
    
    def fileformat(timestamp: datetime=now()):
        return timestamp.replace(microsecond=0, tzinfo=None).isoformat().replace(":", "_")