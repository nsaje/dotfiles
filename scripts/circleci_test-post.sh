#!/bin/bash

# Fail hard and fast
set -eo pipefail

case $CIRCLE_NODE_INDEX in
    0)
        # Push artifact
        cd server/
        echo "${CIRCLE_BUILD_NUM}" > build_number.txt
        git rev-parse HEAD > git_commit_hash.txt
        tar -pc * -zf $CIRCLE_ARTIFACTS/server.tar.gz; ../scripts/push_artifact_to_s3.sh $CIRCLE_ARTIFACTS/server.tar.gz
        ;;
    1)
        # Push artifact
        cd client/ && git rev-parse HEAD > dist/git_commit_hash.txt && tar -pc dist/ ../server/static -zf $CIRCLE_ARTIFACTS/client.tar.gz
        if [[ "$CIRCLE_BRANCH" == "master" ]]; then
            cd ..
            ./scripts/push_static_to_s3.sh;
        fi
        ;;
esac
