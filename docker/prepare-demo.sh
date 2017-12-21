#!/bin/bash

if [[ -f /app/zemanta-eins/manage.py ]]; then
	DIR=/app/zemanta-eins
else
	DIR=/app/z1
fi

DB_NAME=$(echo 'from django.conf import settings; print settings.DATABASES["default"]["NAME"]' | $DIR/manage.py shell 2>/dev/null)
if [[ "$DB_NAME" != "demo-one" && "$DB_NAME" != "one-dev" ]]; then
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
python $DIR/manage.py migrate --noinput

echo "Downloading dump"
curl -L "${DUMP_URL}" >> dump.tar

echo "Clearing the DB"
python $DIR/manage.py sqlflush | grep -v "Loading configuration from" | python $DIR/manage.py dbshell

echo "Extracting dump files"
tar -xf dump.tar

echo "Loading dump"
python $DIR/manage.py loaddata dump*.json

echo "Loading geolocations"
python $DIR/manage.py import_geolocations dash/features/geolocation/supported_locations/GeoIP2-City-Locations-en.csv dash/features/geolocation/supported_locations/yahoo-mapping.csv dash/features/geolocation/supported_locations/outbrain-mapping.csv dash/features/geolocation/supported_locations/facebook-mapping.csv

echo "Creating DB cache tables"
python $DIR/manage.py createcachetable

echo "Incrementing sequences"
python $DIR/manage.py dbshell <<SQL | grep 'ALTER SEQUENCE' | python $DIR/manage.py dbshell
SELECT 'ALTER SEQUENCE ' ||
       quote_ident(S.relname) ||
       ' INCREMENT BY 1000000;'
FROM pg_class AS S
WHERE S.relkind = 'S'
SQL
