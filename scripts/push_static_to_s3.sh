#!/bin/bash

sudo pip install awscli

S3_PATH="s3://z1-static/build-$CIRCLE_BUILD_NUM/"

echo "Syncing static files to $S3_PATH"
echo "Syncing client/one/assets"

ls client/one/assets
