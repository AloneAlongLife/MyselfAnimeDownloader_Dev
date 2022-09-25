import logging
from turtle import down
from modules import Config, My_Datetime, set_logging, Thread, M3U8
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
    logger.info(f"Version: {Config.other_setting.version}")

    if not isdir("cache"): makedirs("cache") # 存放網頁資料
    if not isdir("temp"): makedirs("temp") # 存放影片待合成片段(.ts)

    if DEV_TEST:
        from modules import Myself
        # print(Myself.animate_info_table("https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwjCnunV_If6AhXNtVYBHes3A2wQFnoECDAQAQ&url=https%3A%2F%2Fmyself-bbs.com%2Fthread-46195-1-1.html&usg=AOvVaw0h_qp-4xn19xy26BEvjrKN"))
        # print(Myself.week_animate())
        # print(len(Myself.search("異世界")))
        downloader = M3U8("https://v.myself-bbs.com/vpx/48642/001", "測試_1", "/tes")
        downloader_2 = M3U8("https://v.myself-bbs.com/vpx/48642/002", "測試_2", "/tes")
        downloader.start()
        swc = False
        while not downloader.is_finish():
            sleep(1)
            progress_1 = downloader.progress()
            print(f"\r[{'=' * int(50 * progress_1)}]{format(100 * progress_1, '.2f')}%", end="")
            if progress_1 > 0.5 and not swc:
                downloader.cancel()
                break
                # swc = True
                # downloader.pause()
                # downloader_2.start()
                # print()
                # while not downloader_2.is_finish():
                #     progress_2 = downloader_2.progress()
                #     print(f"\r[{'=' * int(50 * progress_2)}]{format(100 * progress_2, '.2f')}%", end="")
                # print()
                # downloader.resume()
        downloader.clean_up()
        exit()
    
    dashboard = Dashboard()
    flask_thread = Thread(target=dashboard.run, name="FlaskThread")
    flask_thread.start()

    # while True:
    #     print(Config.myself_setting.auto_download_thread)
    #     sleep(1)

    flask_thread.join()
    