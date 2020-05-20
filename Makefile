SHELL := /bin/bash
# this is private Docker registry URL hosted on AWS
ECR_BASE = 569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta
GIT_HASH := $(shell git rev-parse --verify HEAD)
TIMESTAMP := $(shell date +"Created_%Y-%m-%d_%H.%M")

ifdef HUDSON_COOKIE # Jenkins
	GIT_BRANCH := $(shell printf ${BRANCH_NAME} )# Jenkins
	BUILD_NUM := $(shell printf ${BUILD_NUMBER} )# Jenkins
	Z1_CLIENT_IMAGE := $(shell printf "$(ECR_BASE)/z1-client:$(GIT_BRANCH).$(BUILD_NUM)")
	Z1_SERVER_IMAGE := $(shell printf "$(ECR_BASE)/z1:$(GIT_BRANCH).$(BUILD_NUM)")
	ACCEPTANCE_IMAGE := $(shell printf "$(ECR_BASE)/z1:$(GIT_BRANCH).$(BUILD_NUM)")
	SKIP_TESTS := $(shell [[ "$(GIT_BRANCH)" == *skiptest* ]] && echo "true" || echo "")
else # Local development environment
	GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
	BUILD_NUM  := $(shell printf "00000" )
	Z1_CLIENT_IMAGE := $(shell printf "$(ECR_BASE)/z1-client")
	Z1_SERVER_IMAGE := $(shell printf "$(ECR_BASE)/z1")
	ACCEPTANCE_IMAGE := $(shell printf "$(ECR_BASE)/z1")
	SKIP_TESTS := ""
endif

# Exported because docker-compose.*.yml uses it
export Z1_CLIENT_IMAGE
export Z1_SERVER_IMAGE
export ACCEPTANCE_IMAGE
export TESTIM_TOKEN

run:	## runs whole stack with docker-compose
	docker-compose up --force-recreate -d

run_devenv:	## runs only development environment (i.e. services that are needed by z1)
	docker-compose -f docker-compose.yml -f docker-compose.devenv.yml up --force-recreate -d

run_clientless:	## runs whole stack except for the client (saves resources when client is not needed)
	docker-compose up --force-recreate -d postgres statspostgres memcached telegraf server

stop:	## stops the whole stack
	docker-compose stop

kill:	## kills the whole stack
	docker-compose kill

remove:	## removes all containers belonging to the stack
	docker-compose rm

run_e2e_creator:	## runs whole e2e stack with docker-compose
	docker-compose -p e2e-creator-zemanta-eins -f docker-compose.yml -f docker-compose.e2e-creator.yml up --force-recreate -d

stop_e2e_creator:	## stops the whole e2e stack
	docker-compose -p e2e-creator-zemanta-eins -f docker-compose.yml -f docker-compose.e2e-creator.yml stop

kill_e2e_creator:	## kills the whole e2e stack
	docker-compose -p e2e-creator-zemanta-eins -f docker-compose.yml -f docker-compose.e2e-creator.yml kill

remove_e2e_creator:	## removes all containers belonging to the e2e stack
	docker-compose -p e2e-creator-zemanta-eins -f docker-compose.yml -f docker-compose.e2e-creator.yml rm

reset_local_database:	## loads latest demo dump to local postgres
	./scripts/reset_local_database.sh

reset_local_stats_database:	## loads latest materialization dump to local stats postgres
	docker-compose run --rm server ./manage.py reset_stats_postgres

test_server:	## runs server tests
	mkdir -p server/.junit_xml/
	[ -n "$(SKIP_TESTS)" ] && echo "Skipping tests due to skiptest in branch name, PASSED" || \
	docker-compose \
			-f docker-compose.yml \
			-f docker-compose.server-test.yml \
			run \
			--rm \
			-e CI_TEST=true --entrypoint=/entrypoint_dev.sh \
			server bash -x ./run_tests.sh

