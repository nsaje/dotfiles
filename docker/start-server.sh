#!/bin/bash

source /init.sh

GUNICORN_TO=${GUNICORN_TIMEOUT:-60}
GUNICORN_WC=${GUNICORN_WORKERS:-4}

msg "booting container. ETCD: $ETCD"
cd /app/zemanta-eins
python manage.py collectstatic --noinput
msg "starting app in $PWD"
gunicorn --timeout $GUNICORN_TO --worker-class=gevent --workers=$GUNICORN_WC --log-level=warn --bind 0.0.0.0:8000 server.wsgi:application
