SHELL := /bin/bash
# this is private Docker registry URL hosted on AWS
ECR_BASE = 569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta
GIT_HASH := $(shell git rev-parse --verify HEAD)
TIMESTAMP := $(shell date +"Created_%Y-%m-%d_%H.%M")

ifdef HUDSON_COOKIE # Jenkins
	GIT_BRANCH:= $(shell echo -n ${BRANCH_NAME} )# Jenkins
	BUILD_NUM:= $(shell echo -n ${BUILD_NUMBER} )# Jenkins
else # CircleCI
	GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
	BUILD_NUM  := $(shell test -n "${CIRCLE_BUILD_NUM}" && echo -n "${CIRCLE_BUILD_NUM}" || echo -n "00000" )
endif

run:	## runs whole stack with docker-compose
	docker-compose up --force-recreate -d

run_devenv:     ## run only development environment (i.e. services that are needed by z1).
	docker-compose -f docker-compose.yml -f docker-compose.devenv.yml up --force-recreate -d

reset_local_database:     ## loads latest demo dump to local postgres
	./scripts/reset_local_database.sh

reset_local_stats_database:     ## loads latest materialization dump to local stats postgres
	docker-compose run --rm eins ./manage.py reset_stats_postgres

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
	docker-compose -f docker-compose.yml -f docker-compose.jenkins.yml run -e CI_TEST=true --entrypoint=/entrypoint_dev.sh eins bash -x ./run_tests.sh

test_acceptance:	## runs tests against a running server in a container
ifdef GIT_BRANCH
	export ACCEPTANCE_IMAGE=z1:$(GIT_BRANCH).$(BUILD_NUM) && ./scripts/docker_test_acceptance.sh
else
	export ACCEPTANCE_IMAGE=$(ECR_BASE)/z1 && ./scripts/docker_test_acceptance.sh
endif

####################
# image management #
####################
login:	## login to ECR
ifdef ${LOGGED_IN}
	@echo "Already logged in"
else
	$$(aws ecr get-login --no-include-email)
	$(eval LOGGED_IN=yes)
endif


build_baseimage:	## rebuilds a zemanta/z1-base docker image
	docker pull python:3.6-slim
	docker build 	-t $(ECR_BASE)/z1-base:$(GIT_HASH) \
					-t $(ECR_BASE)/z1-base:$(GIT_BRANCH) \
					-t $(ECR_BASE)/z1-base:$(TIMESTAMP) \
					-t $(ECR_BASE)/z1-base \
					-f docker/Dockerfile.base . \
	&& docker tag $(ECR_BASE)/z1-base:$(TIMESTAMP) $(ECR_BASE)/z1-base:$(GIT_BRANCH).$(BUILD_NUM)


build:	## rebuilds a zemanta/z1 docker image
	docker build 	--rm=false \
					-t $(ECR_BASE)/z1:$(GIT_HASH) \
					-t $(ECR_BASE)/z1:$(GIT_BRANCH) \
					-t $(ECR_BASE)/z1:$(TIMESTAMP) \
					-t $(ECR_BASE)/z1 \
					-t z1:$(GIT_BRANCH).$(BUILD_NUM) \
					--build-arg BUILD=$(BUILD_NUM) \
					--build-arg BRANCH=$(GIT_BRANCH) \
					-f docker/Dockerfile.z1 . \
	&& docker tag $(ECR_BASE)/z1:$(TIMESTAMP) $(ECR_BASE)/z1:$(GIT_BRANCH).$(BUILD_NUM)

push_baseimage:	## pushes zemanta/z1-base docker image to registry
	test -n "$(GIT_BRANCH)" && docker push $(ECR_BASE)/z1-base:$(GIT_BRANCH)
	test -n "$(GIT_HASH)"	&& docker push $(ECR_BASE)/z1-base:$(GIT_HASH)
	test -n "$(BUILD_NUM)"	&& docker push $(ECR_BASE)/z1-base:$(GIT_BRANCH).$(BUILD_NUM)

pull: login	## pulls zemanta/z1-base docker image
	docker pull $(ECR_BASE)/z1-base:master && docker tag $(ECR_BASE)/z1-base:master $(ECR_BASE)/z1-base:latest
	docker pull $(ECR_BASE)/z1:master && docker tag $(ECR_BASE)/z1:master $(ECR_BASE)/z1:latest

push:	## pushes zemanta/z1 docker image to registry
	test -n "$(GIT_BRANCH)" && docker push $(ECR_BASE)/z1:$(GIT_BRANCH)
	test -n "$(GIT_HASH)"	&& docker push $(ECR_BASE)/z1:$(GIT_HASH)
	test -n "$(BUILD_NUM)"	&& docker push $(ECR_BASE)/z1:$(GIT_BRANCH).$(BUILD_NUM)

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

