#!/bin/bash

# Fail hard and fast
set -eo pipefail

msg() {
	echo "[zemanta-eins] $@"
}

msg "fetching build artifact from given URL"

DEST=/app/zemanta-eins
mkdir -p $DEST/
cd $DEST/ && \
curl -H "Authorization: token ${PACKAGE_TOKEN}" \
     -L "${PACKAGE_URL}" | tar -xz -C $DEST/

if [ "$?" != "0" ]; then
        echo "[ERROR] Unable to download application. Check your GitHub.com credentials"
        exit -1
else
        echo "[INFO] App download successfull"
fi



msg "Configuration stage"
# Either provide local file or CONF_URL+CONF_SECRET
cd $DEST
# you must pass  -v path_to_localsettings:/localsettings.py  setting to docker for this to work
if [ -f /localsettings.py ]; then
    cp /localsettings.py server/localsettings.py
else
    curl "${CONF_URL}" \
    | openssl enc -d -base64 -aes-256-ecb -k "$(printf $CONF_SECRET)" > server/localsettings.py
fi

# Check if all requirements are installed
if [[ "$(cat requirements.txt|md5sum)" != "$(cat /requirements.txt-installed|md5sum)" ]]; then
    msg "IMPORTANT: Requirements change detected. I will install it but please update your image to reduce initialization time";
    pip install -U -r requirements.txt
else
    msg "Requirements are up-to-date"
fi
