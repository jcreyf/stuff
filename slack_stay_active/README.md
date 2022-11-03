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
  times:
    # Configure the days and times to be online on (optional).
    # If you don't set days/times, then the tool will keep you online 24/7.
    # You can configure multiple configs for different days.
    - name: "Regular Work Week"
      # Time of the day to set you online:
      start: "08:45"
      # Build in some randomness to show you online:
      # Set online somewhere between start time and a random number of minutes between 0 and this number (0 = default):
      start_random_minutes: 15
      # Stop setting online at this time of day:
      stop: "18:00"
      # Build in some randomness to show you offline:
      # Stop setting online somewhere between stop time and a random number of minutes between 0 and this number (0 = default):
      stop_random_minutes: 30
      # On which days of the week do these settings apply (Mo,Tu,We,Th,Fr,Sa,Su):
      days: "Mo,Tu,We,Th"
    - name: "Summer Hours"
      start: "08:45"
      start_random_minutes: 15
      stop: "13:00"
      stop_random_minutes: 30
      days: "Fr"
  exclusions:
    # Days on which we don't want to set our status (optional).
    - name: "End Year"
      date_from: 2022-12-25
      date_to: 2023-01-02
      yearly: true
    - name: "PTO"
      date_from: 2022-11-01
      date_to: 2022-11-03
```

The tool is using my own encryption module: https://github.com/jcreyf/secrets  

You can encrypt your password by using the `--encrypt` command line argument in combination with the `--key` argument (or setting the key in the environment variable described below).  

Set the used encryption key token in this environment variable so that the tool can decrypt the password:  
```
export JC_SECRETS_KEY=<key_string>
```

---

## Installation on Mac:

Skip all the Anaconda steps if you're not interested in setting up separate, shielded Python runtime environments.

- Install Anaconda:
```
/> brew install anaconda
```

- Setup your shell:  
(`conda init zsh` if you're using the default ZSH shell)  
```
/> conda init bash
```
I had to fix ownership of my `~/.conda/` directory on my Mac (it was owned by root and I had no permissions to write to this directory).  Fix (if needed):
```
/>  sudo chown -R $USER ~/.conda
```

- restart your shell

- Create Anaconda environment:  
(find the latest conda supported Python version here: https://repo.anaconda.com/pkgs/main/osx-64/ )  
```
/> conda create --name slack python=3.10.6
```

- Activate your slack environment:
```
/> conda activate slack
```

- Install the required modules for this app:  
```
/> conda install -c conda-forge selenium webdriver-manager cerberus yaml
```
- Install the required packages for the security app:  
```
/> conda install -c conda-forge pycryptodome
```

- Install dependencies that are for some reason not automatically installed:  
```
/> conda install -c conda-forge packaging
```

- Test the app:  
(this is what we expect to see when your Python environment is setup correctly)  
```
/> ./slack_active.py --test
** TEST MODE **
11/02 12:26:01: ==================
11/02 12:26:01: slack_active.py: v1.4 - 2022-10-26
11/02 12:26:01: Load config: /Users/JCREYF/data/jcreyf/git/jcreyf/stuff/slack_stay_active/slack_active.yaml
11/02 12:26:01: Load schema definition: /Users/JCREYF/data/jcreyf/git/jcreyf/stuff/slack_stay_active/config.schema
11/02 12:26:01: We don't have the encryption key!
11/02 12:26:01: Add it to the config-file or set environment variable: JC_SECRETS_KEY
```

---

## Download the code:
Run this in whichever directory you want to install this app:  
(this pulls down the code that we use to encrypt/decrypt our credentials)  
```
git clone https://github.com/jcreyf/secrets
```

In that same directory, run this to pull down the code for the app:  
```
git clone https://github.com/jcreyf/stuff
```
You can delete all sub-directories, except for `slack_stay_active`  

---

## Start script:
Navigate into the `./stuff/slack_stay_active/` directory.  
```
/> cat start.sh
source /usr/local/anaconda3/etc/profile.d/conda.sh
conda activate slack
echo $(conda info | grep "active environment")

export JC_SECRETS_KEY=<your key>
nohup <your directory>/stuff/slack_stay_active/slack_active.py 2>&1 > /tmp/slack_active.log &

pid=$(ps -ef | grep -v grep | grep slack_active.py | awk '{print $2}')
echo "PID: ${pid}"
```

---

## Encrypt your password:
Set the conda environment if not done already:  
```
/> conda activate slack
```

Use one of the below options to encrypt your password.  
Create file `~/jc_secrets_key.txt` with a secondary key string to add double protection in case your app key gets exposed somehow.  
```
/> cat ~/jc_secrets_key.txt
My2ndKey!
```

### Pass in the key through the command-line:
```
> ./slack_active.py -e MyPassword -k MyKey
...
11/02 14:28:13: Need to encrypt: MyPassword
Extra key set
11/02 14:28:13: String 'MyPassword' encrypts to: 'QXlSOUdVYnZhdUthYjdvb1FMcHBHbmRsNndaL0VINWpjcVJJb2lMdUZsZz0='
11/02 14:28:13: decrypts back to: 'MyPassword'
QXlSOUdVYnZhdUthYjdvb1FMcHBHbmRsNndaL0VINWpjcVJJb2lMdUZsZz0=
```

### Pass in the key through the `JC_SECRET_KEY` environment variable:
```
/> export JC_SECRETS_KEY=MyKey

/> ./slack_active.py -e MyPassword
...
11/02 14:32:13: Need to encrypt: MyPassword
Extra key set
11/02 14:32:13: String 'MyPassword' encrypts to: 'SWVXc3l2azh5aDVzVFJVMlVoeVlrRU56Zng4d3FZUWw3bzFpQXU3dEhDVT0='
11/02 14:32:13: decrypts back to: 'MyPassword'
SWVXc3l2azh5aDVzVFJVMlVoeVlrRU56Zng4d3FZUWw3bzFpQXU3dEhDVT0=
```

Now you can copy/paste this encrypted password into your `slack_active.yaml` file:
```
  slack:
    password: "SWVXc3l2azh5aDVzVFJVMlVoeVlrRU56Zng4d3FZUWw3bzFpQXU3dEhDVT0="
```

