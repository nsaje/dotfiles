#!/bin/bash
DIR="$(dirname $(readlink -f $0))"

aglio -i $DIR/api_blueprint.md --theme-style $DIR/theme/style.less --theme-variables $DIR/theme/variables.less --theme-template $DIR/theme/template.jade -o $DIR/index.html
