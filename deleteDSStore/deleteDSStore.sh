#!/usr/bin/env bash
#*********************************************************#
# Script to automatically remove all these pesky .DS_Store files in directories.
# These files are created by the file browser (Finder) when we navigate to some directory.
# Nuke em!!!!
#*********************************************************#
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

#log "running: deleteDSStore.sh"

# Change the default space delimiter to deal with directories that may have a space in their name:
_IFS=$IFS
IFS=$'\n'
# Find all the .DS_Store files in the home directory:
_files=($(find ~ -name ".DS_Store" 2>/dev/null))
log "${#_files[@]} '.DS_Store' files to delete:"
for _file in ${_files[*]}
do
  log "  $_file"
  rm -f $_file
done
# Restore the default delimiter:
IFS=$_IFS

# The find command will exit with "1" if no files found.
# Exit the script with a success code to avoid unnecessary launchd messages logging in /var/log/system.log
exit 0
