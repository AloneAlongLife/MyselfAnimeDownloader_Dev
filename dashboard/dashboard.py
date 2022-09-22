import logging
from urllib.parse import unquote

from flask import (Flask, Request, make_response, render_template,
                   request)
from modules import Cache, Config, Json, Myself, Download_Queue, google_search_redirect

logger = logging.getLogger("main")

MYSELF_URL = Config.myself_setting.url
ANIME1_URL = Config.anime1_setting.url

def _deal_requeste(type_of: str, data: str | bytes, raw_requests: Request):
    try:
        logger.info(f"Get Request Type:{type_of}; Data:{data.decode('utf-8')}")
    except:
        logger.info(f"Get Request Type:{type_of}; Data:{data}")
    try:
        if type_of == "include":
            return render_template(raw_requests.json.get("file_name"))
        elif type_of == "send_setting_form":
            for item in raw_requests.json.get("download_setting", {}).items():
                if item[1] == None: continue
                Config.download_setting[item[0]] = type(Config.download_setting.get(item[0], ""))(item[1])
            for item in raw_requests.json.get("myself_setting", {}).items():
                if item[1] == None: continue
                Config.myself_setting[item[0]] = type(Config.myself_setting.get(item[0], ""))(item[1])
            for item in raw_requests.json.get("anime1_setting", {}).items():
                if item[1] == None: continue
                Config.anime1_setting[item[0]] = type(Config.anime1_setting.get(item[0], ""))(item[1])
            Config.save()
        elif type_of == "get_setting_form":
            return {
                "download_setting": Config.download_setting.to_str(),
                "myself_setting": Config.myself_setting.to_str(),
                "anime1_setting": Config.anime1_setting.to_str()
            }
        elif type_of == "animate_info":
            keyword = raw_requests.json["keyword"]
            from_ = raw_requests.json["from"]
            if "://" in keyword:
                keyword = google_search_redirect(keyword)
                if MYSELF_URL in keyword:
                    return Json.dumps({"type": "url", "data": Myself.animate_info_table(keyword, raw_requests.json["cache"])})
            if from_ == "Myself":
                return Json.dumps({"type": "search", "data": Myself.search(keyword)})
    except:
        return ("", 404)
    return ("", 204)

class Dashboard():
    app = Flask(__name__)
    def __init__(self) -> None:
        pass

    @app.route("/", methods=["GET", "POST"])
    def root():
        request_type = request.headers.get("Request-type")
        if request_type != None:
            return _deal_requeste(request_type, request.get_data(), request)
        return render_template("index.html")

    @app.route("/cache/img")
    def cache_img():
        url = request.args.get("url", "")
        image = Cache.read_from_cache(unquote(url))
        if not image: return ("", 404)
        response = make_response(image)
        response.headers.set('Content-Type', 'image')
        return response

    @app.route("/api/v1.0/<data>")
    def api(data: str):
        if data == "queue":
            return Download_Queue.get_dict()
        return ("", 404)
    
    def run(self):
        self.app.run(
            host=Config.web_console.host,
            port=Config.web_console.port,
            debug=Config.web_console.debug,
            use_reloader=False
        )
