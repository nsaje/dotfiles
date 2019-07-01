import os
import threading
import wsgiref.simple_server

import celery.signals

from . import wsgi

__all__ = ["outbrain_celery_setup"]


def outbrain_celery_setup():
    celery.signals.worker_init.connect(handle_worker_init)
    celery.signals.worker_process_init.connect(handle_worker_process_init)


def handle_worker_init(**kwargs):
    if kwargs["sender"].pool_cls in ("gevent", "solo"):
        start_outbrain_wsgi_server()


def handle_worker_process_init(**kwargs):
    start_outbrain_wsgi_server()


def start_outbrain_wsgi_server():
    app = wsgi.OutbrainWSGI()
    port = int(os.environ.get("CELERY_SERVER_PORT", "8000"))
    httpd = wsgiref.simple_server.make_server("", port, app)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
