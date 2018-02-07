#!/bin/bash

TASK=${1:-there_is_no_default}
shift
TASK_PARAMS=$@
if [[ "${TASK}" == "there_is_no_default" ]]; then
    echo "Please define manage.py command as parameter"
    exit -1
fi

CONTAINER_ID=$(docker ps -q -f status=exited -f name="$TASK")
if [[ "$CONTAINER_ID" != "" ]]; then
    echo "[WARN] Deleting leftover container [$TASK]"
    docker rm $CONTAINER_ID
fi

echo "running $0 $TASK $TASK_PARAMS"

exec /usr/bin/docker run --rm -h $(hostname) \
    --name="${TASK}" \
    -e "CONF_ENV=prod" \
    -e "NEW_RELIC_LICENSE_KEY=1dfbd7b07a5cbf7bcc6eb18db5003808a058d16f" \
    -e "NEW_RELIC_APP_NAME=Zemanta One (Cron jobs)" \
    -e "NEW_RELIC_PROCESS_HOST_DISPLAY_NAME=$(hostname)-docker" \
    -e "NEW_RELIC_STARTUP_TIMEOUT=10.0" \
    -e "NEW_RELIC_SHUTDOWN_TIMEOUT=10.0" \
    --network legacynet \
    --label "traefik.enable=false" \
    z1-bundle:current /usr/local/bin/newrelic-admin run-program python manage.py "${TASK}" $TASK_PARAMS 2>&1 | sudo tee -a "/mnt/logs/eins/cron-${TASK}.log" > /dev/null
