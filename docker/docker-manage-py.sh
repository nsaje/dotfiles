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
    -e "ZWEI_CALLBACK_BASE_URL=https://one-cb.zemanta.com" \
    -e "CONF_ENV=prod" \
    --link=memcached \
    --entrypoint=python \
    z1-bundle:current manage.py "${TASK}" $TASK_PARAMS 2>&1 | sudo tee -a "/mnt/logs/eins/cron-${TASK}.log" > /dev/null
