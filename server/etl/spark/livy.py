import json
import logging
from os import path
import requests
import time

from django.conf import settings

FILE_PREFIX = "etl/spark/code"
LIVY_URL = "http://{}:8998"
SCALA = "spark"
PYTHON = "pyspark"

logger = logging.getLogger(__name__)


def get_session():
    return LivySession(
        LIVY_URL.format(settings.SPARK_MASTER),
        driverMemory="1g",
        # executor memory has to be of size that assures even distribution of workers between nodes
        # for example with 16G nodes and 2g for executors, some nodes might get 5 workers and some 3
        # instead of 4x8=32, so we need to set a bit more moemory
        executorMemory="4150m",
        driverCores=1,
        executorCores=1,
        conf={
            "spark.default.parallelism": 128,  # number of tasks on input
            "spark.sql.shuffle.partitions": 128,  # number of tasks after join or group
            "spark.sql.broadcastTimeout": 600,
            "spark.sql.autoBroadcastJoinThreshold": -1,
        },
    )


class LivySession:
    def __init__(self, url, **params):
        self.url = url
        self.params = params
        self.state = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def start(self):
        if self.state is not None:
            return

        data = {"kind": PYTHON}
        data.update(self.params)

        result = requests.post(self.url + "/sessions", data=json.dumps(data)).json()
        while result["state"] == "starting":
            time.sleep(1)
            result = requests.get(self.url + "/sessions/" + str(result["id"])).json()

        if result["state"] != "idle":
            raise Exception("Invalid session state: " + result["state"])

        self.state = result["id"]

    def close(self):
        if self.state is None:
            return
        requests.delete(self.url + "/sessions/" + str(self.state))
        self.state = None

    def run(self, code, kind=PYTHON):
        if self.state is None:
            raise Exception("Session not started")

        data = {"code": code, "kind": kind}

        result = requests.post(self.url + "/sessions/" + str(self.state) + "/statements", data=json.dumps(data)).json()
        while result["state"] in ("waiting", "running"):
            time.sleep(1)
            result = requests.get(self.url + "/sessions/" + str(self.state) + "/statements/" + str(result["id"])).json()

        if result["state"] != "available":
            raise Exception("Invalid statement state: " + result["state"])

        if result["output"]["status"] == "error":
            raise Exception(result["output"])

        return result["output"]

    def run_file(self, filename, *args, kind=PYTHON, **kwargs):
        logger.info("Running spark job %s for %s", filename, kwargs.get("table"))
        with open(path.join(FILE_PREFIX, filename), "r") as f:
            code = f.read()

        code = code.format(*args, **kwargs)

        logger.debug("Running spark code:\n%s", code)

        self.run(code, kind=kind)
        logger.info("Done spark job %s for %s", filename, kwargs.get("table"))
