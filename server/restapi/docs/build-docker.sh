#!/bin/bash
DIR="$(dirname $(readlink -f $0))"
docker run --rm -v $DIR:/tmp 569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta/z1 bash -c "python manage.py api_blueprint_generate_constants /tmp/api_blueprint.md  > /tmp/api_blueprint_generated.md"
docker run --rm -v $DIR:/tmp -t -e "DRAFTER_EXAMPLES=true" -e "NOCACHE=1" zemanta/z1-aglio -i "/tmp/api_blueprint_generated.md" --theme-style "/tmp/theme/style.less" --theme-variables "/tmp/theme/variables.less" --theme-template "/tmp/theme/template.jade" -o "/tmp/$1"
