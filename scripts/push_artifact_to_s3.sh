#!/bin/bash -x

PROJECT="zemanta-eins"

if [ -f "$1" ]; then
    S3_PATH="s3://zemanta-artifacts/${PROJECT}"
    BASENAME=$(basename $1)


    aws s3 cp --acl private "$1" "${S3_PATH}/build-${CIRCLE_BUILD_NUM}/${BASENAME}"

    if [[ "$CIRCLE_BRANCH" == "master" ]]; then
        echo "${CIRCLE_BUILD_NUM}" > latest.txt
        aws s3 cp --acl private latest.txt "${S3_PATH}/"
    fi
fi
