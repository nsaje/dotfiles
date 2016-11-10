#!/bin/bash

# Run REST API acceptance tests
#
# Runs run-test-server.py to get a clean acceptance test server,
# then runs dredd against that server.

DIR="$(dirname $(readlink -f $0))"

SERVER_CMD="python $DIR/restapi-test-server.py"
SERVER_ENDPOINT="localhost:8123"
SERVER_LOG="$DIR/acceptance_test_server.log"
DREDD_CMD="dredd"

BLUEPRINT="$DIR/restapi/api_blueprint.md"
HOOKFILES="$DIR/restapi/acceptance_tests/hooks.py"

function kill_server {
    kill -TERM $SERVER_PID
}

function exit_ok {
    kill_server
    exit 0
}

function exit_error {
    kill_server
    exit 1
}

# check if dredd is installed
command -v $DREDD_CMD >/dev/null 2>&1 || { echo "Please install dredd with 'npm install -g dredd'.  Aborting."; exit 1; }

# clean up server when we exit
trap exit_ok TERM INT

# start server
$SERVER_CMD $SERVER_ENDPOINT &> "$SERVER_LOG" &
SERVER_PID=$!

echo "Waiting for server"
retval=1
n=0
while true; do
    curl -q "$SERVER_ENDPOINT" 2> /dev/null
    retval=$?
    case "$retval" in
        0)  # connection successful
            break
            ;;
        7)  # could not connect
            sleep 1
            ((n++))
            if [[ $n -ge 120 ]]; then
                echo "Waiting for server timed out"
                exit_error
            fi
            continue
            ;;
        *)
            echo "Something is wrong, curl returned $retval"
            exit_error
            ;;
    esac
done
echo "Server opened port"

$DREDD_CMD $BLUEPRINT http://$SERVER_ENDPOINT --language python --hookfiles=$HOOKFILES
exit_ok
