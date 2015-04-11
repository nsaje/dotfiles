from __future__ import absolute_import

from server.celery import app

@app.task
def add(x, y):
    return x + y

add.apply_async((2, 2))
