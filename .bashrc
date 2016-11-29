# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions


#HISTORY
# Avoid duplicates
export HISTCONTROL=ignoredups:erasedups
# When the shell exits, append to the history file instead of overwriting it
shopt -s histappend
# unlimited history size
export HISTSIZE=
export HISTFILESIZE=
# write history in real time
PROMPT_COMMAND="history -a;$PROMPT_COMMAND"


# pip should only run if there is a virtualenv currently activated
export PIP_REQUIRE_VIRTUALENV=true
# cache pip-installed packages to avoid re-downloading
export PIP_DOWNLOAD_CACHE=$HOME/.pip/cache
syspip(){
   PIP_REQUIRE_VIRTUALENV="" pip "$@"
}

export WORKON_HOME=~/virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
export TERM=xterm-256color

genpasswd() {
	local l=$1
       	[ "$l" == "" ] && l=16
      	tr -dc A-Za-z0-9_ < /dev/urandom | head -c ${l} | xargs
}
 
eval "$(fasd --init auto)"

# prompt
export GITAWAREPROMPT=~/.bash/git-aware-prompt
source "${GITAWAREPROMPT}/main.sh"

#export PS1="\[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[\033[33;1m\]\w\[\033[m\]\n\$abc "
#export export PS1="\[$(tput bold)\][\u@\h\[$(tput sgr0)\] \[$(tput bold)\]\w]\[$(tput sgr0)\]\n\[$(tput bold)\]\\$\[$(tput sgr0)\] \[$(tput sgr0)\]"
#export PS1="\[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[\033[33;1m\]\w\[\033[m\]\n\$ "
#export PS1="\[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[\033[33;1m\]\w\[\033[m\]\n\[$txtcyn\]\$git_branch\[$txtred\]\$git_dirty\[$txtrst\] \$ "
#export PS1="\[$txtcyn\]\$git_branch\[$txtred\]\$git_dirty\[$txtrst\] \[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[\033[33;1m\]\w\[\033[m\]\n\$ "
export PS1="\[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[$txtcyn\]\$git_branch\[$txtred\]\$git_dirty\[$txtrst\] \[\033[33;1m\]\w\[\033[m\]\n\$ "
#export PS1="\u@\h \W \[$txtcyn\]\$git_branch\[$txtred\]\$git_dirty\[$txtrst\]\$ "


# alias nvim
alias vi="nvim"


export GOPATH=$HOME/.go
export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin
export GO15VENDOREXPERIMENT=1

export PATH="$PATH:~/go_appengine"
export PATH="$PATH:~/arduino-1.6.12"


[ -s "/home/nsaje/.scm_breeze/scm_breeze.sh" ] && source "/home/nsaje/.scm_breeze/scm_breeze.sh"

# git completion
source ~/.local/bin/git-completion.bash

# The next line updates PATH for the Google Cloud SDK.
source '/home/nsaje/Downloads/google-cloud-sdk/path.bash.inc'

# The next line enables shell command completion for gcloud.
source '/home/nsaje/Downloads/google-cloud-sdk/completion.bash.inc'
