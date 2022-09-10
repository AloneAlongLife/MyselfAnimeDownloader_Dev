from os import makedirs
from os.path import isdir

if __name__ == "__main__":
    if not isdir("cache"): makedirs("cache") # 存放網頁資料
    if not isdir("temp"): makedirs("temp") # 存放影片待合成片段(.ts)

    