#!/bin/bash
if [ -n "$CIRCLE_BUILD_NUM" ]; then
	BUILD_NUM=$CIRCLE_BUILD_NUM
else
	BUILD_NUM=${BUILD_NUMBER:-manual}
fi

if [ -d client/dist ]; then
	S3_PATH="s3://z1-static/build-${BUILD_NUM}"

	# need to set content-disposition for attachments sync assets separately
	aws s3 sync --acl public-read --content-disposition 'attachment' client/dist/one/assets "${S3_PATH}/client/one/assets"

	aws s3 sync --acl public-read --exclude 'assets/' client/dist "${S3_PATH}/client"
	aws s3 sync --acl public-read server/static "${S3_PATH}/server"


	echo ${BUILD_NUM} | aws s3 cp - s3://z1-static/latest.txt
fi
