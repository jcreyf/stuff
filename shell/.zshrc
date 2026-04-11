#!/bin/zsh

# Source global definitions
if [ -f /etc/zshrc ]; then
  . /etc/zshrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

#
# Some SSH commands like SCP and SFTP have issues with content in the .zshrc file
# when a remote shell is established.
# To solve that issue, we should do our best to keep the content that is getting sourced
# during non-interactive shells like SCP/SFTP to a bare minimun so it won't interfere.
#
case $- in
*i*)
  # This is an interactive shell.  Source in the whole sjaboem (set up in different file) ...
  . ~/.zshrc_jcreyf
  . ~/.zshrc_git
  . ~/.zshrc_nike
  . ~/.zshrc_containers
  ;;
esac

export TERM=xterm-color
export LSCOLORS=Gxfxcxdxbxegedabagacad

# Enable zsh built-in git completion (no need for external git-completion.sh)
autoload -Uz compinit && compinit

# Loading gimme-aws-creds CLI autocomplete:
# if [ -f /Users/jcreyf/data/nike/platforms/tools/gimme-aws-creds-autocomplete.sh ]; then
#   source /Users/jcreyf/data/nike/platforms/tools/gimme-aws-creds-autocomplete.sh
# fi

# Loading kubectl autocomplete (using native zsh completion):
if command -v kubectl &> /dev/null; then
  source <(kubectl completion zsh)
fi

# # Loading NSP1 epctl autocomplete:
# if command -v epctl &> /dev/null; then
#   source <(epctl completion zsh)
# fi

# Loading Helm CLI autocomplete (using native zsh completion):
if command -v helm &> /dev/null; then
  source <(helm completion zsh)
fi

# Loading Kafka CLI autocomplete: (https://github.com/birdayz/kaf)
if command -v kaf &> /dev/null; then
  source <(kaf completion zsh)
fi

# Loading Cerberus CLI autocomplete: (https://github.com/nike-zookeepers-cerberus/cerberus-cli)
#   https://github.com/nike-zookeepers-cerberus/cerberus-cli/blob/main/cerberus-completion.sh
# if [ -f /Users/jcreyf/data/nike/platforms/tools/cerberus-completion.sh ]; then
#   source /Users/jcreyf/data/nike/platforms/tools/cerberus-completion.sh
# fi

# Loading Terraform CLI autocomplete:
if command -v tf &> /dev/null; then
  source <(tf completion zsh)
fi

# Loading OAuth get_token CLI autocomplete:
alias get_token="/Users/jcreyf/data/nike/git/jcreyf_nike/scripts/get_token.sh"
if command -v get_token &> /dev/null; then
  source <(get_token completion zsh)
fi

# Loading gimme-creds CLI autocomplete:
alias gimme-creds="/Users/jcreyf/data/nike/git/jcreyf_nike/scripts/gimme-creds.sh"
if command -v gimme-creds &> /dev/null; then
  source <(gimme-creds completion zsh)
fi

#THIS MUST BE AT THE END OF THE FILE FOR SDKMAN TO WORK!!!
# Java JDKs managed through the 'sdkman'.
# Source in the sdkman-init script to get access to the sdk cli:
export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh"
