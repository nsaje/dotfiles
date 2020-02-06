#!/bin/bash

cleanup() {
    docker rm -f z1-rest-aglio
}
trap cleanup SIGINT

DIR="$(dirname $(readlink -f $0))"

cleanup
docker run --name z1-rest-aglio -p 3000:3000 -v $DIR:/tmp -t -e "DRAFTER_EXAMPLES=true" -e "NOCACHE=1" zemanta/z1-aglio -i "/tmp/api_blueprint.md" --theme-style "/tmp/theme/style.less" --theme-variables "/tmp/theme/variables.less" --theme-template "/tmp/theme/template.jade" -s -h 0.0.0.0 -p 3000
