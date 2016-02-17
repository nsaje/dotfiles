#!/bin/bash

LIVE_SESSIONS_COUNT=$(w -h | wc -l)
if [[ $LIVE_SESSIONS_COUNT > 1 ]]; then
        echo "there are still live sessions [" $((LIVE_SESSIONS_COUNT - 1)) "] - postponing termination"
else
        echo "terminating container"
        for pid_file in /var/run/dropbear.pid /var/run/sshd.pid; do
            test -f $pid_file &&  kill -9 $(cat $pid_file)
        done
fi

