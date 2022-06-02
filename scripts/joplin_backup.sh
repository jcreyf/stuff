#!/usr/bin/env bash
#****************************************************************************#
# Script to backup all my Joplin notes and cleanup old backup directories.   #
#----------------------------------------------------------------------------#
# 2020/12/27  v1.0  jcreyf  Initial version                                  #
#****************************************************************************#
DATA_DIR="/data"
NOTES_DIR="notes_jo"
BACKUP_DIR="/data/backup"
LOG_FILE="${BACKUP_DIR}/joplin_backup.log"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NOTES_DIR="${BACKUP_DIR}/${NOTES_DIR}_${TIMESTAMP}"
DELETE_AFTER_DAYS=14


#-------------------------------- 
# Helper method to log something to our log-file with a time stamp and output to the console
#-------------------------------- 
log() 
{ 
  DT=`date +%m/%d/%y-%H:%M:%S` 
  echo "${DT} - $*" >> ${LOG_FILE}
#  echo "$*"
}


#
# Create a new backup:
#
log "Backup from '${DATA_DIR}/${NOTES_DIR}' to '${BACKUP_NOTES_DIR}'"
cp -rp ${DATA_DIR}/${NOTES_DIR} ${BACKUP_NOTES_DIR}
if [[ $? -ne 0 ]] ; then
  log "BACKUP FAILED!!!"
fi


#
# Delete backup directories that are older than 14 days:
#
# Get the number of seconds for today (midnight):
TODAY_IN_SECONDS=$(date -d $(date +%Y%m%d) +%s)
# Get a list of backup directories.
# this creates a list with elements like this:
#   /data/backup/notes_jo_20201227-213720
BACKUP_DIRECTORIES=$(find ${BACKUP_DIR} -type d -name "notes_jo_*")
# Loop through all these directories:
for _dir in ${BACKUP_DIRECTORIES} ; do
  # parse out the datestamp (sed will blank out everything until after "../notes_jo_"):
  _fileDate=$(echo "$_dir" | sed "s|${BACKUP_DIR}/${NOTES_DIR}_||" | cut -d"-" -f1)
  # get the number of seconds for the datestamp (midnight):
  _fileDateInSeconds=$(date -d $_fileDate +%s)
  # how many seconds is that older than today's number of seconds:
  _secondsDiff=$(($TODAY_IN_SECONDS - $_fileDateInSeconds))
  # 86400 seconds in a day:
  _numberOfDays=$(($_secondsDiff / 86400))
# display directory info:
#  log "$_dir  -> $_fileDate -> $_fileDateInSeconds -> $_numberOfDays"
  # delete the directory if it's older than the configured number of days:
  if [ "$_numberOfDays" -gt "${DELETE_AFTER_DAYS}" ] ; then
    log "deleting directory older than ${DELETE_AFTER_DAYS} days: $_dir"
    rm -rf $_dir
  fi
done
