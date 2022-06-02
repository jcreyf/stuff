# Mouse Move

This is just a little helper app that is run as a daemon in the background to basically move the mouse pointer a little every so many seconds to prevent the screensaver from kicking in.  
The number of seconds is configurable in the `mouse_move.yaml` file and changes to the file will get detected during runtime and will be applied as soon as they are detected, so you can increase/decrease the delay time while the app is running in the background and you can temporarily disable mouse moves by turning off the `enabled` flag.  
