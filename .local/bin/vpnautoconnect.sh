#!/bin/bash -x

CONN_REGEX="OutbrainWiFi"
VPN_NAME="nsaje - Outbrain VPN"

while true; do
	CONN_ACTIVE=$(nmcli connection show --active | grep "$CONN_REGEX")
	VPN_ACTIVE=$(nmcli connection show --active | grep "$VPN_NAME")

	if [[ ! -z "$CONN_ACTIVE" ]] && [[ -z "$VPN_ACTIVE" ]]; then
		echo "Trying to connect to VPN..."
		nmcli connection up "$VPN_NAME"
	fi

	sleep 10
done
