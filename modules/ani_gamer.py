from logging import getLogger
from time import time

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import get

from modules import Config

logger = getLogger("main")

# 網址
URL = "https://ani.gamer.com.tw"

# 偽裝瀏覽器
HEADERS = {
    "User-Agent": Config.download_setting.user_agent
}

class Ani_Gamer:
    @staticmethod
    def week_animate() -> list:
        """
        爬首頁的每週更新表。
        (index 0 對應星期一)

        return: :class:`list`
        [
            [
                {
                    "name": 動漫名字,
                    "url": 動漫網址,
                    "update": 更新集數,
                },
                {...}
            ],
            [...]
        ]
        """
        res = get(URL, headers=HEADERS).content.decode()
        if res == None: return []
        week_data = []
        page = BeautifulSoup(res, features="html.parser")
        week_list: list[Tag] = page.select("div.day-list")
        for day_data in week_list:
            week_data.append([])
            day_list: list[Tag] = day_data.find_all("a")
            if len(day_list) == 0:
                continue
            for ani_info in day_list:
                week_data[-1].append(
                    {
                        "name": ani_info.select_one("p.text-anime-name").text,
                        "url": f"{URL}/{ani_info.get('href')}",
                        "update": ani_info.select_one("p.text-anime-number").text
                    }
                )
        for i in range(7):
            week_data[i] = sorted(week_data[i], key=lambda x: x.get("name"))
        return week_data

if __name__ == "__main__":
    # print(Myself.animate_info_table("https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwjCnunV_If6AhXNtVYBHes3A2wQFnoECDAQAQ&url=https%3A%2F%2Fmyself-bbs.com%2Fthread-46195-1-1.html&usg=AOvVaw0h_qp-4xn19xy26BEvjrKN"))
    # print(Myself.animate_info_table("https://myself-bbs.com/thread-48691-1-1.html"))
    # print(Myself.week_animate())
    # open("test.json", mode="w").write(Json.dumps(Myself.finish_list()["2022"], indent=2))
    pass
