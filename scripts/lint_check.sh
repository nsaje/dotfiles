#!/bin/bash -x

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
source $DIR/helpers.sh

DIFF=$(docker run --rm \
    -v $PWD:/src \
    --workdir=/src/ \
    --entrypoint=sh \
    py3-tools -c "pip-compile server/requirements.in --no-annotate" | diff server/requirements.txt -)
if [ "$DIFF" != "" ]; then
    echo "$DIFF"
    report_check_result 1 "requirements.in"
fi

# Black ------------------------------------------------------------------------
blue "Black lint in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=black py3-tools -l 120 --exclude="build/|buck-out/|dist/|_build/|\.git/|\.hg/|\.mypy_cache/|\.tox/|\.venv/|.*\/migrations\/.*" --fast --check ./server/

EXITCODE=$?
report_check_result $EXITCODE "Black"

# Flake8 ------------------------------------------------------------------------
blue "Flake8 lint in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=flake8 py3-tools ./server/

EXITCODE=$?
report_check_result $EXITCODE "Flake8"


# Client Lint ----------------------------------------------------------------------
blue "ClientLint in progress ..."

docker run --rm \
           -v "/src/client/node_modules" \
           -v $PWD/.eslintrc.yml:/root/.eslintrc.yml \
           -v $PWD/client:/src \
           --entrypoint=sh \
           client-lint -c "rm -f /package.json ; npm run lint"

EXITCODE=$?
report_check_result $EXITCODE "ClientLint"


# Xenon ----------------------------------------------------------------------------
blue "Xenon (cyclomatic complexity) check in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=xenon py3-tools  \
  --max-absolute D \
  -e "server/dash/table.py,server/dash/models.py,server/dash/views/views.py,server/dash/dashapi/api_breakdowns.py,server/core/entity/settings/ad_group_settings.py,server/core/entity/settings/ad_group_settings/model.py" \
  ./server/

EXITCODE=$?
report_check_result $EXITCODE "Xenon"


# mypy -----------------------------------------------------------------------------
blue "mypy check in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/server/ --entrypoint=sh py3-tools \
           -c 'mypy $(find . -name "*.py" | xargs grep typing | cut -d ":" -f1 | sort | uniq)'
EXITCODE=$?
report_check_result $EXITCODE "mypy"

