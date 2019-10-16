import json
import time

import requests

import demo
import structlog
from utils import metrics_compat
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)

NUM_RETRIES = 10


class Command(Z1Command):
    def handle(self, *args, **options):
        demo = self._start_demo()
        try:
            self._check_demo_url(demo)
        except Exception as err:
            metrics_compat.incr("demo.monitor", 1, status="error")
            raise (err)
        finally:
            self._stop_demo(demo["name"])
        metrics_compat.incr("demo.monitor", 1, status="ok")

    def _start_demo(self):
        instance_name, url, password = demo.request_demo()

        return {"name": instance_name, "url": url, "username": "regular.user+demo@zemanta.com", "password": password}

    def _find_string_in_login_page(self, session, demo_instance):
        response = session.get(demo_instance["url"])
        body = response.text
        if "Zemanta One" not in body or "Sign in" not in body:
            raise Exception("Invalid response from demo({instance_name})".format(instance_name=demo_instance["name"]))

    def _try_to_login(self, session, demo_instance):
        response = session.post(
            url="%s/signin" % demo_instance["url"],
            data={
                "username": demo_instance["username"],
                "password": demo_instance["password"],
                "csrfmiddlewaretoken": session.cookies["csrftoken"],
            },
            headers={"Referer": "%s/signin?next=/" % demo_instance["url"]},
        )
        if response.status_code != 200:
            raise Exception(
                "Invalid response code from demo signin({instance_name})".format(instance_name=demo_instance["name"])
            )

    def _fetch_all_accounts_nav(self, session, demo_instance):
        response = session.get(
            url="%s/api/all_accounts/nav/" % demo_instance["url"], headers={"Accept": "application/json"}
        )
        if response.status_code != 200:
            raise Exception(
                "Invalid response code from demo nav({instance_name})".format(instance_name=demo_instance["name"])
            )
        data = json.loads(response.text)
        if not data.get("success", False):
            raise Exception("Could not get basic nav data({instance_name})".format(instance_name=demo_instance["name"]))

        return session

    def _check_demo_url(self, demo_instance):
        error = Exception(
            "Automatic 'Request demoV3' check failed for unknown reason({instance_name}).".format(
                instance_name=demo_instance["name"]
            )
        )
        for _ in range(NUM_RETRIES):
            try:
                session = requests.Session()
                self._find_string_in_login_page(session, demo_instance)
                self._try_to_login(session, demo_instance)
                self._fetch_all_accounts_nav(session, demo_instance)
                return

            except Exception as err:
                error = err
                time.sleep(5)
        raise error

    def _stop_demo(self, name):
        demo.terminate_demo(name)
