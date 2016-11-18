#!/bin/bash

RESTAPI_DOCS=server/restapi/docs/index.html

if [ -f "$RESTAPI_DOCS" ]
then
	S3_PATH="s3://dev.zemanta.com/one/api/build-$CIRCLE_BUILD_NUM.html"
	aws s3 cp "$RESTAPI_DOCS" "$S3_PATH"
fi
