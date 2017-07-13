#!/bin/bash

msg() {
        echo -e "[zemanta-z1] $@"
}

GUNICORN_TO=${GUNICORN_TIMEOUT:-60}
GUNICORN_WC=${GUNICORN_WORKERS:-4}
GUNICORN_THREADS=${GUNICORN_THREADS:-1}
GUNICORN_WORKER_CLASS=${GUNICORN_WORKER_CLASS:-gevent}
GUNICORN_LOG_LEVEL=${GUNICORN_LOG_LEVEL:-info}
GUNICORN_BACKLOG=${GUNICORN_BACKLOG:-2048}
GUNICORN_ACCESS_LOGFORMAT={$GUNICORN_ACCESS_LOGFORMAT:-"%(h)s %(l)s %(u)s %(t)s \"%(r)s\" elb=%({X-Amzn-Trace-Id}i)s traefik=%({X-Traefik-Reqid}i)s %(s)s %(b)s \"%(f)s\" \"%(a)s\""}

msg "booting container. ETCD: $ETCD"
python manage.py collectstatic --noinput
if [ -z "$NEW_RELIC_LICENSE_KEY" ]; then
    msg "starting app in $PWD"
    gunicorn --timeout $GUNICORN_TO --workers=$GUNICORN_WC --threads=$GUNICORN_THREADS --worker-class=$GUNICORN_WORKER_CLASS --log-level=$GUNICORN_LOG_LEVEL --backlog=$GUNICORN_BACKLOG --access-logfile=- --access-logformat=$GUNICORN_ACCESS_LOGFORMAT --bind 0.0.0.0:8000 server.wsgi:application
else
    msg "starting app with NewRelic in $PWD"
    /usr/local/bin/newrelic-admin run-program /usr/local/bin/gunicorn --timeout $GUNICORN_TO --workers=$GUNICORN_WC --threads=$GUNICORN_THREADS --worker-class=$GUNICORN_WORKER_CLASS  --log-level=$GUNICORN_LOG_LEVEL --backlog=$GUNICORN_BACKLOG --access-logfile=- --access-logformat=$GUNICORN_ACCESS_LOGFORMAT --bind 0.0.0.0:8000 server.wsgi:application
fi
