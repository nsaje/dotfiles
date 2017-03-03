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

	# Push styleguides to well-known URL
	aws s3 cp --acl public-read client/dist/one/zemanta-one.css s3://z1-static/styleguides/
	aws s3 cp --acl public-read client/dist/one/zemanta-one.lib.min.css s3://z1-static/styleguides/
fi

if [ -d client/dist ]; then
	S3_PATH="s3://one-static.zemanta.com/build-${BUILD_NUM}"

	# need to set content-disposition for attachments sync assets separately
	aws s3 sync --acl public-read --content-disposition 'attachment' client/dist/one/assets "${S3_PATH}/client/one/assets"

	aws s3 sync --acl public-read --exclude 'assets/' client/dist "${S3_PATH}/client"
	aws s3 sync --acl public-read server/static "${S3_PATH}/server"


	echo ${BUILD_NUM} | aws s3 cp - s3://one-static.zemanta.com/latest.txt

	# Push styleguides to well-known URL
	aws s3 cp --acl public-read client/dist/one/zemanta-one.css s3://one-static.zemanta.com/styleguides/
	aws s3 cp --acl public-read client/dist/one/zemanta-one.lib.min.css s3://one-static.zemanta.com/styleguides/
fi
