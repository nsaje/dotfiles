#!/bin/bash

echo "Wait for PostgreSQL"
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

python manage.py migrate

python manage.py runserver 0.0.0.0:8000

