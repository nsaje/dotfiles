# this is private Docker registry URL hosted on AWS
ECR_BASE = 569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta
GIT_HASH := $(shell git rev-parse --verify HEAD)
TIMESTAMP := $(shell date +"Created_%Y-%m-%d_%H.%M")

ifdef HUDSON_COOKIE # Jenkins
	GIT_BRANCH:= $(shell echo  ${BRANCH_NAME}) # Jenkins
	BUILD_NUM:= $(shell echo -n ${BUILD_NUMBER}) # Jenkins
else # CircleCI
	GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
	BUILD_NUM  := $(shell test -n "${CIRCLE_BUILD_NUM}" && echo -n "${CIRCLE_BUILD_NUM}" || echo -n "00000" )
endif

run:	## runs whole stack with docker-compose
	CONF_ENV=docker	docker-compose up --force-recreate -d

run_devenv:     ## run only development environment (i.e. services that are needed by z1).
	CONF_ENV=docker	docker-compose -f docker-compose.yml -f docker-compose.devenv.yml up --force-recreate -d

stop:	## stops the whole stack
	docker-compose stop

kill:	## kills the whole stack
	docker-compose kill

remove: ## removes all containers belonging to the stack
	docker-compose rm

test:	## runs tests inside container environment
	docker-compose run --rm --entrypoint=/entrypoint_dev.sh eins bash -x ./run_tests.sh
jenkins_test:
	mkdir -p server/.junit_xml/
	docker-compose -f docker-compose.yml -f docker-compose.jenkins.yml run --entrypoint=/entrypoint_dev.sh eins bash -x ./run_tests.sh

test_acceptance:	## runs tests against a running server in a container
	bash -c 'PWD=`pwd` export COMPOSE_PROJECT_NAME=acceptance-`basename ${PWD}`; \
	echo "compose project name ${COMPOSE_PROJECT_NAME}"; \
	docker-compose -f docker-compose.yml -f docker-compose.acceptance.yml up --force-recreate -d; \
	docker-compose -f docker-compose.yml -f docker-compose.acceptance.yml run --rm dredd ./restapi-acceptance-tests.sh; \
	docker-compose -f docker-compose.yml -f docker-compose.acceptance.yml stop;'

####################
# image management #
####################
login:	## login to ECR
ifdef ${LOGGED_IN}
	@echo "Already logged in"
else
	$$(aws ecr get-login)
	$(eval LOGGED_IN=yes)
endif


build_baseimage:	## rebuilds a zemanta/z1-base docker image
	docker pull python:2.7-slim
	docker build 	-t $(ECR_BASE)/z1-base:$(GIT_HASH) \
					-t $(ECR_BASE)/z1-base:$(GIT_BRANCH) \
					-t $(ECR_BASE)/z1-base:$(TIMESTAMP) \
					-t $(ECR_BASE)/z1-base \
					-f docker/Dockerfile.base . \
	&& docker tag $(ECR_BASE)/z1-base:$(TIMESTAMP) $(ECR_BASE)/z1-base:${BUILD_NUM} || true


build:	## rebuilds a zemanta/z1 docker image
	docker build 	--rm=false \
					-t $(ECR_BASE)/z1:$(GIT_HASH) \
					-t $(ECR_BASE)/z1:$(GIT_BRANCH) \
					-t $(ECR_BASE)/z1:$(TIMESTAMP) \
					-t $(ECR_BASE)/z1 \
					-t z1:$(BUILD_NUM) \
					-f docker/Dockerfile.z1 . \
	&& docker tag $(ECR_BASE)/z1:$(TIMESTAMP) $(ECR_BASE)/z1:${BUILD_NUM} || true

push_baseimage:	## pushes zemanta/z1-base docker image to registry
	test -n "$(GIT_BRANCH)" && docker push $(ECR_BASE)/z1-base:$(GIT_BRANCH)
	test -n "$(GIT_HASH)"	&& docker push $(ECR_BASE)/z1-base:$(GIT_HASH)
	test -n "$(BUILD_NUM)"	&& docker push $(ECR_BASE)/z1-base:$(BUILD_NUM)
	/usr/bin/test "$(GIT_BRANCH)" == "master" \
		&& docker tag $(ECR_BASE)/z1-base:$(GIT_BRANCH) $(ECR_BASE)/z1-base:current \
		&& docker push $(ECR_BASE)/z1-base:current \
		|| true

pull_baseimage:	## pulls zemanta/z1-base docker image
	docker pull $(ECR_BASE)/z1-base

push:	## pushes zemanta/z1 docker image to registry
	test -n "$(GIT_BRANCH)" && docker push $(ECR_BASE)/z1:$(GIT_BRANCH)
	test -n "$(GIT_HASH)"	&& docker push $(ECR_BASE)/z1:$(GIT_HASH)
	test -n "$(BUILD_NUM)"	&& docker push $(ECR_BASE)/z1:$(BUILD_NUM)
	/usr/bin/test "$(GIT_BRANCH)" == "master" \
		&& docker tag $(ECR_BASE)/z1:$(GIT_BRANCH) $(ECR_BASE)/z1:current \
		&& docker push $(ECR_BASE)/z1:current \
		|| true

update_baseimage: login build_baseimage push_baseimage	## helper combining build & push

update: login build push	## helper combining build & push

####################
#  CI help tasks   #
####################

rebuild_if_differ: ## compares requirements.txt and Dockerfile from Docker image with current git version
	@docker run --rm --entrypoint=/bin/bash $(ECR_BASE)/z1-base -c "cat /requirements.txt-installed /Dockerfile.base | md5sum" | cat > /tmp/docker-md5sum.txt
	@cat server/requirements.txt docker/Dockerfile.base | md5sum > /tmp/git-md5sum.txt
	@diff --ignore-all-space --text --brief /tmp/docker-md5sum.txt /tmp/git-md5sum.txt || make update_baseimage

#### Support for help/self-documenting feature
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ${MAKEFILE_LIST} | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help

