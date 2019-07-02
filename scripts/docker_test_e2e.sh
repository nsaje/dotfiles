#!/bin/bash

set -e

clean_up () {
	ARG=$?
	docker-compose -f docker-compose.yml -f docker-compose.e2e-runner.yml stop;
	exit $ARG
}
trap clean_up EXIT

if [ -z "${Z1_SERVER_IMAGE}" ]; then
	export Z1_SERVER_IMAGE="569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta/z1:current"
fi

export COMPOSE_PROJECT_NAME=e2e-runner-`basename $(pwd)`;
echo "Compose project name: ${COMPOSE_PROJECT_NAME}"
echo "E2E image: ${Z1_SERVER_IMAGE}"
docker-compose -f docker-compose.yml -f docker-compose.e2e-runner.yml up --force-recreate -d
docker-compose -f docker-compose.yml -f docker-compose.e2e-runner.yml run --rm testim-runner ./run_e2e_tests.sh
clean_up
