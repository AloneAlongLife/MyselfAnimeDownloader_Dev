from datetime import time
import logging
from logging.config import dictConfig
from modules.config import Config
from modules.datetime import My_Datetime
from os import mkdir
from os.path import isdir
from time import sleep

class DatetimeFormatter(logging.Formatter):
    def format(self, record):
        record.ctime = My_Datetime.now().replace(microsecond=0).isoformat()

        return super().format(record)

def set_logging():
    while not Config.updated: sleep(0.1)
    midnight = time(0, 0, 0, 0, Config.other_setting.time_zone)
    if not isdir("logs"):
        mkdir("logs")
    if not isdir("web-logs"):
        mkdir("web-logs")
    dict_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s][%(levelname)s][%(threadName)s]: %(message)s"
            },
            "werkzeug": {
                "format": "[%(asctime)s][%(levelname)s]: %(message)s"
            },
            "debug": {
                "format": "[%(name)s][%(asctime)s][%(levelname)s][%(threadName)s]: %(message)s"
            }
        },
        "handlers":
        {
            "default_handler": {
                "class" : "logging.StreamHandler",
                "formatter": "default"
            },
            "main_file_handler": {
                "class" : "logging.handlers.TimedRotatingFileHandler",
                "filename": "logs/log.log",
                "formatter": "default",
                "when": "D",
                "interval": 1,
                "encoding": "utf-8",
                "atTime": midnight
            },
            "werkzeug_file_handler": {
                "class" : "logging.handlers.TimedRotatingFileHandler",
                "filename": "web-logs/web.log",
                "formatter": "werkzeug",
                "when": "D",
                "interval": 1,
                "encoding": "utf-8",
                "atTime": midnight
            }
        },
        "root": {
            "level": Config.other_setting.log_level,
            "handlers": []
        },
        "loggers": {
            "main": {
                "level": Config.other_setting.log_level,
                "handlers": ["default_handler", "main_file_handler"]
            },
            "werkzeug": {
                "level": Config.other_setting.log_level,
                "handlers": ["default_handler", "werkzeug_file_handler"]
            }
        }
    }
    dictConfig(dict_config)