# Stay active in Slack

Little web scraper tool to stay active in Slack.

~~Writing this in Go since it's faster than doing the same in Python:<br>~~
- https://medium.com/@arnesh07/how-golang-can-save-you-days-of-web-scraping-72f019a6de87
- https://github.com/Arnesh07/golang-python-web-scraping

I was planning on writing this in Go with BeautifulSoup but ended up writing it in Python because BeautifulSoup 
is missing functionality that I need.<br>

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
    # Directory where the web browser can store session information so that you don't have to log on each time:
    # on Linux machines:
    data_dir: /home/<user>/.config/google-chrome/Default
    # on Macs:
    data_dir: /Users/<user>/Library/Application Support/Google/Chrome/Default
```
