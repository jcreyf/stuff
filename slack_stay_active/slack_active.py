#!/usr/bin/env python3

# 
# Going with Selenium because we need more than just web scraping.  We need to provide user feedback
# as if the user is interacting with the web pages!
#
# Install the Selenium and Webdriver Manager packages:
#   pip install selenium webdriver-manager
#

import sys
import time
import yaml
import signal
import platform

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def signal_handler(signum, frame):
    print("End of app...")
    exit(0)


def main(argv):
    # Set the signal handler to deal with CTRL+C presses:
    signal.signal(signal.SIGINT, signal_handler)

    # Load the config file:
    with open("slack_active.yaml", "r") as stream:
        try:
            settings = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print(e)
            return 1

    # Parse the debug-flag and set a default if not found:
    try:
        DEBUG = settings['config']['debug']
        if DEBUG is None:
            DEBUG = False
    except KeyError:
        DEBUG = False

    # Parse the enabled-flag and set a default if not found:
    try:
        ENABLED = settings['config']['enabled']
        if ENABLED is None:
            ENABLED = True
    except KeyError:
        ENABLED = True

    # Parse the url to the Slack web page and throw an error if we didn't get it:
    try:
        SLACK_ORG_URL = settings['config']['slack']['org_url']
        if SLACK_ORG_URL is None:
            raise KeyError("Need a value for 'config.slack.org_url'!")
    except KeyError as err:
        print("Can't do anything if I don't have the url to your Slack org!")
        print("Set it in 'slack_active.yaml'")
        print(f"Error: {err}")
        return 1

    # Parse the workspace name in the Slack or and throw an error if we didn't get it:
    try:
        SLACK_WORKSPACE = settings['config']['slack']['workspace']
        if SLACK_WORKSPACE is None:
            raise KeyError("Need a value for 'config.slack.workspace'!")
    except KeyError as err:
        print("Can't do anything if I don't have the workspace in your Slack org!")
        print("Set it in 'slack_active.yaml'")
        print(f"Error: {err}")
        return 1

    # Parse the Slack user name and throw an error if we didn't get it:
    try:
        SLACK_USERNAME = settings['config']['slack']['username']
        if SLACK_USERNAME is None:
            raise KeyError("Need a value for 'config.slack.username'!")
    except KeyError as err:
        print("Can't do anything if I don't have the username to log on to Slack!")
        print("Set it in 'slack_active.yaml'")
        print(f"Error: {err}")
        return 1

    # Parse the Slack user password and throw an error if we didn't get it:
    try:
        SLACK_PASSWORD = settings['config']['slack']['password']
        if SLACK_PASSWORD is None:
            raise KeyError("Need a value for 'config.slack.password'!")
    except KeyError as err:
        print("Can't do anything if I don't have the password to log on to Slack!")
        print("Set it in 'slack_active.yaml'")
        print(f"Error: {err}")
        return 1

    # Display the configuration settings:
    print(f"debug: {DEBUG}")
    print(f"enabled: {ENABLED}")
    print(f"Slack url: {SLACK_ORG_URL}")
    print(f"Slack workspace: {SLACK_WORKSPACE}")
    print(f"Slack user: {SLACK_USERNAME}")

    chrome_options = Options()
    # Find a list of arguments here:
    #   https://peter.sh/experiments/chromium-command-line-switches/
    chrome_options.add_argument("window-position=5,10")
    chrome_options.add_argument("window-size=300,500")
    # Set the Google Chrome user profile dir.
    # This enables us to save the session information and with that, bypass a bunch of redirection and authentication
    # hoops if we want to run this frequently.  The browser will only force us through the Okta auth when the session
    # expired and we don't have valid cookies.
    # (see "Profile Path" when you navigate to "chrome://version" in your browser)
    #   Mac:   ~/Library/Application Support/Google/Chrome/Default
    #   Linux: ~/.config/google-chrome/default
    chrome_options.add_argument("user-data-dir='/Users/JCREYF/Library/Application Support/Google/Chrome/Default'")

    if not DEBUG:
        # Run the web browser hidden in the background.
        # Set the option to hide it:
        chrome_options.add_argument("--headless")

    # Open the web browser:
    webbrowser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        # Now navigate to the Slack web page and wait for it to be loaded:
        webbrowser.get(SLACK_ORG_URL)
        WebDriverWait(webbrowser, timeout=600).until(EC.presence_of_element_located((By.XPATH, "//html")))
    except:
        print("We got a timeout!  It's taking too long to load the page.")
        return 1

    # Zoom out to 75%
