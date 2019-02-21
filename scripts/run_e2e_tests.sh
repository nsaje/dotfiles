#!/bin/bash

# Run e2e tests with testim CLI

APP_URL=${1:-"e2e_server:8123"}

function exit_ok {
    exit 0
}

function exit_error {
    exit 1
}

trap exit_ok TERM INT

echo "Waiting for app to start"
retval=1
n=0
while true; do
    wget -s "$APP_URL" 2> /dev/null
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
                echo "Waiting for app to start timed out"
                exit_error
            fi
            continue
            ;;
    esac
done
echo "App started"

# TODO (e2e-tests): Launch testim CLI with tunnel setup
# TODO (e2e-tests): Figure out how to create a tunnel/proxy to APP_URL
# testim --tunnel --tunnel-port 8123 --label "<YOUR LABEL>" --token "<YOUR ACCESS TOKEN>" --project "<YOUR PROJECT ID>" --grid "<Your grid name>" --report-file test-results/testim-tests-report.xml
