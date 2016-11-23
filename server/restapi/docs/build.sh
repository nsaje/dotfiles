#!/bin/bash
DIR="$(dirname $(readlink -f $0))"

NOCACHE=1 aglio -i "$DIR/api_blueprint.md" --theme-style "$DIR/theme/style.less" --theme-variables "$DIR/theme/variables.less" --theme-template "$DIR/theme/template.jade" "$@"
