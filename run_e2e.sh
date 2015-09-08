SCRIPTPATH='.'
SERVER_PORT=9993
STATIC_PORT=9999

export E2E=1

current_time=$(date "+%Y%m%d%H%M%S")
rand=$(< /dev/urandom tr -dc a-z-0-9 | head -c8)
export E2E_REDDB="stats_e2e_${current_time}_${rand}"

STATUS=1
echo 'Loading fixtures' &&
$SCRIPTPATH/server/manage.py syncdb --noinput &&
$SCRIPTPATH/server/manage.py migrate --noinput &&
$SCRIPTPATH/server/manage.py redshift_create_e2e_db &&
$SCRIPTPATH/server/manage.py loaddata demo_groups &&
$SCRIPTPATH/server/manage.py loaddata demo_data

echo 'Running server' &&
$SCRIPTPATH/server/manage.py runserver localhost:$SERVER_PORT &

CURR_DIR=$PWD
cd $SCRIPTPATH/client
grunt dev&

sleep 40

grunt e2e
STATUS=$?
cd $CURR_DIR

echo "Killing server"
fuser -k $SERVER_PORT/tcp 1> /dev/null || lsof -P | grep ":$SERVER_PORT" | awk '{print $2}' | xargs kill;
fuser -k $STATIC_PORT/tcp 1> /dev/null || lsof -P | grep ":$STATIC_PORT" | awk '{print $2}' | xargs kill;

echo "Cleaning up"
$SCRIPTPATH/server/manage.py redshift_cleanup_e2e_db &&

exit $STATUS
