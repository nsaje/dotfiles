To update fixtures run : 
PGPASSWORD=$POSTGRES_PASSWORD pg_dump --no-owner -U $POSTGRES_USER -d "$POSTGRES_DB"  > /docker-entrypoint-initdb.d/00_initial.sql

