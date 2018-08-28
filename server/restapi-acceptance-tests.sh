#!/bin/bash

# Run REST API acceptance tests

DIR="$(dirname $(readlink -f $0))"

SERVER_ENDPOINT=${1:-"einsacceptance:8123"}
BLUEPRINT="$DIR/restapi/docs/api_blueprint.md"
HOOKFILES="$DIR/restapi/acceptance_tests/hooks.py"

DREDD_CMD="dredd"

function exit_ok {
    exit 0
}

function exit_error {
    exit 1
}

trap exit_ok TERM INT

echo "Waiting for server"
retval=1
n=0
while true; do
    wget -s "$SERVER_ENDPOINT" 2> /dev/null
    retval=$?
    case "$retval" in
        0)  # connection successful
            break
            ;;
        *)  # could not connect
            sleep 1
	    echo -n "."
            ((n++))
            if [[ $n -ge 360 ]]; then
                echo "Waiting for server timed out"
                exit_error
            fi
            continue
            ;;
        #*)
            #echo "Something is wrong, curl returned $retval"
            #exit_error
            #;;
    esac
done
echo "Server opened port"

$DREDD_CMD $BLUEPRINT http://$SERVER_ENDPOINT --language python --hookfiles=$HOOKFILES --reporter junit --output .junit_acceptance.xml --hooks-worker-connect-timeout 5000
