SCRIPTPATH='.'
SERVER_PORT=9993
STATIC_PORT=9999

export E2E=1

STATUS=1
echo 'Loading fixtures' &&
$SCRIPTPATH/server/manage.py syncdb --noinput &&
$SCRIPTPATH/server/manage.py migrate --noinput &&
$SCRIPTPATH/server/manage.py loaddata demo_groups &&
$SCRIPTPATH/server/manage.py loaddata demo_data

echo 'Running server' &&
$SCRIPTPATH/server/manage.py runserver localhost:$SERVER_PORT &

CURR_DIR=$PWD
cd $SCRIPTPATH/client

grunt dev
# wait until we have the port open
while ! fuser $STATIC_PORT/tcp 2>/dev/null 1>/dev/null; do sleep 1; done

grunt e2e
STATUS=$?
cd $CURR_DIR

echo "Killing server"
fuser -k $SERVER_PORT/tcp 1> /dev/null || lsof -P | grep ":$SERVER_PORT" | awk '{print $2}' | xargs kill;
fuser -k $STATIC_PORT/tcp 1> /dev/null || lsof -P | grep ":$STATIC_PORT" | awk '{print $2}' | xargs kill;
exit $STATUS