#    webbrowser.execute_script(f"document.body.style.zoom='75%'")
#    webbrowser.refresh()

    # We may already be on the Slack page at this point if we had a valid session and cookies in our Chrome cache.
    slack = EC.presence_of_element_located((By.CSS_SELECTOR, "meta[name='author'][content='Slack']"))
    if slack == None:
        # This is not the Slack page!
        # We need to go through the gates of hell...

        # This is when the "Sign in to your workspace" page comes up:
        #
        #   <input data-qa="signin_domain_input" aria-describedby="domain_hint" aria-invalid="false" 
        #          aria-labelledby="domain_label" aria-required="false" aria-label autocomplete="off" 
        #          class="c-input_text c-input_text--large full_width margin_bottom_100" 
        #          id="domain" name="domain" placeholder="your-workspace" type="text" value>
        # -> nikedigital
        workspace = WebDriverWait(webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='domain']")))
        workspace.clear()
        workspace.send_keys(SLACK_WORKSPACE)

        # Then click button "Continue":
        #   <button class="c-button c-button--primary c-button--large p-signin_form__aubergine_button full_width 
        #           margin_bottom_150" data-qa="submit_team_domain_button" type="submit">…</button>
        button = WebDriverWait(webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        button.click()

        # We now moved on to the "Sign in to Nike, Inc." page:
        #
        #   <a id="enterprise_member_guest_account_signin_link_Nike's OKTA / ID[me]" data-clog-event="WEBSITE_CLICK" 
        #      data-clog-params="click_target=enterprise_member_signin_with_saml_provider" 
        #      href="/sso/saml/start?redir=%2Fr-t16129201079%3Fredir%3D%252Fgantry%252Fauth%2…dca9f47164352ae3ac5ffee99ee7202a9001e8e8440cb1919079614992304&action=login" 
        #      class="btn btn_large sign_in_sso_btn top_margin">
        logon = WebDriverWait(webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-clog-event='WEBSITE_CLICK']")))
        logon.click()

        # We now moved to the "ID[me] Sign-in Page":
        #
        #   <input type="text" placeholder name="username" id="okta-signin-username" value aria-label 
        #          autocomplete="username" aria-required="true" required>
        # -> jo.creyf@nike.com
        username = WebDriverWait(webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
        username.clear()
        username.send_keys(SLACK_USERNAME)

        #   <input type="password" placeholder name="password" id="okta-signin-password" value aria-label 
        #          autocomplete="current-password" aria-invalid="false" aria-required="true" required>
        # -> secret
        password = WebDriverWait(webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
        password.clear()
        password.send_keys(SLACK_PASSWORD)

        # Then click "Sign In" button:
        #   <input class="button button-primary" type="submit" value="Sign In" id="okta-signin-submit" data-type="save">
        signin = WebDriverWait(webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
        signin.click()

        # We're now at the "Okta Verify" page:
        #   <label for="input82" data-se-for-name="autoPush" class>Send push automatically</label>
        #
        #   <input class="button button-primary" type="submit" value="Send Push" data-type="save">
        okta_verify = WebDriverWait(webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
        okta_verify.click()

        # We're now finally in Slack and should see all our channels and texts.
        # This is all we need to get flagged "active"
        # Wait for this element to be fully loaded and clickable:
        #   <button class="c-button-unstyled p-ia__nav__user__button p-top_nav__button p-top_nav__windows_controls_container"
        #           data-qa="user-button" aria-label="User menu: Jo Creyf" delay="150" aria-haspopup="menu"
        #           aria-expanded="false" data-sk="tooltip_parent" type="button">…</button>
#        user_menu = WebDriverWait(webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='user-button']")))


    # Zoom out to 50%
    webbrowser.execute_script(f"document.body.style.zoom='50%'")
    webbrowser.refresh()

    # Zoom out by clicking <CTRL><-> a number of times:
#    if platform.system() == "Darwin":
#        print("Mac")
#        ctrl_key = Keys.COMMAND
#    else:
#        ctrl_key = Keys.CONTROL

    # Loop forever, scrolling the page up and down every so many seconds:
    action = ActionChains(webbrowser)
    y = -200
    while True:
        print("move...")
        action.scroll_by_amount(0, y)
        if y == 200:
            y = -200
        else:
            y = 200
        time.sleep(5)

# The text input box at the bottom of the page:
# <div data-qa="message_input" data-message-input="true" data-channel-id="GEUFXD8AY" data-view-context="message-pane" data-min-lines="1" class="c-texty_input_unstyled ql-container focus">

# ToDo:
# - in the loop, detect if the browser got closed by the user.  If yes, open a new one and restart;


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))