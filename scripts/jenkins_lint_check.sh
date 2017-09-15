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

function banner {
  EXITCODE=$1
  PROGRAM=$2
  if [[ $EXITCODE != 0 ]]; then
      red "+-------------------------+"
      red "|   ${PROGRAM} CHECK FAILED   |"
      red "+-------------------------+"
      exit 1
  fi
  green "${PROGRAM} check successful"
}

DIFF=$(docker run --rm \
    -v $PWD:/src \
    --workdir=/src/ \
    --entrypoint=sh py-tools "pip-compile server/requirements.in | diff server/requirements.txt -")
if [ "$DIFF" != "" ]; then
    banner 1 "requirements.in"
fi

# Flake8 ------------------------------------------------------------------------
blue "Flake8 lint in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=flake8 py-tools ./server/

EXITCODE=$?
banner $EXITCODE "Flake8"


# Client Lint ----------------------------------------------------------------------
blue "ClientLint in progress ..."

docker run --rm \
           -v $PWD/.eslintrc.yml:/root/.eslintrc.yml \
           -v $PWD/client:/src:ro \
           --entrypoint=sh \
           client-lint -c "rm -f /package.json ; npm run lint"

EXITCODE=$?
banner $EXITCODE "ClientLint"


# Xenon ------------------------------------------------------------------------
blue "Xenon (cyclomatic complexity) check in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=xenon py-tools  \
  --max-absolute D \
  -e "server/dash/table.py,server/dash/models.py,server/dash/views/views.py,server/dash/dashapi/api_breakdowns.py,server/core/entity/settings/ad_group_settings.py,server/core/entity/settings/ad_group_settings/model.py" \
  ./server/

EXITCODE=$?
banner $EXITCODE "Xenon"
