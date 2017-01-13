#!/bin/bash -x

# Fail hard and fast
set -eo pipefail

function red {
  echo -e "\e[31m$1\e[0m"
}

function blue {
  echo -e "\e[34m$1\e[0m"
}

function green {
  echo -e "\e[32m$1\e[0m"
}

# PEP 8 ------------------------------------------------------------------------

blue "PEP8 lint in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=pep8 py-tools \
  --first \
  --exclude="__init__.py,test_api.py,settings.py,wsgi.py,migrations,localsettings.py,regions.py" \
  --max-line-length=700 \
  ./server/

EXITCODE=$?
if [[ $EXITCODE != 0 ]]; then
    red "+-------------------------+"
    red "|    PEP8 CHECK FAILED    |"
    red "+-------------------------+"
    exit 1
fi
green "PEP8 check successful"

# ES Lint ----------------------------------------------------------------------

# blue "ESLint in progress ..."
# eslint client/one client/test

# EXITCODE=$?
# if [[ $EXITCODE != 0 ]]; then
#     red "+---------------------------+"
#     red "|    ESLINT CHECK FAILED    |"
#     red "+---------------------------+"
#     exit 1
# fi
# green "ESLint check successful"

# Xenon ------------------------------------------------------------------------

blue "Xenon (cyclomatic complexity) check in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=xenon py-tools  \
  --max-absolute D \
  -e "server/dash/table.py,server/dash/models.py,server/dash/views/views.py,server/dash/dashapi/api_breakdowns.py" \
  ./server/

EXITCODE=$?
if [[ $EXITCODE != 0 ]]; then
    red "+---------------------------+"
    red "|    XENON CHECK FAILED     |"
    red "+---------------------------+"
    exit 1
fi
green "Xenon check successful"
