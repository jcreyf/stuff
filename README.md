# Stuff
All kinds of random stuff


## - deleteDSStore
This is a little shell script to run on my MAC, that I typically run through launchd to periodically remove pesky `.DS_Store` files.

## - killCode42
This is another little shell script that I run through launchd to periodically check and kill Code42 processes.<br>
Code42 is a resource hog that is copying more than I want to some cloud storage and I don't have permissions to simply disable it.<br>
This piece of mallware just keeps on getting pushed back to my system if I dare to uninstall it.  It's also automatically restarting when I kill the process, so need to automate the killing for me.

## - mouse_move
This is a little tool, written in Golang, to move the mouse pointer on my machine every so many seconds.<br>
I made this to basically bypass the screensaver, over which I have no control and thus need to hack my way around it.<br>
I manually enable the screensaver whenever that makes sense.

## - scripts
A bucket of random scripts that seem important enough to version.

## - shell
My personal Bash profile files that are also important enough for me to version.

## - slack_stay_active
A little tool to send triggers to Slack to keep your userID in "active" state for as long as this app runs.