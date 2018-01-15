#!/bin/bash

set -e

DB_HOST=${DB_ENV_POSTGRES_HOST:-postgres}
DB_NAME=${DB_ENV_POSTGRES_DB:-one-dev}
DB_USER=${DB_ENV_POSTGRES_USER:-eins}
DB_PASS=${DB_ENV_POSTGRES_PASSWORD:-devpwd}

until PGPASSWORD="$DB_PASS" psql -w -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -c '\l' -P pager=off; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $@
