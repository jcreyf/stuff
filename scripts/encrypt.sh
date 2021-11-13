#!/bin/bash
#===============================================================================================================#
# Script to encrypt / decrypt passwords into Base64 encoded strings.                                            #
#                                                                                                               #
# Script arguments:                                                                                             #
#   -p|--pwd <string>             : the password to encrypt/decrypt                                             #
#   -k|--key <string>             : the encryption/decryption key                                               #
#   -f|--file <path to file>      : location of the file with passwords to encrypt                              #
#   -d|--debug                    : Turn on debug level output                                                  #
#                                                                                                               #
# returns:                                                                                                      #
#      0 = SUCCESS                                                                                              #
#      1 = FAILURE                                                                                              #
#                                                                                                               #
# ex. ${SCRIPT_NAME} -k MySecret -p EncryptMe                                                                   #
#     ${SCRIPT_NAME} -k 'R#4!trOp' -p '8R9#%ju@oui'                                                             #
#     ${SCRIPT_NAME} -k SuperSecret4U -f MyCredentials.md                                                       #
#---------------------------------------------------------------------------------------------------------------#
# 2021-05-24  v1.0  jcreyf  Initial version                                                                     #
#===============================================================================================================#

# We have a very specific way of parsing command line arguments because we first save the arguments in an array
# at the very beginning of the script and we're iterating over all elements much later in the script where these
# values would typically have been reset through other commands that we run to prepare the script.
# Some command line arguments may contain spaces, which are typically field delimiters in bash!
# We need to make sure to keep string values together that may have spaces in them (the --description argument).
ARGS=("$@")

ENCRYPTION_KEY=""
FILE_TO_PROCESS=""
PASSWORDS=""
DEBUG=${DEBUG:-false}

# Static variables
SCRIPT_VERSION="v1.0 (2021-05-24)"
STATE_SUCCESS=0
STATE_CONDITIONAL_SUCCESS=50
STATE_FAIL=1


#--------------------------------
# Helper method to log something to our log-file with a time stamp
#--------------------------------
log()
{
  if [ -z "$*" ] ; then
    # Add a blank line if we received an empty sting, not prefixing a timestamp
    echo ""
  else
    # We may add newlines to our log-messages.  If so, then have printf parse them!
    # We don't want the printf command use the "%b" field indicator for everything since we may have backslashes in our text/data
    # which may not be part of some special character.
    if [[ $* == *"\\"* ]] ; then
      printf "%b\n" "$*"
    else
      printf "%s\n" "$*"
    fi
  fi
}


#--------------------------------
# Helper method to log something if the debug-flag is enabled
#--------------------------------
logDebug()
{
  ${DEBUG} && log "$*"
}


#--------------------------------
# Read and validate command line arguments
# We have a very specific way of parsing command line arguments because we first save the arguments in an array
# at the very beginning of the script and we're iterating over all elements here.
# Some arguments may contain spaces though, which are typically field delimiters in bash!
# We need to make sure to keep string values together that may have spaces in them (the --description argument).
#--------------------------------
parseArguments() {
  if [[ "${#ARGS[@]}" -eq 0 ]] ; then
    usage
    endScript ${STATE_FAIL}
  else
    # Loop through the values in the $ARGS variable
    for((index=0; index <= ${#ARGS[@]}; index++)) ; do
      case "${ARGS[index]}" in
        -p|--pwd)
          ((index+=1))
          PASSWORDS=("${ARGS[index]}")
          ;;
        -k|--key)
          ((index+=1))
          ENCRYPTION_KEY=("${ARGS[index]}")
          ;;
        -f|--file)
          ((index+=1))
          FILE_TO_PROCESS="${ARGS[index]}"
          ;;
        -d|--debug)
          DEBUG=true
          ;;
        -*|*)
          if [ -n "${ARGS[index]}" ] ; then
            log "Argument not supported: '${ARGS[index]}'"
            log ""
            usage
            endScript ${STATE_FAIL}
          fi
          ;;
      esac
    done
  fi

  if [ -z ${ENCRYPTION_KEY} ] ; then
    log "Need an encryption key!!!"
    endScript ${STATE_FAIL}
  fi

  if [ -z ${PASSWORDS} ] && [ -z ${FILE_TO_PROCESS} ] ; then
    log "Need a password or a file with passwords to chew on!!!"
    endScript ${STATE_FAIL}
  fi
}


