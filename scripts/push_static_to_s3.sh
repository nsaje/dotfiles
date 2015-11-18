#!/bin/bash

sudo pip install awscli

S3_PATH="s3://z1-static/build-$CIRCLE_BUILD_NUM/"

echo "Syncing static files to $S3_PATH"

aws s3 sync client/one/assets $S3_PATH/assets
aws s3 sync client/one/img $S3_PATH/img
