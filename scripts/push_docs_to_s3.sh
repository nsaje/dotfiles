#!/bin/bash

RESTAPI_DOCS=$1

if [ -f "$RESTAPI_DOCS" ]
then
	FILENAME=$(basename "$RESTAPI_DOCS")
	S3_PATH="s3://dev.zemanta.com/one/api/$FILENAME"
	aws s3 cp "$RESTAPI_DOCS" "$S3_PATH"
fi
