#!/bin/bash

DIR="$(dirname $(readlink -f $0))"
NOTIFICATION_LIMIT="10"
SUSPEND_LIMIT="5"

while true
do
	CAPACITY=`grep "POWER_SUPPLY_CAPACITY=" "$DIR/.uevent" | cut -d= -f2`
	STATUS=`grep "POWER_SUPPLY_STATUS=" "$DIR/.uevent" | cut -d= -f2`
	if [[ $(echo "$CAPACITY < $NOTIFICATION_LIMIT" | bc) -eq 1 && "$STATUS" == "0" ]]; then
		/usr/bin/i3-nagbar -m "Battery low, plug in!" &
	fi
	if [[ $(echo "$CAPACITY < $SUSPEND_LIMIT" | bc) -eq 1  && "$STATUS" == "0" ]]; then
		/usr/bin/i3-nagbar -m "Battery low, suspending!" &
		systemctl suspend
	fi
	sleep 60
done
