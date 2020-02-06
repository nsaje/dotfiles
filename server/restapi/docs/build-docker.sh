#!/bin/bash
DIR="$(dirname $(readlink -f $0))"

docker run -v $DIR:/tmp -t -e "DRAFTER_EXAMPLES=true" -e "NOCACHE=1" zemanta/z1-aglio -i "/tmp/api_blueprint.md" --theme-style "/tmp/theme/style.less" --theme-variables "/tmp/theme/variables.less" --theme-template "/tmp/theme/template.jade" -o "/tmp/$1"
