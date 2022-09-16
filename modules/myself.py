from logging import getLogger
from os import makedirs
from os.path import isdir, isfile
from typing import Union
from urllib.parse import unquote

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import get
from requests.exceptions import RequestException, Timeout

from modules import Config

logger = getLogger("main")

# 資料節不可包含之字元:\/:*?"<>|
BAN = "\\/:*?\"<>|"
# 替代用字元
REPLACE = "_"
# 網址
URL = Config.myself_setting.url

# 偽裝瀏覽器
HEADERS = {
    "User-Agent": Config.myself_setting.user_agent
}

# 動漫資訊的 Key 對照表
ANIMATE_TABLE = {
    "作品類型": "animate_type",
    "首播日期": "premiere_date",
    "播出集數": "episode_number",
    "原著作者": "author",
    "官方網站": "official_website",
    "備注": "remarks",
}

# 全形半形轉換表
HF_CONVERT = [("（", "("), ("）", ")")]


def retouch_name(name: str) -> str:
    """
    避免不正當名字出現導致資料夾或檔案無法創建。
    :param name: str 名字。
    :return: str
    """
    for char in BAN: name = name.replace(char, REPLACE)
    return name

def retouch_url(name: str) -> str:
    """
    避免不正當名字出現導致資料夾或檔案無法創建。
    :param name: str 名字。
    :return: str
    """
    for char in BAN:
        if char == "/":
            continue
        name = name.replace(char, REPLACE)
    return name


