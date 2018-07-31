#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
ROOT="$( dirname $DIR )"
if [[ $(basename $0) = "pre-commit" ]]; then
    # we're run from git hook, adjust root
    ROOT="$( dirname $ROOT )"
fi

source $ROOT/scripts/helpers.sh

cd "$ROOT"

function run_on_staged_files {
	FILTER=$1
	CMD=$2
	git diff --diff-filter=d --cached --name-only -z -- $FILTER \
		| xargs -0 -I % sh -c "$CMD"
}

# Black
run_on_staged_files '*.py' 'docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=black py3-tools -l 120 --fast "%" ; git add %'
report_check_result 0 "Black"

# Flake8
run_on_staged_files '*.py' 'docker run --rm -v $PWD:/src --workdir=/src/ --entrypoint=flake8 py3-tools "%"'
EXITCODE=$?
report_check_result $EXITCODE "Flake8"

# ESLint
run_on_staged_files '*.js' 'docker run --rm -v "/src/client/node_modules" -v $PWD/client/.eslintrc.yml:/root/.eslintrc.yml -v $PWD:/src --workdir=/src/ --entrypoint=eslint client-lint --format codeframe "%";'

EXITCODE=$?
report_check_result $EXITCODE "ESLint"

# TSLint
# FIXME(nsaje&jurebajt)
run_on_staged_files '*.ts' 'docker run --rm -v "/src/client/node_modules" -v $PWD:/src --workdir=/src/ --entrypoint=tslint client-lint --project client/tsconfig.json --format codeFrame "%";'

EXITCODE=$?
report_check_result $EXITCODE "TSLint"
