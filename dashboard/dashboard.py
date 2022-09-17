import logging
from urllib.parse import unquote

from flask import (Flask, Request, make_response, redirect, render_template,
                   request, url_for)
from modules import Cache, Config, Json, Myself

logger = logging.getLogger("main")

def _deal_requeste(type_of: str, data: str | bytes, raw_requests: Request):
    try:
        logger.info(f"Get Request Type:{type_of}; Data:{data.decode('utf-8')}")
    except:
        logger.info(f"Get Request Type:{type_of}; Data:{data}")
    try:
        if type_of == "include":
            return render_template(raw_requests.json.get("file_name"))
        elif type_of == "send_setting_form":
            for item in raw_requests.json.items():
                if item[1] == None: continue
                Config.myself_setting[item[0]] = type(Config.myself_setting.get(item[0], ""))(item[1])
            Config.save()
        elif type_of == "get_setting_form":
            return Config.myself_setting.to_str()
        elif type_of == "animate_info":
            keyword = raw_requests.json["keyword"]
            if "://" in keyword:
                return Json.dumps({"type": "url", "data": Myself.animate_info_table(keyword)})
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
            # from random import randint
            # return [{"name": "test_1", "progress": randint(0, 100), "id": "abcd"}, {"name": "test_2", "progress": randint(0, 100), "id": "abce"}]
            return []
        return ("", 404)
    
    def run(self):
        self.app.run(
            host=Config.web_console.host,
            port=Config.web_console.port,
            debug=Config.web_console.debug,
            use_reloader=False
        )
