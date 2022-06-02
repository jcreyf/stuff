#!/usr/bin/env bash
#**********************************************************************************#
# Little script to kill all processes related to some tool.                        #
# I'm thinking here of tools that tend to pull down my internet connection because #
# it wants to be "smart" and "help" by copying all my data-files to some backup    #
# server.  You know who you are!!!                                                 #
# (Code42 is the flavor of tool today but have been different tools in the past)   #
# I don't get the permission to uninstall these apps and have very little to no    #
# control over what they broadcast or download, so the most effective way to try   #
# get them under control is by destroying the processes they spawn to do their     #
# dirty work.                                                                      #
#                                                                                  #
# This script expects you to have a NOPASSWD line in your sudoers config for the   #
# /bin/kill command so that you don't have to enter your password each time the    #
# script runs.                                                                     #
# I can take care of my own backups!  Lets cron this puppy!!!                      #
#----------------------------------------------------------------------------------#
# 2020-12-29 v1  jcreyf   Initial version                                          #
#----------------------------------------------------------------------------------#
SCRIPT_NAME=$(basename "$0")
SCRIPT_NAME_BASE=${SCRIPT_NAME%.*}
LOG_FILE="/Users/JCREYF/tmp/scripts.log"


#-------------------------------- 
# Helper method to log something to our log-file with a time stamp and output to the console
#-------------------------------- 
log()
{ 
  DT=`date +%m/%d/%y-%H:%M:%S`
#  echo "${DT} - ${SCRIPT_NAME_BASE} - $*" >> ${LOG_FILE}
  echo "${DT} - $*"
}

#log "running: killCode42.sh"

# sudo killall -d Code42

_procs=$(ps -eo pid,comm | grep -i Code42)

_pids=$(echo "$_procs" | sed -e 's/^[[:space:]]*//' | cut -d' ' -f1)
for _pid in ${_pids[*]} ; do
  # The '=' in the ps column fields is to supress printing the header for that column:
  log "killing process: $(ps -p $_pid -o pid=,comm=)"
  sudo kill -9 $_pid
done
