import logging
from modules import Config, My_Datetime, set_logging, Thread
from dashboard import Dashboard
from os import makedirs
from os.path import isdir
from time import sleep

set_logging()
logger = logging.getLogger("main")

# 檢查設置檔。
while Config.readied == None: sleep(1)
# if Config.readied == False:
#     input("Press any key to exit...")
#     exit()

if __name__ == "__main__":
    logger.info(f"Version: {Config.other_setting.version}")

    if not isdir("cache"): makedirs("cache") # 存放網頁資料
    if not isdir("temp"): makedirs("temp") # 存放影片待合成片段(.ts)

    dashboard = Dashboard()
    flask_thread = Thread(target=dashboard.run)
    flask_thread.start()

    while True:
        pass
    