# .bashrc

#------------------
# IMPORTANT NOTE WHEN RUNNING BASH ON MAC:
#   https://itnext.io/upgrading-bash-on-macos-7138bd1066ba
#------------------

#
# See what shell type was opened and run some stuff based on type.
#
#SHELL_TYPE="$-"
#DT=`date +%m/%d/%y-%H:%M:%S`
#echo "${DT} - Opening a new shell: '${SHELL_TYPE}'" >> /home/jcreyf/systemd.jcreyf.log
#if [[ ${SHELL_TYPE} == *"i"* ]] ; then
#  # This is an interactive shell
#  echo "${DT} - Opening an interactive shell" >> /home/jcreyf/systemd.jcreyf.log
#else
#  echo "${DT} - Executing /home/jcreyf/.bashrc" >> /home/jcreyf/systemd.jcreyf.log
#  env >> /home/jcreyf/systemd.jcreyf.log
#  /home/jcreyf/Documents/scripts/detectScreen.sh >> /home/jcreyf/systemd.jcreyf.log
#fi


# Source global definitions
if [ -f /etc/bashrc ]; then
  . /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

#
# Some SSH commands like SCP and SFTP have issues with content in the .bashrc file
# when a remote shell is established.
# To solve that issue, we should do our best to keep the content that is getting sourced
# during non-interactive shells like SCP/SFTP to a bare minimun so it won't interfere.
#
case $- in
*i*)
  # This is an interactive shell.  Source in the whole sjaboem (set up in different file) ...
  . ~/.bashrc_jcreyf
  . ~/.bashrc_git
  ;;
esac

export TERM=xterm-color
export LSCOLORS=Gxfxcxdxbxegedabagacad

#export LSCOLORS='di=31'
#export CLICOLOR_FORCE=true
#export CLICOLOR=$LSCOLOR

#LSCOLORS="fi=01;37:di=01;34:ex=01;32:ln=37\
#:or=01;30:mi=00:mh=31\
#:pi=33:so=43;30:do=35\
#:bd=35;01:cd=35\
#:su=37;41:sg=30;43:ca=30;41\
#:tw=07;34:ow=30;44:st=30;44"

# Attribute codes:
# 00=none 01=bold 04=underscore 05=blink 07=reverse 08=concealed
# Text color codes:
# 30=black 31=red 32=green 33=yellow 34=blue 35=magenta 36=cyan 37=white
# Background color codes:
# 40=black 41=red 42=green 43=yellow 44=blue 45=magenta 46=cyan 47=white

#LS_COLORS="rs=0:\
#di=34;01:\
#ln=38;05:\
#mh=44;38;05:\
#pi=40;38;05:\
#so=38;05:\
#do=38;05:\
#bd=48;05;232;38;5;11:\
#cd=48;05;232;38;5;3:\
#or=48;05;232;38;5;9:\
#mi=05;48;05;232;38;5;15:\
#su=48;05;196;38;5;15:\
#sg=48;05;11;38;5;16:\
#ca=48;05;196;38;5;226:\
#tw=48;05;10;38;5;16:\
#ow=48;05;10;38;5;21:\
#st=48;05;21;38;5;15:\
#ex=34;00;31:\
#*.log=38;05;9"

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/home/jcreyf/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/jcreyf/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/home/jcreyf/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/home/jcreyf/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