test_client:	## runs client tests
	[ -n "$(SKIP_TESTS)" ] && echo "Skipping tests due to skiptest in branch name" || \
	docker run \
		   --rm \
		   -u 1000 \
		   -v $(PWD)/client/:/app/ \
		   -v /app/node_modules/ \
		   -e CHROME_BIN=/run-chrome.sh \
		   $(Z1_CLIENT_IMAGE) \
		   bash -c "npm run tests"

test_acceptance:	## runs tests against a running server in a container
	[ -n "$(SKIP_TESTS)" ] && echo "Skipping tests due to skiptest in branch name" || \
	./scripts/docker_test_acceptance.sh

test_e2e:	## runs e2e tests against a running app in a container
	[ -n "$(SKIP_TESTS)" ] && echo "Skipping tests due to skiptest in branch name" || \
	./scripts/docker_test_e2e.sh

lint_server:	## runs server linters
	[ -n "$(SKIP_TESTS)" ] && echo "Skipping tests due to skiptest in branch name" || \
	bash ./scripts/lint_check.sh

lint_client:	## runs client linters
	[ -n "$(SKIP_TESTS)" ] && echo "Skipping tests due to skiptest in branch name" || \
	docker run \
		   --rm \
		   -v $(PWD)/client:/app/ \
		   -v /app/node_modules/ \
		   $(Z1_CLIENT_IMAGE) \
		   bash -c "npm run lint"

build_client:	## builds client app for production
	docker run \
		   --rm \
		   -v $(PWD)/client:/app/ \
		   -v /app/node_modules/ \
		   $(Z1_CLIENT_IMAGE) \
		   bash -c "npm run prod --build-number=$(BUILD_NUM) --branch-name=$(GIT_BRANCH) --sentry-token=$(Z1_SENTRY_TOKEN)"

collect_server_static:	## collects static files for production build
	rm -rf server/static && mkdir server/static && chmod 777 server/static
	docker run \
		--rm \
    --env IS_COLLECTSTATIC=1 \
		-v $(PWD)/server/:/app/z1/ \
		-v $(PWD)/server/.junit_xml/:/app/z1/.junit_xml/ \
		-v $(PWD)/server/static/:/app/z1/static/ \
		$(Z1_SERVER_IMAGE) \
		bash -c "python manage.py collectstatic --noinput"

refresh_requirements: login build_utils
	docker run --rm \
    -v $$PWD:/src \
	--user ubuntu \
    --workdir=/src/ \
    --entrypoint=sh \
    py3-tools -c "pip-compile -v --no-annotate server/requirements.in"

####################
# image management #
####################

login:	## login to ECR
ifdef ${LOGGED_IN}
	@echo "Already logged in"
else
	$$(aws ecr get-login --no-include-email 2>/dev/null) || aws ecr get-login-password | docker login --username AWS --password-stdin $(ECR_BASE)
	$(eval LOGGED_IN=yes)
endif

build_baseimage:	## rebuilds a zemanta/z1-base docker image
	docker pull python:3.7.5-slim
	docker build 	-t $(ECR_BASE)/z1-base:$(GIT_HASH) \
					-t $(ECR_BASE)/z1-base:$(GIT_BRANCH) \
					-t $(ECR_BASE)/z1-base:$(TIMESTAMP) \
					-t $(ECR_BASE)/z1-base:$(GIT_BRANCH).$(BUILD_NUM) \
					-t $(ECR_BASE)/z1-base \
					-f docker/Dockerfile.base .

