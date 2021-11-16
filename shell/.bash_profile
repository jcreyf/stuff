# .bash_profile
#
# .bash_profile is being sourced in whenever the user logs on to the system.  Either locally
# in a console (or GUI) or remotely through ssh.
# .bashrc on the other hand is getting loaded each time a shell is opened (interactive or non-interactive).
# .bash_logout is being called whenever the user logs out of the system.
#

#
# Looks like the profile is only run when the computer is booted up.  Not when shells are started.
# As explained above, the profile is only being loaded as part of the user logging on to the system.
#
#DT=`date +%m/%d/%y-%H:%M:%S`
#echo "${DT} - Executing /home/jcreyf/.bash_profile" >> /home/jcreyf/systemd.jcreyf.log


# Source in the shell configurations
if [ -f ~/.bashrc ]; then
  . ~/.bashrc
fi
