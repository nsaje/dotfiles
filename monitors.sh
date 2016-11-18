#!/bin/bash

xrandr --output eDP1 --primary
xrandr --output DP1 --auto --above eDP1
xrandr --output DP2 --auto --left-of DP1 --rotate left
feh --bg-fill ~/Pictures/verdon.jpg