build:	## rebuilds a zemanta/z1 && zemanta/z1-client docker image
	docker build --rm=false \
				-t $(ECR_BASE)/z1:$(GIT_HASH) \
				-t $(ECR_BASE)/z1:$(GIT_BRANCH) \
				-t $(ECR_BASE)/z1:$(TIMESTAMP) \
				-t $(ECR_BASE)/z1:$(GIT_BRANCH).$(BUILD_NUM) \
				-t $(ECR_BASE)/z1 \
				-t z1 \
				--build-arg BUILD=$(BUILD_NUM) \
				--build-arg BRANCH=$(GIT_BRANCH) \
				-f docker/Dockerfile.z1 . \
	# You can't mount volume during build time because of docker version mismatch. This is workaround:
	cp client/package.json docker/ \
	&& cp client/npm-shrinkwrap.json docker/ \
	&& docker build --rm=false \
					-t $(ECR_BASE)/z1-client:$(GIT_HASH) \
					-t $(ECR_BASE)/z1-client:$(GIT_BRANCH) \
					-t $(ECR_BASE)/z1-client:$(TIMESTAMP) \
					-t $(ECR_BASE)/z1-client:$(GIT_BRANCH).$(BUILD_NUM) \
					-t $(ECR_BASE)/z1-client \
					-t z1-client \
					-f docker/Dockerfile.z1-client docker/ \
	&& rm docker/package.json \
	&& rm docker/npm-shrinkwrap.json

build_utils:	## builds utility images for CI
	docker build -t py3-tools -f docker/Dockerfile.py3-tools  docker/
	docker build -t zemanta/z1-aglio -f docker/Dockerfile.z1-aglio docker/

pull: login	## pulls zemanta docker images
	docker pull $(ECR_BASE)/z1-base:master && docker tag $(ECR_BASE)/z1-base:master $(ECR_BASE)/z1-base:latest
	docker pull $(ECR_BASE)/z1:master && docker tag $(ECR_BASE)/z1:master $(ECR_BASE)/z1:latest
	docker pull $(ECR_BASE)/z1-client:master && docker tag $(ECR_BASE)/z1-client:master $(ECR_BASE)/z1-client:latest

pull_testim:
	docker pull testim/docker-cli:node-8

push_baseimage:	## pushes zemanta/z1-base docker image to registry
	test -n "$(GIT_BRANCH)" && docker push $(ECR_BASE)/z1-base:$(GIT_BRANCH)
	test -n "$(GIT_HASH)"	&& docker push $(ECR_BASE)/z1-base:$(GIT_HASH)
	test -n "$(BUILD_NUM)"	&& docker push $(ECR_BASE)/z1-base:$(GIT_BRANCH).$(BUILD_NUM)

push:	## pushes zemanta/z1 && zemanta/z1-client docker image to registry
	test -n "$(GIT_BRANCH)" && docker push $(ECR_BASE)/z1:$(GIT_BRANCH)
	test -n "$(GIT_HASH)"	&& docker push $(ECR_BASE)/z1:$(GIT_HASH)
	test -n "$(BUILD_NUM)"	&& docker push $(ECR_BASE)/z1:$(GIT_BRANCH).$(BUILD_NUM)
	test -n "$(GIT_BRANCH)" && docker push $(ECR_BASE)/z1-client:$(GIT_BRANCH)
	test -n "$(GIT_HASH)"	&& docker push $(ECR_BASE)/z1-client:$(GIT_HASH)
	test -n "$(BUILD_NUM)"	&& docker push $(ECR_BASE)/z1-client:$(GIT_BRANCH).$(BUILD_NUM)

update_baseimage: login build_baseimage push_baseimage	## helper combining build_baseimage & push_baseimage

update: login build push	## helper combining build & push

####################
#  CI help tasks   #
####################

rebuild_if_differ:	## compares requirements.txt and Dockerfile from Docker image with current git version
	@docker run --rm --entrypoint=/bin/bash $(ECR_BASE)/z1-base -c "cat /requirements.txt-installed /Dockerfile.base | md5sum" | cat > /tmp/docker-md5sum.txt
	@cat server/requirements.txt docker/Dockerfile.base | md5sum > /tmp/git-md5sum.txt
	@diff --ignore-all-space --text --brief /tmp/docker-md5sum.txt /tmp/git-md5sum.txt || make update_baseimage

help:	#### Support for help/self-documenting feature
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ${MAKEFILE_LIST} | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help
