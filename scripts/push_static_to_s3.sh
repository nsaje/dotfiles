#!/bin/bash

if [ -d client/dist ]
then
	sudo pip install awscli
	
	S3_PATH="s3://z1-static/build-$CIRCLE_BUILD_NUM"
	
	aws s3 sync --acl public-read client/dist "${S3_PATH}/dist"
fi
