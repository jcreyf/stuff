#!/bin/bash
#
# Try to find plain text on disk.
# Made this in a hurry to try find the contents of a file I deleted.
# This script needs to be run as root and the file system needs to be unmounted.
#

DISK=/dev/disk1s5
CHUNK_SIZE=$((8*1024*1024))
STRING="mouse_move"

i=0
while true ; do
  _data=$(dd if=$DISK bs=$CHUNK_SIZE count=1 skip=$i 2>/dev/null)
  if [ $? -gt 0 ] ; then 
    if [ $i -eq 0 ] ; then
      # If there is an error on the first run, then do it again and display the error:
      dd if=$DISK bs=$CHUNK_SIZE count=1 skip=$i
    else
      echo "End or error.  Chunks searched: $i (8MB each)"
      break
    fi
  fi
  echo $_data | grep -F "$STRING" && echo "chunk $i -> $_data"
  i=$(($i+1))
done
