#!/bin/bash
if [ -n "$CIRCLE_BUILD_NUM" ]; then
	BUILD_NUM=$CIRCLE_BUILD_NUM
  BRANCH=""
else
	BUILD_NUM=${BUILD_NUMBER:-manual}
  BRANCH=$BRANCH_NAME
  if [ "$BRANCH_NAME" == "master" ]; then
      BRANCH=""
  fi
fi

if [ -d client/dist ]; then
	S3_PATH="s3://z1-static/build-${BRANCH}${BUILD_NUM}"

	# need to set content-disposition for attachments sync assets separately
	aws s3 sync --acl public-read --content-disposition 'attachment' client/dist/one/assets "${S3_PATH}/client/one/assets"

	aws s3 sync --acl public-read --exclude 'assets/' client/dist "${S3_PATH}/client"
	aws s3 sync --acl public-read server/static "${S3_PATH}/server"


  if [ "$BRANCH_NAME" == "master" ]; then
	    echo ${BUILD_NUM} | aws s3 cp - s3://z1-static/latest.txt
  fi

	# Push styleguides to well-known URL
	aws s3 cp --acl public-read client/dist/one/zemanta-one.css s3://z1-static/styleguides/
	aws s3 cp --acl public-read client/dist/one/zemanta-one.lib.css s3://z1-static/styleguides/
fi

if [ -d client/dist ]; then
	S3_PATH="s3://one-static.zemanta.com/build-${BRANCH}${BUILD_NUM}"

	# need to set content-disposition for attachments sync assets separately
	aws s3 sync --acl public-read --content-disposition 'attachment' client/dist/one/assets "${S3_PATH}/client/one/assets"

	aws s3 sync --acl public-read --exclude 'assets/' client/dist "${S3_PATH}/client"
	aws s3 sync --acl public-read server/static "${S3_PATH}/server"


  if [ "$BRANCH_NAME" == "master" ]; then
    echo ${BUILD_NUM} | aws s3 cp - s3://one-static.zemanta.com/latest.txt
  fi

	# Push styleguides to well-known URL
	aws s3 cp --acl public-read client/dist/one/zemanta-one.css s3://one-static.zemanta.com/styleguides/
	aws s3 cp --acl public-read client/dist/one/zemanta-one.lib.css s3://one-static.zemanta.com/styleguides/
fi