class Myself:
    @staticmethod
    def _req(url: str, timeout: int=5) -> Union[str, None]:
        try:
            r = get(url=url, headers=HEADERS, timeout=timeout)
            if r and r.ok:
                if URL in url:
                    file = url.replace(URL, "cache")
                else:
                    url = url.replace("://", "").split("/")
                    url[0] = "cache"
                    file = "/".join(url)
                file = retouch_url(file)
                path = "/".join(file.split("/")[:-1])
                if not isdir(path): makedirs(path)
                with open(file, mode="wb") as save_file: save_file.write(r.content)
                return r.content.decode("utf-8")
            return None
        except Timeout:
            file = url.replace(URL, "cache")
            file = retouch_url(file)
            if not isfile(file): return None
            logger.error(f"Request Timeout.")
            with open(file, mode="rb") as cache_file: return cache_file.read().decode("utf-8")
        except RequestException as e:
            logger.error(f"Request Error: {e}")
            return None
    
    @staticmethod
    def _save_to_cache(url: str, timeout: int=5) -> None:
        try:
            if URL in url:
                file = url.replace(URL, "cache")
            else:
                url = url.replace("://", "").split("/")
                url[0] = "cache"
                file = "/".join(url)
            file = retouch_url(file)
            path = "/".join(file.split("/")[:-1])
            if isfile(file): return None
            if not isdir(path): makedirs(path)
            r = get(url=url, headers=HEADERS, timeout=timeout)
            with open(file, mode="wb") as save_file: save_file.write(r.content)
            return None
        except RequestException as e:
            logger.error(f"Request Error: {e}")
            return None

    @staticmethod
    def _url_to_html(url: str, timeout: int=5) -> Union[str, None]:
        if url == None or url == "": return None
        if "!DOCTYPE html" in url: return url
        if "www.google.com/url?" in url: url = unquote(url.split("url=")[1].split("&")[0])
        return Myself._req(url, timeout)

    @classmethod
    def week_animate(self) -> list:
        """
        爬首頁的每週更新表。
        (index 0 對應星期一)

        return: :class:`list`
        [
            [
                {
                    "name": 動漫名字,
                    "url": 動漫網址,
                    "color": 字體顏色,
                    "update": 更新集數,
                },
                {...}
            ],
            [...]
        ]
        """
        res = self._req(url=f"{URL}/portal.php")
        if res == None:
            return []
        week_data = []
        week_elements: list[Tag] = BeautifulSoup(res, features="html.parser").find("div", id="tabSuCvYn").find_all("div", class_="module cl xl xl1")
        for day_element in week_elements:
            day_data = []
            for element in day_element.find_all("li"):
                print(element)
                _a: Tag = element.find("a")
                _fonts: list[Tag] = element.find_all("font")
                day_data.append(
                    {
                        "name": _fonts[0].text,
                        "url": f"{URL}/{_a.get('href')}",
                        "color": _fonts[2].get("style")[:-1].split(": ")[1],
                        "update": _fonts[2].text
                    }
                )
            week_data.append(day_data)
        return week_data

    @classmethod
    def animate_info_table(self, res: str) -> Union[dict, None]:
        """
        取得動漫資訊

        res: :class:`str`
            網頁或網址。

        return: :class:`dict`
        {
            name: 名字,
            animate_type: 作品類型,
            premiere_date: 首播日期,
            episode_number: 播出集數,
            author: 原著作者,
            official_website: 官方網站,
            remarks: 備注,
            synopsis: 簡介,
            image: 封面連結,
            episode_data: [{name: 集數, url: 網址},{...}]
        }
        """
        res = self._url_to_html(res)
        if res == None: return None
        # 一般信息
        data = {}
        res: BeautifulSoup = BeautifulSoup(res, features="html.parser")
        all_info: list[Tag] = res.find("div", class_="info_info").find_all("li")
        for info in all_info:
            key, value = info.text.split(": ")
            data[ANIMATE_TABLE[key]] = value
        img_src = res.find("div", class_="info_img_box").find("img").get("src")
        self._save_to_cache(img_src)
        data["name"] = res.find("title").text.split("【")[0]
        data["image"] = img_src
        data["synopsis"] = res.find("div", id="info_introduction_text").text
        # 影片資料
        _REPLACE_LIST = [("player/play", "vpx"), ("\r", ""), ("\n", "")]
        episode_data = []
        all_episodes: list[Tag] = res.find("ul", class_="main_list").select("a[href=\"javascript:;\"]")
        for episode in all_episodes:
            name = episode.text
            data_url = episode.find_next("a").get("data-href")
            for _replace in _REPLACE_LIST: data_url = data_url.replace(*_replace) # 更改連結&移除字元 \r \n
            episode_data.append({"name": name, "url": data_url})
        data["episode_data"] = episode_data
        return data

    @classmethod
    def finish_list(self) -> dict:
        """
        取得完結列表頁面的動漫資訊。

        return: :class:`dict`
        {
            "2022": [
                {"title": "2022年01月(冬)","data": [{"name": "失格紋的最強賢者", "url": "動漫網址"}, {...}]},
                {"title": "2022年04月(春)", "data": [{...}]}.
                {...}
            ]
        }
        """
        res = self._req(url=f"{URL}/portal.php?mod=topic&topicid=8")
        if res == None:
            return []
        data = {}
        all_years: list[Tag] = BeautifulSoup(res, features="html.parser").find_all("div", class_="tab-title title column cl")
        for year in all_years:
            year_list = []
            all_seasons: list[Tag] = year.find_all("div", class_="blocktitle title")
            for season in all_seasons:
                season_data = {}
                title = season.text
                for _replace in HF_CONVERT: title = title.replace(*_replace)
                season_data["title"] = title
                all_animates: list[Tag] = season.find_next("div", class_="module cl xl xl1").find_all("a")
                animate_list = []
                for animate in all_animates:
                    animate_list.append({"name": animate.text, "url": f"{URL}/{animate.get('href')}"})
                season_data["data"] = animate_list
                year_list.append(season_data)
            year_list.reverse()
            data[year_list[0]["title"].split("年")[0]] = year_list
        return data
    
    @classmethod
    def search(self, keyword: str):
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
        first_url = get(url=f"{URL}/search.php?mod=forum&srchtxt={keyword}&searchsubmit=yes").url
        res = self._req(first_url)
        if res == None:
            return []
        result_pages: list[BeautifulSoup] = [BeautifulSoup(res, features="html.parser")]
        result_num = int(result_pages[0].find("div", class_="sttl mbn").text[:-4].split(" ")[-1])
        if result_num == 0: return []
        data = []
        page_num = result_num // 20 + 1
        for i in range(2, page_num + 1):
            result_pages.append(BeautifulSoup(self._req(f"{first_url}&page={i}"), features="html.parser"))
        for result_page in result_pages:
            for animate_element in result_page.find("div", id="threadlist").find_all("li"):
                data.append({"title": animate_element.find("h3").text.replace("\n", "").lstrip(), "url": f"{URL}/thread-{animate_element['id']}-1-1.html"})
        return data

if __name__ == "__main__":
    # print(Myself.animate_info_table("https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwjCnunV_If6AhXNtVYBHes3A2wQFnoECDAQAQ&url=https%3A%2F%2Fmyself-bbs.com%2Fthread-46195-1-1.html&usg=AOvVaw0h_qp-4xn19xy26BEvjrKN"))
    # print(Myself.animate_info_table("https://myself-bbs.com/thread-48691-1-1.html"))
    # print(Myself.week_animate())
    # open("test.json", mode="w").write(Json.dumps(Myself.finish_list()["2022"], indent=2))
    pass
