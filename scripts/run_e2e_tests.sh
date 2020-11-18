#!/bin/bash

# Run e2e tests

SERVER_INTERNAL_HOSTNAME=${SERVER_INTERNAL_HOSTNAME:-"server"}
SERVER_PORT=${SERVER_PORT:-"8123"}
SERVER_INTERNAL_ENDPOINT="${SERVER_INTERNAL_HOSTNAME}:${SERVER_PORT}"
SERVER_EXTERNAL_ENDPOINT="${SERVER_EXTERNAL_HOSTNAME}:${SERVER_PORT}"

TESTIM_PROJECT="95qRp4zvX0ycrDY1MHRI"
TESTIM_TEST_PLAN="Z1 Dashboard E2E"
OWNER_TEAM="z1" # owner in dyploma

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
    wget -S "$SERVER_INTERNAL_ENDPOINT" 2> /dev/null
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
    esac
done
echo "Server opened port"

# https://confluence.outbrain.com/display/WG/Jenkins+integration
curl -s https://bitbucket.outbrain.com/projects/FEG/repos/e2e-scripts/raw/run-testim-kubernetes-grid.sh |
    TESTIM_TOKEN="$TESTIM_TOKEN" \
    TESTIM_PROJECT="$TESTIM_PROJECT" \
    TESTIM_TEST_PLAN="$TESTIM_TEST_PLAN" \
    TESTIM_BASE_URL="http://$SERVER_EXTERNAL_ENDPOINT" \
    OWNER_TEAM="$OWNER_TEAM" \
    TESTIM_RETRIES=3 \
    PARALLEL_TESTS=4 \
    bash
