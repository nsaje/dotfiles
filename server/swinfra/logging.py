import datetime
import logging
from typing import Callable
from typing import Optional

from pythonjsonlogger import jsonlogger


class OBJsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self, version_getter: Optional[Callable[[], str]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version_getter = version_getter or (lambda: "1")

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict):
        breakpoint()
        super(OBJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["thread"] = record.processName + "-" + str(record.process)
        log_record["loggerName"] = record.name
        log_record["filename"] = record.module
        log_record["timeMillis"] = record.created * 1000
        log_record["lineno"] = str(record.lineno)
        log_record["@timestamp"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        log_record["@version"] = self.version_getter()
        log_record["levelname"] = record.levelname
        log_record["processName"] = record.processName
        log_record["created"] = record.created
        log_record["thread"] = record.thread
        log_record["name"] = record.name
