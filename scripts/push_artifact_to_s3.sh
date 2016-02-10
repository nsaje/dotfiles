#!/bin/bash -x

if [ -f "$1" ]; then
    S3_PATH="s3://zemanta-artifacts/z1/build-${CIRCLE_BUILD_NUM}"
    BASENAME=$(basename $1)

    aws s3 cp --acl private "$1" "${S3_PATH}/${BASENAME}"

    if [[ "$CIRCLE_BRANCH" == "master" ]]; then
        echo "${CIRCLE_BUILD_NUM}" > latest.txt
        aws s3api put-object --bucket zemanta-artifacts --key z1/latest.txt --body latest.txt
    fi
fi
