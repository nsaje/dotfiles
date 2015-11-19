#!/bin/bash

if [ -d client/dist ]
then
	sudo pip install awscli
	
	S3_PATH="s3://z1-static/build-$CIRCLE_BUILD_NUM"
	
	aws s3 sync --acl public-read client/dist "${S3_PATH}/client"
	
	echo $CIRCLE_BUILD_NUM > latest.txt
	aws s3api put-object --bucket z1-static --key latest.txt --body latest.txt
fi
