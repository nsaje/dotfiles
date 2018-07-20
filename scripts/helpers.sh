#!/bin/bash -x

function red {
    echo -e "\e[31m$1\e[0m"
}

function blue {
    echo -e "\e[34m$1\e[0m"
}

function green {
    echo -e "\e[32m$1\e[0m"
}

function report_check_result {
    EXITCODE=$1
    PROGRAM=$2
    if [[ $EXITCODE != 0 ]]; then
        red "+------------------------------------+"
        red "|   ${PROGRAM} CHECK FAILED   |"
        red "+------------------------------------+"
        exit 1
    fi
    green "${PROGRAM} check successful"
}
