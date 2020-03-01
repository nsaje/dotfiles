#!/bin/bash
trace -x

DIR="$(dirname $(readlink -f $0))"
UEVENT_PATH="/sys/class/power_supply/BAT0/uevent"
NOTIFICATION_LIMIT="10"
SUSPEND_LIMIT="5"

while true
do
	CAPACITY=`grep "POWER_SUPPLY_CAPACITY=" "$UEVENT_PATH" | cut -d= -f2`
	STATUS=`grep "POWER_SUPPLY_STATUS=" "$UEVENT_PATH" | cut -d= -f2`
	if [[ $(echo "$CAPACITY < $NOTIFICATION_LIMIT" | bc) -eq 1 && "$STATUS" == "Discharging" ]]; then
		flock --nonblock /tmp/lowbattery-msg-lock --command "i3-nagbar -m 'Battery low, plug in!'" &
	fi
	if [[ $(echo "$CAPACITY < $SUSPEND_LIMIT" | bc) -eq 1  && "$STATUS" == "Discharging" ]]; then
		systemctl suspend
	fi
	sleep 60
done
