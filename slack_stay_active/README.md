# Stay active in Slack

Little web scraper tool to stay active in Slack.

Writing this in Go since it's faster than doing the same in Python:<br>
- https://medium.com/@arnesh07/how-golang-can-save-you-days-of-web-scraping-72f019a6de87
- https://github.com/Arnesh07/golang-python-web-scraping

Use config-file `slack_active.yaml` to control the app.<br>
Supported data format for the file:<br>
```
---
config:
  # Do not click the mouse if we disable functionality:
  enabled: true
  # Output feedback to the console:
  debug: false
  click_every_N_seconds: 300
  slack:
    org_url: https://app.slack.com/client/<workspace code>/<channel code>
    workspace: <workspace name>
    username: <userID>
    password: <secret>
```
