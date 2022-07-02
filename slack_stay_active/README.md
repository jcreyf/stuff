# Stay active in Slack

Little web scraper tool to stay active in Slack.

~~Writing this in Go since it's faster than doing the same in Python:<br>~~
- https://medium.com/@arnesh07/how-golang-can-save-you-days-of-web-scraping-72f019a6de87
- https://github.com/Arnesh07/golang-python-web-scraping

I was planning on writing this in Go with BeautifulSoup but ended up writing it in Python because BeautifulSoup 
is missing functionality that I need.  I could of course also have used Selenium in Go but it seemed quite a bit easier in Python.<br>

Use config-file `slack_active.yaml` to control the app.<br>
Supported layout and properties in the file:<br>
```
---
config:
  # Do not click the mouse if we disable functionality:
  enabled: true
  # Output feedback to the console:
  debug: false
  click:
    # randomize the number of seconds between clicks?
    random: true
    # If 'random' is enabled, then the click will happen randomly between 1 second and whatever the 'seconds'
    # parameter is set to.  Otherwise, the click will happen every time at the end of this delay in seconds:
    seconds: 300
  slack:
    org_url: https://app.slack.com/client/<workspace code>/<channel code>
    workspace: <workspace name>
    username: <userID>
    password: <secret>
  webbrowser:
    # Directory where the web browser can store session information so that you don't have to log on each time.
    # See "Profile Path" when you navigate to "chrome://version" in your Chrome web browser.
    # on Linux machines:
    data_dir: /home/<user>/.config/google-chrome/Default
    # on Macs:
    data_dir: /Users/<user>/Library/Application Support/Google/Chrome/Default
    # Window position in "x,y" pixel coordinates on screen ("1,1" = top left corner of main display):
    window_position: 5,10
    # Window size in "width,height" pixels:
    window_size: 300,500
    # Either get the latest and greatest or set a specific version like: "102.0.5005.61"
    chrome_version: "latest"
```

The tool is using my own encryption module: https://github.com/jcreyf/secrets  

You can encrypt your password by using the `--encrypt` command line argument in combination with the `--key` argument (or setting the key in the environment variable described below).  

Set the used encryption key token in this environment variable so that the tool can decrypt the password:  
```
export JC_SECRETS_KEY=<key_string>
```
