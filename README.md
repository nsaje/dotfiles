Manually install:

```
dunst
fasd
x11-xkb-utils
xautolock
feh
pulseaudio-utils
xbacklight
fonts-roboto
scrot
```

For Vim:

``` 
wget https://github.com/Lokaltog/powerline/raw/develop/font/PowerlineSymbols.otf
wget https://github.com/Lokaltog/powerline/raw/develop/font/10-powerline-symbols.conf
mkdir ~/.fonts/
mv PowerlineSymbols.otf ~/.fonts/
fc-cache -vf ~/.fonts
mkdir -p ~/.config/fontconfig/conf.d/
mv 10-powerline-symbols.conf ~/.config/fontconfig/conf.d/
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
# :PluginInstall
```

Bash utils:

```
scm_breeze
git-completion.bash
```


Thinkpad touchpad:
`xinput --set-prop 11 "Synaptics Finger" 5 20 0`
