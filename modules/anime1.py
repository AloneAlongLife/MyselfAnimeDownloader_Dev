from logging import getLogger
from typing import Optional
from urllib.parse import unquote

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import get

from modules import Cache, Config

logger = getLogger("main")

# 網址
URL = Config.anime1_setting.url

def google_search_redirect(url: str) -> Optional[str]:
    if "www.google.com/url?" in url:
        url = unquote(url.split("url=")[1].split("&")[0])
    if len(url.replace(URL, "").split("/")) == 2:
        redirect = BeautifulSoup(Cache.cache_requests(url, read_from_cache=True), features="html.parser").select_one("a[href*=\"/?cat\"]").get("href")
        url = f"{URL}{redirect}"
    return url

class Anime1:
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
        res = Cache.cache_requests(url)
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
            name = f"第 {content_a.text[ep_start:ep_end]} 集"
            data_url = content_a.get("href")
            episode_data.append({"name": name, "url": data_url})
        data["episode_data"] = episode_data
        return data

    @staticmethod
    def finish_list(read_from_cache: bool=True) -> dict:
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
        res = Cache.cache_requests(url=f"{URL}/portal.php?mod=topic&topicid=8", read_from_cache=read_from_cache)
        if res == None: return []
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
        first_url = get(url=f"{URL}/search.php?mod=forum&srchtxt={keyword}&searchsubmit=yes").url
        res = Cache.cache_requests(first_url, save_to_cache=False)
        if res == None:
            return []
        result_pages: list[BeautifulSoup] = [BeautifulSoup(res, features="html.parser")]
        result_num = int(result_pages[0].find("div", class_="sttl mbn").text[:-4].split(" ")[-1])
        if result_num == 0: return []
        data = []
        page_num = result_num // 20 + 1
        for i in range(2, page_num + 1):
            result_pages.append(BeautifulSoup(Cache.cache_requests(f"{first_url}&page={i}", save_to_cache=False), features="html.parser"))
        for result_page in result_pages:
            for animate_element in result_page.select("#threadlist li"):
                data.append({"title": animate_element.find("h3").text.replace("\n", "").lstrip(), "url": f"{URL}/thread-{animate_element['id']}-1-1.html"})
        return data

if __name__ == "__main__":
    # print(Myself.animate_info_table("https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwjCnunV_If6AhXNtVYBHes3A2wQFnoECDAQAQ&url=https%3A%2F%2Fmyself-bbs.com%2Fthread-46195-1-1.html&usg=AOvVaw0h_qp-4xn19xy26BEvjrKN"))
    # print(Myself.animate_info_table("https://myself-bbs.com/thread-48691-1-1.html"))
    # print(Myself.week_animate())
    # open("test.json", mode="w").write(Json.dumps(Myself.finish_list()["2022"], indent=2))
    pass
