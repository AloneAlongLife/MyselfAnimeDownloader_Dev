import logging

from flask import Flask, Request, redirect, render_template, request, url_for
from modules.config import Config
from modules.json import Json

logger = logging.getLogger("main")

def _deal_requeste(type_of: str, data: str | bytes, raw_requests: Request):
    try:
        logger.info(f"Get Request Type:{type_of}; Data:{data.decode('utf-8')}")
    except:
        logger.info(f"Get Request Type:{type_of}; Data:{data}")
    if type_of == "include":
        return render_template(Json.loads(data).get("file_name"))
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
    
    @app.route("/home")
    def home():
        return render_template("home.html")

    @app.route("/info")
    def info():
        return render_template("info.html")

    @app.route("/data")
    def data():
        return render_template("data.html")

    @app.route("/api/v1.0/<data>")
    def api(data: str):
        if data == "queue":
            from random import randint
            return [{"name": "test_1", "progress": randint(0, 100), "id": "abcd"}]
        return ("", 204)
    
    def run(self):
        self.app.run(
            host=Config.web_console.host,
            port=Config.web_console.port,
            debug=Config.web_console.debug,
            use_reloader=False
        )
