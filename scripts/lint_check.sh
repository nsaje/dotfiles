#!/bin/bash -x

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
source $DIR/helpers.sh

DIFF=$(docker run --rm \
    -v $PWD:/src \
    --workdir=/src/ \
    --entrypoint=sh \
    py3-tools -c "pip-compile server/requirements.in --dry-run --no-annotate --no-header 2>&1" | grep -v "^#" | grep -v "^Dry-run" | diff <(grep -v "^#" server/requirements.txt) -)
if [ "$DIFF" != "" ]; then
    echo "$DIFF"
    report_check_result 1 "requirements.in"
fi


# Isort ------------------------------------------------------------------------
# blue "Isort lint in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=isort py3-tools --check-only -sp /src/setup.cfg\

EXITCODE=$?
report_check_result $EXITCODE "Isort"

# Black ------------------------------------------------------------------------
blue "Black lint in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=black py3-tools --fast --check ./server/

EXITCODE=$?
report_check_result $EXITCODE "Black"

# Flake8 -----------------------------------------------------------------------
blue "Flake8 lint in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=flake8 py3-tools ./server/

EXITCODE=$?
report_check_result $EXITCODE "Flake8"

# Xenon -------------------------------------------------------------------------
blue "Xenon (cyclomatic complexity) check in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=xenon py3-tools  \
  --max-absolute D \
  -e "server/dash/table.py,server/dash/models.py,server/dash/views/views.py,server/dash/dashapi/api_breakdowns.py,server/core/models/settings/ad_group_settings.py,server/core/models/settings/ad_group_settings/model.py,server/dash/management/commands/consolidate_rtap_fields.py" \
  ./server/

EXITCODE=$?
report_check_result $EXITCODE "Xenon"

# mypy --------------------------------------------------------------------------
blue "mypy check in progress ..."
docker run --rm -v $PWD:/src --workdir=/src/server/ --entrypoint=sh py3-tools \
           -c 'mypy $(find . -name "*.py" | xargs grep typing | cut -d ":" -f1 | sort | uniq)'
EXITCODE=$?
report_check_result $EXITCODE "mypy"
