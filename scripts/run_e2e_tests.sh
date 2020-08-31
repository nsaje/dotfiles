#!/bin/bash

# Run e2e tests with testim CLI

SERVER_ENDPOINT=${1:-"server:8123"}

TESTIM_PROJECT="95qRp4zvX0ycrDY1MHRI"
GRID_HOST="zalenium"
GRID_PORT="4444"

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
    wget -S "$SERVER_ENDPOINT" 2> /dev/null
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

# Launch testim CLI for Chrome
testim \
    --name "Automations Rules (Account Manager)" \
    --name "Automations Rules (Agency Manager)" \
    --name "Automations Rules (Internal User)" \
    --name "Create account" \
    --name "Create ad group" \
    --name "Create campaign" \
    --name "Create credit" \
    --name "Credits Library (Account Manager)" \
    --name "Credits Library (Agency Manager / Clear account)" \
    --name "Credits Library (Agency Manager)" \
    --name "Deals Library (Account Manager)" \
    --name "Deals Library (Agency Manager)" \
    --name "Deals Library (Internal User)" \
    --name "Deals Library (Read Only)" \
    --name "Login/Logout" \
    --name "Publisher groups (Account manager)" \
    --name "Publisher groups (Agency manager)" \
    --name "Publisher groups (Internal user)" \
    --name "Publisher groups (Readonly)" \
    --name "User management (Account Manager)" \
    --name "User management (Agency manager)" \
    --name "User management (Internal user)" \
    --token "$TESTIM_TOKEN" \
    --project "$TESTIM_PROJECT" \
    --host "$GRID_HOST" \
    --port "$GRID_PORT" \
    --base-url "http://$SERVER_ENDPOINT" \
    --parallel 2 \
    --test-config "Chrome" \
    --test-config "Firefox" --mode selenium \
    --report-file testim-tests-report.xml
