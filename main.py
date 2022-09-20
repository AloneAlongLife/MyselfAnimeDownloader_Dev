import logging
from modules import Config, My_Datetime, set_logging, Thread
from dashboard import Dashboard
from os import makedirs
from os.path import isdir
from time import sleep

set_logging()
logger = logging.getLogger("main")

DEV_TEST = False

# 檢查設置檔。
while Config.readied == None: sleep(1)
# if Config.readied == False:
#     input("Press any key to exit...")
#     exit()

if __name__ == "__main__":
    if DEV_TEST:
        from modules import Myself
        # print(Myself.animate_info_table("https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwjCnunV_If6AhXNtVYBHes3A2wQFnoECDAQAQ&url=https%3A%2F%2Fmyself-bbs.com%2Fthread-46195-1-1.html&usg=AOvVaw0h_qp-4xn19xy26BEvjrKN"))
        # print(Myself.week_animate())
        print(len(Myself.search("異世界")))
        exit()
    logger.info(f"Version: {Config.other_setting.version}")

    if not isdir("cache"): makedirs("cache") # 存放網頁資料
    if not isdir("temp"): makedirs("temp") # 存放影片待合成片段(.ts)

    dashboard = Dashboard()
    flask_thread = Thread(target=dashboard.run, name="FlaskThread")
    flask_thread.start()

    # while True:
    #     print(Config.myself_setting.auto_download_thread)
    #     sleep(1)

    flask_thread.join()
    