#!/bin/bash -x

# Fail hard and fast
set -eo pipefail

PROJECT="zemanta-eins"
BUILD_NUM=${BUILD_NUMBER}
BRANCH=${BRANCH_NAME}
S3_PATH="s3://zemanta-artifacts/${PROJECT}"

if [ -f "$1" ]; then
    BASENAME=$(basename $1)

    aws s3 cp --acl private "$1" "${S3_PATH}/${BRANCH}/${BUILD_NUM}/${BASENAME}"

    echo "${BUILD_NUM}" > latest.txt
    aws s3 cp --acl private latest.txt "${S3_PATH}/${BRANCH}/latest.txt"
fi
