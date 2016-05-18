run:	## runs whole stack with docker-compose
	docker-compose up --force-recreate -d

run_devenv:     ## run only development environment (i.e. services that are needed by eins).
	docker-compose -f docker-compose.yml -f docker-compose.devenv.yml up --force-recreate -d

stop:	## stops the whole stack
	docker-compose stop

kill:	## kills the whole stack
	docker-compose kill

remove: ## removes all containers belonging to the stack
	docker-compose rm

# image management
build:	## rebuilds a zemanta/z1 docker image
	docker pull python:2.7
	docker build -t zemanta/z1 .
push:	## pushes zemanta/z1 docker image to DockerHub
	docker push zemanta/z1

update: build push ## helper combining build & push


#### Support for help/self-documenting feature
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help