#--------------------------------
# Display a usage
#--------------------------------
usage() {
  echo "${SCRIPT_NAME} - ${SCRIPT_VERSION}"
  echo "Script to encrypt/decrypt passwords."
  echo ""
  echo "Script arguments:"
  echo "  -p|--pwd <string>             : the password to encrypt/decrypt"
  echo "  -k|--key <string>             : the encryption/decryption key"
  echo "  -f|--file <path to file>      : location of the file with passwords to encrypt"
  echo "  -d|--debug                    : Turn on debug level output"
  echo ""
  echo "returns:"
  echo "     0 = SUCCESS"
  echo "     1 = FAILURE"
  echo ""
  echo "ex. ${SCRIPT_NAME} -k MySecret -p EncryptMe"
  echo "    ${SCRIPT_NAME} -k 'R#4!trOp' -p '8R9#%ju@oui'"
  echo "    ${SCRIPT_NAME} -k SuperSecret4U -f MyCredentials.md"
  echo ""
}


#--------------------------------
# See if a string is Base64 encoded (telltail sign that this is an encrypted password).
# Base64 encoding is surprisingly difficult to detect!!!
# There are no bash tools or simple commands to determine whether or not a string is Base64 encoded.
# We know that our passwords are constructed from numbers; letters and punctuation characters but non-printable characters.
# Punctuation Characters ([:punct:]) ->  !”#$%&‘()*+,–./:;<=>?@[\]^_`{|}~
# I've tried using regular expressions to try match: ^[0-9a-zA-Z[:punct:]]*$
# Need to check for ASCII values 32 (0x20) > char < 127 (0x7F)
#--------------------------------
isEncoded()
{
  local _pwd="$1"
  if [ $((${#_pwd} % 4)) -eq 0 ] ; then
    # This password is a multiple of 4 characters long, which may indicate that it's a Base64 encoded string
    # Non encoded 4 character strings are slipping through the maze and I can't seem to find a good way to filter
    # them out.  I tried filtering them out in the modulus 4 check but is not working for some dark reason.
    # Decoding a non-encoded 4 character string results in non-printable characters just like any other sized string
    # but the non of the checks I've tried below is catching this!  I have to assume at this stage that there is a bug
    # somewhere in the base64 or grep commands that is preventing me from catching these cases.
    # Am done trying to find a clean way to filter them out!  We're never going to see Base64 encoded strings that are
    # only 4 characters long.  If it's a 4 character string, then assume it's plain text!!!
    if [ ${#_pwd} -eq 4 ] ; then
      echo 1
    else
      local _decrypted==$(decrypt "${_pwd}")
      # The tr-command throws a fit if it hits a non-printable character:
      #   tr -cd '[:print:]' <<< "$_decrypted" 2>&1 >/dev/null
      # Trying to grep again for printable characters only.  Grep will throw a fit if it hits a non-printable character:
      grep "^[0-9a-zA-Z[:punct:]]*$" <<< $_decrypted 2>&1 >/dev/null
      if [ $? -eq 0 ] ; then
        echo 0
      else
        echo 1
      fi
    fi
  else
    # The password is not a multiple of 4 characters long and thus definately not a Base64 encoded string!
    echo 1
  fi
}


#--------------------------------
# Encrypt a single password
#--------------------------------
encrypt()
{
  local _pwd="$1"
  logDebug "encrypting ${_pwd}"
  # Encrypt the pwd and encode in base64:
  local _encrypted=$(echo "${_pwd}" | openssl enc -e -aes-256-cbc -a -k "${ENCRYPTION_KEY}" | base64)
  echo "$_encrypted"
}


#--------------------------------
# Decrypt a single password
#--------------------------------
decrypt()
{
  local _pwd="$1"
  logDebug "decrypting ${_pwd}"
  # Decrypt the password:
  local _decrypted=$(echo "${_pwd}" | base64 -d | openssl base64 -d | openssl enc -d -aes-256-cbc -k "${ENCRYPTION_KEY}")
  echo "$_decrypted"
}


#--------------------------------
# Encrypt or Decrypt a single password
#--------------------------------
processPassword()
{
  local _pwd="$1"
  logDebug "Processing password: ${_pwd}"
  local _flag=$(isEncoded "$_pwd")
  if [[ $_flag -eq 0 ]] ; then
    echo $(decrypt "$_pwd")
  else
    echo $(encrypt "$_pwd")
  fi
}


#--------------------------------
# Encrypt/Decrypt all password tags in a file
#--------------------------------
processFile()
{
  local _file="$1" _pwd="" _encrypted="" _decrypted="" _same=false

  log "Processing file: $_file"

  # Parse out all the passwords:
  # (using the BeautifulSoup library in Python to parse the HTML and filter out all <PWD>-tags)
  # (adding a pipe '|' after each value so that we can use that as field separator in Bash instead
  # of the default whitespace.  Some values have spaces in them so we need to make sure to keep it
  # all together correctly)
  PASSWORDS=$(python3 -c 'if True:
              import sys
              from bs4 import BeautifulSoup
              html = BeautifulSoup(open(sys.argv[1]).read())
              for pwd in html.findAll("pwd"):
                print(("{pwd}|").format(pwd=pwd.contents[0]))
              ' ${_file} | sort | uniq)

  # Change the standard (space) field separator to pipe:
  local _ifs=$IFS
  IFS="|"

  if [ ${#PASSWORDS[@]} -gt 0 ] ; then
    # Create a backup of the file if we have passwords to process:
    cp $_file "${_file}_"$(date +"%Y%m%d-%H%M")
  fi

  # Loop through all the values in the list:
  for _pwd in ${PASSWORDS} ; do
    # Remove the extra characters that python added (quotes for strings and newlines):
    _pwd=$(echo "${_pwd//[$'\r\n']}" | sed -e "s/'//g")
    # Check to see if the password is encrypted:
# This check is not reliable :-(
# Not spending more time on this right now!!!
# I know that all strings in the file are plain text ... encrypt and encode!!!
# I'll circle back to this later when time comes to go the opposite direction when my encryption key changes.
#
#    local _flag=$(isEncoded "$_pwd")
#    if [ $_flag -eq 0 ] ; then
#log "pwd '$_pwd' is encoded!"
#      _decrypted=$(decrypt "$_pwd")
#      _encrypted=$(encrypt "$_decrypted")
#      _same=$([ "$_pwd" == "$_encrypted" ] && echo true || echo false)
#    else
#log "pwd '$_pwd' is not encoded!"
      _encrypted=$(encrypt "$_pwd")
      _decrypted=$(decrypt "$_encrypted")
      _same=$([ "$_pwd" == "$_encrypted" ] && echo true || echo false)
#    fi

    # All is good if the decoded and decrypted string is the same as the password:
    if $_same ; then
      log "replacing pwd: '${_pwd}' with '${_encrypted}'"
      # Replace all the occurences of this password in the file (can be 1 to many occurences):
      sed -i -e "s|<PWD>${_pwd}</PWD>|<PWD>${_encrypted}</PWD>|g" $_file
      if [ $? -ne 0 ] ; then
        log "FAILED TO REPLACE THE PASSWORD!!!"
      fi
    else
      log "BAD ENCRYPTION/ENCODING!!! '${_pwd}' -> ${_encrypted} -> '${_decrypted}'"
    fi
  done

  # Restore the field separator:
  IFS=$_ifs
}


#--------------------------------
# End the script and set an endScript value
#--------------------------------
endScript() {
  local _exitValue=$1
  case $_exitValue in
    ${STATE_FAIL})
      log "Finished: FAILED"
      ;;
    ${STATE_SUCCESS})
      log "Finished: SUCCESS"
      ;;
    *)
      log "Finished: CONDITIONAL SUCCESS"
      ;;
  esac
  exit $_exitValue
}



#################################
#  THE SCRIPT STARTS HERE!!!!   #
#################################
parseArguments

if [ -z "${FILE_TO_PROCESS}" ] ; then
  processPassword ${PASSWORDS}
else
  processFile ${FILE_TO_PROCESS}
fi
