#!/bin/bash

msg() {
        echo -e "[zemanta-z1] $@"
}

GUNICORN_TO=${GUNICORN_TIMEOUT:-60}
GUNICORN_WC=${GUNICORN_WORKERS:-4}
GUNICORN_WORKER_CLASS=${GUNICORN_WORKER_CLASS:-gevent}
GUNICORN_LOG_LEVEL=${GUNICORN_LOG_LEVEL:-info}

msg "booting container. ETCD: $ETCD"
python manage.py collectstatic --noinput
if [ -z "$NEW_RELIC_LICENSE_KEY" ]; then
    msg "starting app in $PWD"
    gunicorn --timeout $GUNICORN_TO --workers=$GUNICORN_WC --worker-class=$GUNICORN_WORKER_CLASS --log-level=$GUNICORN_LOG_LEVEL --bind 0.0.0.0:8000 server.wsgi:application
else
    msg "starting app with NewRelic in $PWD"
    /usr/local/bin/newrelic-admin run-program /usr/local/bin/gunicorn --timeout $GUNICORN_TO --workers=$GUNICORN_WC --worker-class=$GUNICORN_WORKER_CLASS  --log-level=$GUNICORN_LOG_LEVEL --bind 0.0.0.0:8000 server.wsgi:application
fi
