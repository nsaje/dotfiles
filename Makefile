run:
	docker-compose up --force-recreate -d

stop:
	docker-compose stop

kill:
	docker-compose kill

remove:
	docker-compose rm

# image management
build:
	docker pull python:2.7
	docker build -t zemanta/z1 .
push:
	docker push zemanta/z2

update: build push

