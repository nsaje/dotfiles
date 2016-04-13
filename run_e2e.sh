SCRIPTPATH='.'
SERVER_PORT=9993
STATIC_PORT=9999

export E2E=1

current_time=$(date "+%Y%m%d%H%M%S")
rand=$(< /dev/urandom tr -dc a-z0-9 | head -c8)
export E2E_REDDB="stats_e2e_${current_time}_${rand}"

STATUS=1
echo 'Loading fixtures' &&
$SCRIPTPATH/server/manage.py migrate --noinput &&
$SCRIPTPATH/server/manage.py redshift_createdb stats stats_e2e &&
$SCRIPTPATH/server/manage.py redshift_migrate &&
$SCRIPTPATH/server/manage.py loaddata demo_groups &&
$SCRIPTPATH/server/manage.py loaddata demo_data

echo 'Running server' &&
$SCRIPTPATH/server/manage.py runserver localhost:$SERVER_PORT &

CURR_DIR=$PWD
cd $SCRIPTPATH/client

# since in CircleCI and in local environment regular "grunt test" is run beforehand, 
# it means everything has been already built and we don't need to run dev (=build+watch)
grunt connect:dev:keepalive & 
# wait until we have the port open
while ! fuser $STATIC_PORT/tcp 2>/dev/null 1>/dev/null; do sleep 1; done

grunt e2e
STATUS=$?
cd $CURR_DIR

echo "Killing server"
fuser -k $SERVER_PORT/tcp 1> /dev/null || lsof -P | grep ":$SERVER_PORT" | awk '{print $2}' | xargs kill;
fuser -k $STATIC_PORT/tcp 1> /dev/null || lsof -P | grep ":$STATIC_PORT" | awk '{print $2}' | xargs kill;

echo "Cleaning up"
$SCRIPTPATH/server/manage.py redshift_dropdb stats stats_e2e --noinput &&

exit $STATUS
