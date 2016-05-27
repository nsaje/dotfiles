#!/bin/bash

echo "Wait for PostgreSQL"
sleep 5
retval=0
while [[ "$retval" != "52" ]]; do
    curl -q http://${DB_PORT_5432_TCP_ADDR}:${DB_PORT_5432_TCP_PORT}/ 2> /dev/null
    retval=$?
    echo -n "."
    sleep 1
done
echo "PostgreSQL opened port"

# Fail hard and fast
set -eo pipefail

echo "Running migrations"
python /app/zemanta-eins/manage.py migrate --noinput

echo "Downloading dump"
curl -L "${DUMP_URL}" >> dump.json

echo "Loading dump"
python /app/zemanta-eins/manage.py loaddata dump.json

