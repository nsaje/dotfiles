#!/bin/bash -x

# Fail hard and fast
set -eo pipefail

msg() {
        echo -e "[zemanta-z1] $@"
}

cd /app/z1

if [ "$MULTIPROC_PROMETHEUS" == true ]; then
    export prometheus_multiproc_dir=$(mktemp -d -t prometheus-XXXXXXXX)
fi

if [ -z "$NEW_RELIC_LICENSE_KEY" ]; then
    msg "starting app in $PWD"
    exec $@
else
    msg "starting app with NewRelic in $PWD"
    exec /usr/local/bin/newrelic-admin run-program $@
fi
