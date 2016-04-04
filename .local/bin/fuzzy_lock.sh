#!/bin/sh -e

# Take a screenshot
scrot /tmp/screen_locked.png

# Pixellate it 10x
#convert /tmp/screen_locked.png -scale 5% -scale 2000% /tmp/screen_locked2.png
convert /tmp/screen_locked.png -scale 10% -scale 1000% /tmp/screen_locked2.png
#convert /tmp/screen_locked.png -blur 0x15 /tmp/screen_locked2.png
rm /tmp/screen_locked.png

# Lock screen displaying this image.
#i3lock -i /tmp/screen_locked.png
i3lock -i /tmp/screen_locked2.png

# Turn the screen off after a delay.
#sleep 60; pgrep i3lock && xset dpms force off
