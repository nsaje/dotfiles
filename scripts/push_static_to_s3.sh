#!/bin/bash

if [ -d client/dist ]
then
	sudo pip install awscli

	S3_PATH="s3://z1-static/build-$CIRCLE_BUILD_NUM"

	# need to set content-disposition for attachments sync assets separately
	aws s3 sync --acl public-read --content-disposition 'attachment' client/dist/one/assets "${S3_PATH}/client/one/assets"

	aws s3 sync --acl public-read --exclude 'assets/' client/dist "${S3_PATH}/client"
	aws s3 sync --acl public-read server/static "${S3_PATH}/server"


	echo $CIRCLE_BUILD_NUM | aws s3 cp - s3://z1-static/latest.txt
fi
