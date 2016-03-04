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

if [ ! -f "$DEST/manage.py" ] ; then
    if [ -z "${PACKAGE_TOKEN}" ]; then
        curl -L "${PACKAGE_URL}" | tar -xz -C $DEST/
    else
        curl -H "Authorization: token ${PACKAGE_TOKEN}" \
             -L "${PACKAGE_URL}" | tar -xz -C $DEST/
    fi

    if [ "$?" != "0" ]; then
            echo "[ERROR] Unable to download application. Check your GitHub.com credentials"
            exit -1
    else
            echo "[INFO] App download successfull"
    fi
fi


msg "Configuration stage"
# Either provide local file or CONF, which will copy localsettings.py.${CONF} to localsettings.py
cd $DEST
# you must pass  -v path_to_localsettings:/localsettings.py  setting to docker for this to work
if [ -f /localsettings.py ]; then
    cp /localsettings.py server/localsettings.py
else
    cp server/localsettings.py.${CONF_ENV} server/localsettings.py
fi

# Check if all requirements are installed
if [[ "$(cat requirements.txt|md5sum)" != "$(cat /requirements.txt-installed|md5sum)" ]]; then
    msg "IMPORTANT: Requirements change detected. I will install it but please update your image to reduce initialization time";
    pip install -U -r requirements.txt
else
    msg "Requirements are up-to-date"
fi
