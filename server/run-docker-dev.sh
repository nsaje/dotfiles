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
# Check if all requirements are installed

if [[ "$(cat requirements.txt|md5sum)" != "$(cat /requirements.txt-installed|md5sum)" ]]; then
    echo "IMPORTANT: Requirements change detected. I will install it but please update your image to reduce initialization time";
    pip install -U -r requirements.txt
else
    echo "Requirements are up-to-date"

python manage.py migrate

python manage.py runserver 0.0.0.0:8000

