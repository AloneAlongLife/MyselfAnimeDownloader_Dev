from logging import getLogger
from time import time
from typing import Optional
from urllib.parse import unquote

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import get

from modules import Config

logger = getLogger("main")

# 網址
URL = Config.anime1_setting.url

# 偽裝瀏覽器
HEADERS = {
    "User-Agent": Config.download_setting.user_agent
}

def google_search_redirect(url: str) -> Optional[str]:
    if "www.google.com/url?" in url:
        url = unquote(url.split("url=")[1].split("&")[0])
    if len(url.replace(URL, "").split("/")) == 2:
        redirect = BeautifulSoup(get(url, headers=HEADERS).content.decode(), features="html.parser").select_one("a[href*=\"/?cat\"]").get("href")
        url = f"{URL}{redirect}"
    return url

def _total_data() -> list:
    return get(url=f"https://d1zquzjgwo9yb.cloudfront.net/?_={int(time())}").json()

class Anime1:
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
        main_page = BeautifulSoup(get(URL, headers=HEADERS).content.decode(), features="html.parser")
        week_page_url = main_page.select_one("#primary-menu > li:nth-of-type(2) > a").get("href")
        res = get(week_page_url, headers=HEADERS).content.decode()
        if res == None: return []
        total_data = _total_data()
        total_data.sort()
        offset = len(total_data) - total_data[-1][0]
        week_data = [[], [], [], [], [], [], []]
        CONV = [6, 0, 1, 2, 3, 4, 5]
        col_list: list[Tag] = BeautifulSoup(res, features="html.parser").select("tbody > tr")[:-1]
        for col in col_list:
            empty_num = 0
            week_list: list[Tag] = col.find_all("td")
            for i in range(7):
                day: Tag = week_list[i]
                if day.findChild("a"):
                    name = day.findChild().text
                    url = day.findChild().get("href")
                    update = ""
                    num = int(url.split("=")[-1])
                    for episode_data in total_data[num+offset::-1]:
                        if episode_data[0] == num:
                            update = episode_data[2]
                            break
                    week_data[CONV[i]].append({
                        "name": name,
                        "url": f"{URL}{url}",
                        "update": update
                    })
                else:
                    empty_num += 1
            if empty_num >= 7: break
        for i in range(7):
            week_data[i] = sorted(week_data[i], key=lambda x: x.get("name"))
        return week_data

    @staticmethod
    def animate_info_table(url: str) -> Optional[dict]:
        """
        取得動漫資訊

        res: :class:`str`
            網址。

        return: :class:`dict`
        {
            url: 網址,
            name: 名字,
            premiere_date: 首播日期,
            episode_number: 目前播出集數,
            episode_data: [{name: 集數, url: 網址},{...}]
        }
        """
        url = google_search_redirect(url)
        if URL not in url: return None
        res = get(url, headers=HEADERS).content.decode()
        if res == None: return None
        # 一般信息
        res = BeautifulSoup(res, features="html.parser")
        data = {
            "url": url,
            "name": res.find("h1", class_="page-title").text
        }
        all_episodes: list[Tag] = res.select("article")
        all_episodes.reverse()
        data["premiere_date"] = all_episodes[0].find("time").text
        data["episode_number"] = f"共 {len(all_episodes)} 話"
        # 影片資料
        episode_data = []
        for episode in all_episodes:
            content_a: Tag = episode.find_all('a')[1]
            ep_start = content_a.text.find("[") + 1
            ep_end = content_a.text.find("]")
            name = f"第 {content_a.text[ep_start:ep_end]} 話"
            data_url = content_a.get("href")
            episode_data.append({"name": name, "url": data_url})
        data["episode_data"] = episode_data
        return data

    @staticmethod
    def total_list() -> dict:
        """
        取得所有動漫資訊。

        return: :class:`dict`
        {
            "2022": {
                "2022年01月(冬)": [{"name": "失格紋的最強賢者", "url": "動漫網址"}, {...}],
                "2022年04月(春)": [{...}],
            }
        }
        """
        total_data = _total_data()
        if total_data == None: return {}
        CONV_DATA = {
            "冬": "01月(冬)",
            "春": "04月(春)",
            "夏": "07月(夏)",
            "秋": "10月(秋)"
        }
        data = {}
        for episode in total_data:
            if episode[0]:
                year = episode[3].split("/")[0]
                season = episode[4].split("/")[0].replace(year, "")
                title = f"{year}年{CONV_DATA[season]}"
                name = episode[1]
                url = f"{URL}/?cat={episode[0]}"
                if data.get(year) == None: data[year] = {}
                if data[year].get(title) == None: data[year][title] = []
                data[year][title].append({"name": name, "url": url})
        return data
            
    @staticmethod
    def search(keyword: str) -> list:
        """
        搜尋動漫。

        keyword: :class:`str`
            關鍵字。

        return: :class:`list`
        [
            {"title": "OVERLORD 不死者之王 第四季","url": "動漫網址"},
            {...}
        ]
        """
        total_data: list = get(url=f"https://d1zquzjgwo9yb.cloudfront.net/?_={int(time())}").json()
        if total_data == None: return []
        data = []
        for episode in total_data:
            name: str = episode[1]
            for key in keyword.split(" "):
                if key.lower() in name.lower():
                    url = f"{URL}/?cat={episode[0]}"
                    data.append({"title": name, "url": url})
                    break
        return data

if __name__ == "__main__":
    # print(Myself.animate_info_table("https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwjCnunV_If6AhXNtVYBHes3A2wQFnoECDAQAQ&url=https%3A%2F%2Fmyself-bbs.com%2Fthread-46195-1-1.html&usg=AOvVaw0h_qp-4xn19xy26BEvjrKN"))
    # print(Myself.animate_info_table("https://myself-bbs.com/thread-48691-1-1.html"))
    # print(Myself.week_animate())
    # open("test.json", mode="w").write(Json.dumps(Myself.finish_list()["2022"], indent=2))
    pass
