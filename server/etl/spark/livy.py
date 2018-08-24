import json
from os import path
import requests

from django.conf import settings

FILE_PREFIX = "etl/spark/code"
LIVY_URL = "http://{}:8998"


def get_session():
    return LivySession(
        LIVY_URL.format(settings.SPARK_MASTER),
        driverMemory="1g",
        # executor memory has to be of size that assures even distribution of workers between nodes
        # for example with 16G nodes and 2g for executors, some nodes might get 5 workers and some 3
        # instead of 4x8=32, so we need to set a bit more moemory
        executorMemory="2150m",
        driverCores=1,
        executorCores=1,
        conf={
            "spark.default.parallelism": 32,  # number of tasks on input
            "spark.sql.shuffle.partitions": 32,  # number of tasks after join or group
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

        data = {"kind": "pyspark"}
        data.update(self.params)

        result = requests.post(self.url + "/sessions", data=json.dumps(data)).json()
        while result["state"] == "starting":
            result = requests.get(self.url + "/sessions/" + str(result["id"])).json()

        if result["state"] != "idle":
            raise Exception("Invalid session state: " + result["state"])

        self.state = result["id"]

    def close(self):
        if self.state is None:
            return
        requests.delete(self.url + "/sessions/" + str(self.state))
        self.state = None

    def run(self, code):
        if self.state is None:
            raise Exception("Session not started")

        data = {"code": code}

        result = requests.post(self.url + "/sessions/" + str(self.state) + "/statements", data=json.dumps(data)).json()
        while result["state"] in ("waiting", "running"):
            result = requests.get(self.url + "/sessions/" + str(self.state) + "/statements/" + str(result["id"])).json()

        if result["state"] != "available":
            raise Exception("Invalid statement state: " + result["state"])

        if result["output"]["status"] == "error":
            raise Exception(result["output"])

    def run_file(self, filename, *args, **kwargs):
        with open(path.join(FILE_PREFIX, filename), "r") as f:
            code = f.read()

        code = code.format(*args, **kwargs)

        self.run(code)
