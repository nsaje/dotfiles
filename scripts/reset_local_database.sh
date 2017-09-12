#!/bin/bash

set -eo pipefail

LATEST_DEMO_DUMP=$(aws s3 cp s3://z1-demo/latest.txt -)
DUMP_URL=$(aws s3 presign s3://z1-demo/$LATEST_DEMO_DUMP/dump.tar)
docker-compose run --rm -e DUMP_URL="$DUMP_URL" eins /prepare-demo.sh
docker-compose run --rm eins /create-dev-user.sh
