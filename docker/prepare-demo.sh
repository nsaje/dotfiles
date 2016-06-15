#!/bin/bash

if [[ "$CONF_ENV" != "demo" || "${DB_ENV_POSTGRES_DB}" != "demo-one" ]]; then
    echo "ERROR: Running prepare-demo in non-demo environment, which would drop the DB! Exiting."
    exit 1
fi

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

echo "Clearing the DB"
python /app/zemanta-eins/manage.py sqlflush | python /app/zemanta-eins/manage.py dbshell

echo "Loading dump"
python /app/zemanta-eins/manage.py loaddata dump.json

echo "Incrementing sequences"
python /app/zemanta-eins/manage.py dbshell <<SQL | grep 'ALTER SEQUENCE' | python /app/zemanta-eins/manage.py dbshell
SELECT 'ALTER SEQUENCE ' ||
       quote_ident(S.relname) ||
       ' INCREMENT BY 1000000;'
FROM pg_class AS S
WHERE S.relkind = 'S'
SQL
