#!/bin/bash

set -e

clean_up () {
	ARG=$?
	docker-compose -f docker-compose.yml -f docker-compose.acceptance.yml stop;
	exit $ARG
}
trap clean_up EXIT

if [ -z "${ACCEPTANCE_IMAGE}" ]; then
	export ACCEPTANCE_IMAGE="569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta/z1:current"
fi

export COMPOSE_PROJECT_NAME=acceptance-`basename $(pwd)`;
echo "Compose project name: ${COMPOSE_PROJECT_NAME}"
echo "Acceptance image: ${ACCEPTANCE_IMAGE}"
docker-compose -f docker-compose.yml -f docker-compose.acceptance.yml up --force-recreate -d
docker-compose -f docker-compose.yml -f docker-compose.acceptance.yml run --rm dredd ./restapi-acceptance-tests.sh
clean_up
