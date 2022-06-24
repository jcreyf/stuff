#!/usr/bin/env python3
# ======================================================================================================== #
# Little app to keep me 'active' in Slack ... even when I'm "slacking" ;-)                                 #
#                                                                                                          #
# Arguments:                                                                                               #
#    --encrypt <string> | -e <string>        :encrypt a string so that we can copy/paste it into our yaml  #
#                                                                                                          #
# -------------------------------------------------------------------------------------------------------- #
# Going with Selenium because we need more than just web scraping.  We need to provide user input as if    #
# the user is interacting with the web pages!                                                              #
#                                                                                                          #
# Install the Selenium and Webdriver Manager packages:                                                     #
# (make sure to have Selenium v4 or greater installed!)                                                    #
#   pip install selenium                                                                                   #
# Webdriver-manager is no longer needed in Selenium v4 and up.  The driver is now built in Selenium.       #
#   pip install webdriver-manager                                                                          #
# or                                                                                                       #
#   conda install -c conda-forge selenium                                                                  #
# Webdriver-manager is no longer needed in Selenium v4 and up.  The driver is now built in Selenium.       #
#   conda install -c conda-forge webdriver-manager                                                         #
#                                                                                                          #
# Run as a process in the background:                                                                      #
#   /> nohup /<...>/jcreyf/stuff/slack_stay_active/slack_active.py 2>&1 > ~/tmp/slack_active.log &         #
# ======================================================================================================== #
#  2018-01-01  v0.1  jcreyf  Initial version                                                               #
#  2022-06-01  v0.2  jcreyf  Lost the old code.  Rewriting and pushing to public GitHub for the fun of it. #
#  2022-06-21  v1.0  jcreyf  This has been running stable for long enough!                                 #
#                            Adding signal handlers to close the web browser when the process is killed.   #
#  2022-06-23  V1.1  jcreyf  Add password encryption.                                                      #
# ======================================================================================================== #
# ToDo:
#   - add system notifications in case there are issues since this app may run in the background:
#     https://github.com/ms7m/notify-py
#
import os
import sys
import time
import yaml
import signal

from datetime import datetime
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Load my own encryption class:
# This needs:
#   conda install pycryptodome
#from ../../secrets import secrets
sys.path.insert(1, "../../secrets")
from secrets import AES_256_CBC

class SlackTimeout(Exception):
    """
    Custom exception to deal with Slack kicking us out whenever its session expires.
    It's doing this to force to re-authenticate every so many days.
    """
    pass


class SlackActive:
    """
    Class to load the Slack web page and click on the message textbox as if the user is ready to start typing.
    The click will set the user state to "active" in Slack.
    This class allows to set a number of seconds after which to auto-repeat the click in the message textbox
    and go in an endless loop and thus keep the user in "active" state.
    """

    __version__ = "v1.1 - 2022-06-23"

    @staticmethod
    def version() -> str:
        """ Static app version details """
        return f"{os.path.basename(__file__)}: {SlackActive.__version__}"


    def __init__(self):
        """ Constructor, initializing properties with default values. """
        self._debug = False                 # Make the web browser visible and print messages in the console to show what's happening;
        self._enabled = True                # Enable click events in the web browser in the Slack page;
        self._click_random = False          # Sleep a random number of seconds between clicks;
        self._click_seconds = 60            # Number of seconds between repeating the clicks;
        self._slack_org_url = ""            # The url of your Slack page that has the message textbox;
        self._slack_workspace = ""          # The name of your Slack Workspace;
        self._slack_username = ""           # Username to log on with in Slack (if needed);
        self._slack_password = ""           # Password of the user to log on with;
        self._encryption_key = ""           # The key that was used to encrypt the password;
        self._webbrowser = None             # Object holding a reference to the web browser;
        self._webbrowser_data_dir = "/tmp"  # The user's data directory for the web browser (where session info is stored)
        self._webbrowser_position = "5,10"  # "X,Y" pixel position of browser window on main desktop;
        self._webbrowser_size = "300,500"   # "width,height" pixel size of browser window;

    def __del__(self):
        """ Destructor will close the web browser and cleanup. """
#        self.end()
        pass

    def end(self):
        """ Method to close the web browser and cleanup resources. """
        self.log("Closing the web browser...")
        try:
            self._webbrowser.quit()
            self._webbrowser = None
        except:
            pass

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, flag: bool):
        self._debug = flag

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, flag: bool):
        self._enabled = flag

    @property
    def clickRandom(self) -> bool:
        return self._click_random

    @clickRandom.setter
    def clickRandom(self, flag: bool):
        self._click_random = flag

    @property
    def clickSeconds(self) -> int:
        return self._click_seconds

    @clickSeconds.setter
    def clickSeconds(self, value: int):
        self._click_seconds = value

    @property
    def slackURL(self) -> str:
        return self._slack_org_url

    @slackURL.setter
    def slackURL(self, value: str):
        self._slack_org_url = value

    @property
    def slackWorkspace(self) -> str:
        return self._slack_workspace

    @slackWorkspace.setter
    def slackWorkspace(self, value: str):
        self._slack_workspace = value

    @property
    def slackUserName(self) -> str:
        return self._slack_username

    @slackUserName.setter
    def slackUserName(self, value: str):
        self._slack_username = value

    @property
    def slackPassword(self) -> str:
        return self._slack_password

    @slackPassword.setter
    def slackPassword(self, value: str):
        self._slack_password = value

    @property
    def encryptionKey(self) -> str:
        return self._encryption_key

    @encryptionKey.setter
    def encryptionKey(self, value: str):
        self._encryption_key = value

    @property
    def webbrowserDataDir(self) -> str:
        return self._webbrowser_data_dir

    @webbrowserDataDir.setter
    def webbrowserDataDir(self, value: str):
        """
        Set the Google Chrome user profile dir:
        (see "Profile Path" when you navigate to "chrome://version" in your browser)
        Mac:   ~/Library/Application Support/Google/Chrome/Default
        Linux: ~/.config/google-chrome/default
        """
# ToDo: should we check if the directory exists?
        self._webbrowser_data_dir = value

    @property
    def webbrowserPosition(self) -> str:
        return self._webbrowser_position

    @webbrowserPosition.setter
    def webbrowserPosition(self, value: str):
# ToDo: should we do some data validation here to make sure we got a valid coordinate?
        self._webbrowser_position = value

    @property
    def webbrowserSize(self) -> str:
        return self._webbrowser_size

    @webbrowserSize.setter
    def webbrowserSize(self, value: str):
# ToDo: should we do some data validation here to make sure we got valid size values?
        self._webbrowser_size = value


    def log(self, msg: str):
        """ Method to log messages.

        We have to assume that this process may be running in the background and that output is piped to
        a log-file.  Because of that, make sure we flush the stdout buffer to keep tails in sync with the
        real world.
        """
        print(f"{datetime.now().strftime('%H:%M:%S')}: {msg}", flush=True)


    def logDebug(self, msg: str):
        if self.debug:
            self.log(f"DEBUG: {msg}")


    def loadConfig(self):
        """ Method to load the config-file for this app.

        We expect the file to be called 'slack_active.yaml' and sit in the same directory as the app.
        The file layout:

            ---
            config:
            # Do not click the mouse if we disable functionality:
            enabled: true
            # Output feedback to the console:
            debug: false
            click:
                # Wait a random number of seconds between clicks:
                random: True
                seconds: 300
            slack:
                org_url: https://app.slack.com/client/<workspace code>/<channel code>
                workspace: <workspace name>
                username: <userID>
                password: <secret>
                encryption_key: <key>
            webbrowser:
                # Directory where the web browser can store session information so that you don't have to log on each time.
                # See "Profile Path" when you navigate to "chrome://version" in your Chrome web browser:
                # on Linux machines:
                data_dir: /home/<user>/.config/google-chrome/Default
                # on Macs:
                data_dir: /Users/<user>/Library/Application Support/Google/Chrome/Default
                # Window position in "x,y" pixel coordinates on screen ("1,1" = top left corner of main display):
                window_position: 5,10
                # Window size in "width,height" pixels:
                window_size: 300,500
        """
        # Figure out this app's directory and add the name of the config-file to load:
        _configFile = f"{os.path.dirname(os.path.realpath(__file__))}/slack_active.yaml"
        self.log(f"Load config: {_configFile}")
        # Load the config file:
        with open(_configFile, "r") as stream:
            try:
                settings = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(e)
                sys.exit(1)

        # Parse the self._debug-flag and set a default if not found:
        try:
            val = settings['config']['debug']
            if not val is None:
                self.debug = val
        except Exception as ex:
            self.logDebug(f"load error! {ex}")

        # Parse the self._enabled-flag and set a default if not found:
        try:
            val = settings['config']['enabled']
            if not val is None:
                self.enabled = val
        except Exception as ex:
            self.log(f"ENABLED load error! {ex}")

        # Parse the random flag and set a default if not found:
        try:
            val = settings['config']['click']['random']
            if not val is None:
                self.clickRandom = val
        except Exception as ex:
            self.log(f"Click Random flag load error! {ex}")

        # Get the max number of seconds between clicks:
        try:
            self._click_seconds = settings['config']['click']['seconds']
            if self.clickSeconds is None:
                self.clickSeconds = 60
        except Exception as ex:
            self.log(f"Click Seconds load error! {ex}")

        # Parse the url to the Slack web page and throw an error if we didn't get it:
        try:
            val = settings['config']['slack']['org_url']
            if val is None:
                raise KeyError("Need a value for 'config.slack.org_url'!")
            else:
                self.slackURL = val
        except KeyError as err:
            self.log("Can't do anything if I don't have the url to your Slack org!")
            self.log("Set it in 'slack_active.yaml'")
            self.log(f"Error: {err}")
            sys.exit(1)

        # Parse the workspace name in the Slack or and throw an error if we didn't get it:
        try:
            val = settings['config']['slack']['workspace']
            if val is None:
                raise KeyError("Need a value for 'config.slack.workspace'!")
            else:
                self.slackWorkspace = val
        except KeyError as err:
            self.log("Can't do anything if I don't have the workspace in your Slack org!")
            self.log("Set it in 'slack_active.yaml'")
            self.log(f"Error: {err}")
            sys.exit(1)

        # Parse the Slack user name and throw an error if we didn't get it:
        try:
            val = settings['config']['slack']['username']
            if val is None:
                raise KeyError("Need a value for 'config.slack.username'!")
            else:
                self.slackUserName = val
        except KeyError as err:
            self.log("Can't do anything if I don't have the username to log on to Slack!")
            self.log("Set it in 'slack_active.yaml'")
            self.log(f"Error: {err}")
            sys.exit(1)

        # Parse the Slack user password and throw an error if we didn't get it:
        try:
            val = settings['config']['slack']['password']
            if val is None:
                raise KeyError("Need a value for 'config.slack.password'!")
            else:
                self.slackPassword = val
        except KeyError as err:
            self.log("Can't do anything if I don't have the password to log on to Slack!")
            self.log("Set it in 'slack_active.yaml'")
            self.log(f"Error: {err}")
            sys.exit(1)

        # Parse the encryption key:
        try:
            val = settings['config']['slack']['encryption_key']
            if not val is None:
                self.encryptionKey = val
        except KeyError as err:
            self.log("Setting for 'Encryption key' load error! {err}")

        # Parse the web browser data directory for the user and throw an error if we didn't get it:
        try:
            val = settings['config']['webbrowser']['data_dir']
            if not val is None:
                self.webbrowserDataDir = val
        except KeyError as err:
            self.log(f"Setting for 'Web browser data directory' load error! {err}")

        # Load the settings for the web browser position on screen:
        try:
            val = settings['config']['webbrowser']['window_position']
            if not val is None:
                self.webbrowserPosition = val
        except KeyError as err:
            self.log(f"Setting for 'Web browser position' load error! {err}")

        # Load the setting for the web browser window size on screen:
        try:
            val = settings['config']['webbrowser']['window_size']
            if not val is None:
                self.webbrowserSize = val
        except KeyError as err:
            self.log(f"Setting for 'Web browser size' load error! {err}")

        # Display the configuration settings:
        self.log(f"Debug: {self.debug}")
        self.log(f"Enabled: {self.enabled}")
        self.log(f"Click random: {self.clickRandom}")
        if self.clickRandom:
            self.log(f"  wait at most {self.clickSeconds} seconds to click")
        else:
            self.log(f"  click every {self.clickSeconds} seconds")
        self.log(f"Slack url: {self.slackURL}")
        self.log(f"Slack workspace: {self.slackWorkspace}")
        self.log(f"Slack user: {self.slackUserName}")
        self.log("Web browser:")
        self.log(f"  data directory: {self.webbrowserDataDir}")
        self.log(f"  window at pos: {self.webbrowserPosition}; width/height: {self.webbrowserSize} pixels")


    def encryptPassword(self, value: str) -> str:
        """ Method to encrypt the Slack credentials.


        """
        cipher = AES_256_CBC(key=self.encryptionKey, verbose=self.debug)
        enc = cipher.encrypt(value)
        self.log(f"key: {self.encryptionKey}")
        self.log(f"String '{value}' encrypts to: '{enc}'")
        self.log(f"decrypts back to: '{cipher.decrypt(enc)}'")
        return enc


    def loadWebBrowser(self):
        """ Method to load the web browser and navigate to the Slack web page.
        
        The web browser will be opened hidden in the background if the config.debug config is set to false (default).
        This method has 2 paths:
          1. the web browser has no session information from a previous run or the session is expired.  In that case
             the code will go through the authentication steps that are needed to get to the page we want;
          2. we do have a valid session and the browser is able to directly navigate to the page we want.  No need
             to authenticate again;
        """
        chrome_options = Options()
        # Find a list of arguments here:
        #   https://peter.sh/experiments/chromium-command-line-switches/
        chrome_options.add_argument(f"window-position={self.webbrowserPosition}")
        chrome_options.add_argument(f"window-size={self.webbrowserSize}")
        # Set the Google Chrome user profile dir.
        # This enables us to save the session information and with that, bypass a bunch of redirection and authentication
        # hoops if we want to run this frequently.  The browser will only force us through the Okta auth when the session
        # expired and we don't have valid cookies.
        # (see "Profile Path" when you navigate to "chrome://version" in your browser)
        #   Mac:   ~/Library/Application Support/Google/Chrome/Default
        #   Linux: ~/.config/google-chrome/default
        chrome_options.add_argument(f"user-data-dir='{self.webbrowserDataDir}'")

        if not self._debug:
            # Run the web browser hidden in the background.
            # Set the option to hide it:
            chrome_options.add_argument("--headless")

        print("Open web browser...")
        # Open the web browser:
        self._webbrowser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        try:
            # Now navigate to the Slack web page and wait for it to be loaded:
            self.logDebug("Load web page...")
            self._webbrowser.get(self.slackURL)
            WebDriverWait(self._webbrowser, timeout=600).until(EC.presence_of_element_located((By.XPATH, "//html")))
        except:
            raise Exception("We got a timeout!  It's taking too long to load the page.")

        # Zoom out to 75%
        self._webbrowser.execute_script(f"document.body.style.zoom='75%'")
        self._webbrowser.refresh()

        # We may already be on the Slack page at this point if we had a valid session and cookies in our Chrome cache.
        # Let's see if we can see the Slack textbox that we use to type a message in:
        # (it might make more sense to simply grep for the CSS selector in the HTML code at this point)
        try:
            WebDriverWait(driver=self._webbrowser, timeout=30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-qa='message_input']")))
            _found = True
        except:
            _found = False

        if not _found:
            # We'll give Selenium search requests up to a minute to respond:
            webwait = WebDriverWait(driver=self._webbrowser, timeout=60)
            # This is not the Slack page yet that we want to see!
            # We need to go through the gates of hell...
            self.logDebug("  Sign in to your workspace...")
            # This is when the "Sign in to your workspace" page comes up:
            #
            #   <input data-qa="signin_domain_input" aria-describedby="domain_hint" aria-invalid="false" 
            #          aria-labelledby="domain_label" aria-required="false" aria-label autocomplete="off" 
            #          class="c-input_text c-input_text--large full_width margin_bottom_100" 
            #          id="domain" name="domain" placeholder="your-workspace" type="text" value>
            # -> nikedigital
            workspace = webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='domain']")))
            workspace.clear()
            workspace.send_keys(self.slackWorkspace)
            # Then click button "Continue":
            #   <button class="c-button c-button--primary c-button--large p-signin_form__aubergine_button full_width 
            #           margin_bottom_150" data-qa="submit_team_domain_button" type="submit">…</button>
            button = webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            button.click()
            self.logDebug("  Sign in to company...")
            # We now moved on to the "Sign in to <company>" page:
            #
            #   <a id="enterprise_member_guest_account_signin_link_..." data-clog-event="WEBSITE_CLICK" 
            #      data-clog-params="click_target=enterprise_member_signin_with_saml_provider" 
            #      href="/sso/saml/start?redir=%2Fr-t16129201079%3Fredir%3D%252Fgantry%252Fauth%2…dca9f47164352ae3ac5ffee99ee7202a9001e8e8440cb1919079614992304&action=login" 
            #      class="btn btn_large sign_in_sso_btn top_margin">
            logon = webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-clog-event='WEBSITE_CLICK']")))
            logon.click()
            self.logDebug("  Enter credentials...")
            # We now moved to the "ID[me] Sign-in Page":
            #
            #   <input type="text" placeholder name="username" id="okta-signin-username" value aria-label 
            #          autocomplete="username" aria-required="true" required>
            # -> jo.creyf@nike.com
            username = webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
            username.clear()
            username.send_keys(self.slackUserName)
            # Decrypt the password:
            cipher = AES_256_CBC(key=self.encryptionKey, verbose=self.debug)
            _decryptedPassword = cipher.decrypt(self.slackPassword)
            #   <input type="password" placeholder name="password" id="okta-signin-password" value aria-label 
            #          autocomplete="current-password" aria-invalid="false" aria-required="true" required>
            # -> secret
            password = webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
            password.clear()
            password.send_keys(_decryptedPassword)
            # Remove the decrypted password from memory:
            del _decryptedPassword
            # Then click "Sign In" button:
            #   <input class="button button-primary" type="submit" value="Sign In" id="okta-signin-submit" data-type="save">
            signin = webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
            signin.click()
            self.logDebug("  Okta verify...")
            # We're now at the "Okta Verify" page:
            #   <label for="input82" data-se-for-name="autoPush" class>Send push automatically</label>
            #
            #   <input class="button button-primary" type="submit" value="Send Push" data-type="save">
            okta_verify = webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
            okta_verify.click()
            # See if we have access to the text input box at the bottom of the page:
            #   <div data-qa="message_input" data-message-input="true" data-channel-id="GEUFXD8AY" data-view-context="message-pane"
            #        data-min-lines="1" class="c-texty_input_unstyled ql-container focus">
            webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-qa='message_input']")))

        self.log("The Slack page is loaded and ready.")


    def clickTextbox(self):
        """ Method to click the message textbox on the Slack web page.

        This will send an even to Slack and set the user status to "active".
        """
        if self._webbrowser is None:
            raise Exception("Web browser not loaded!")

        try:
            # See if we have access to the text input box at the bottom of the page:
            #   <div data-qa="message_input" data-message-input="true" data-channel-id="GEUFXD8AY" data-view-context="message-pane"
            #        data-min-lines="1" class="c-texty_input_unstyled ql-container focus">
            msg_box = WebDriverWait(self._webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-qa='message_input']")))
            self.logDebug("click...")
            msg_box.click()
        except:
            # Something happened to the web page!  We're no longer where we should be!
            # Restart the steps to get to the correct page!
            raise SlackTimeout("The Slack message textbox is not clickable !!")


    def stayActive(self):
        """ Method to loop indefinitely, clicking the message textbox every so many seconds.

        """
        if self._webbrowser is None:
            raise Exception("Web browser not loaded!")

        # Zoom out to 50%
        self._webbrowser.execute_script(f"document.body.style.zoom='50%'")
        self._webbrowser.refresh()
        # We're on the page that we need.  Let's wait and make sure everything is loaded and ready for us to start clicking:
        msg_box = WebDriverWait(self._webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-qa='message_input']")))
        self.logDebug("Slack page loaded and ready...")
        # Loop forever, clicking the textbox every so many seconds:
        _seconds = self.clickSeconds
        while True:
            self.clickTextbox()
            if self.clickRandom:
                _seconds = randint(1, self.clickSeconds)
            time.sleep(_seconds)

# ----

slacker = None

def signal_handler(signum, frame):
    """ Handle CRTL+C and other kill events """
    slacker.log("End of app...")
    # We're cleaning up resources in the finally block in the loop, so there's probably no need to do it here too.
    # The finally block will still execute even if we CTRL-C out of the app.
#    slacker.end()
    exit(0)


if __name__ == "__main__":
    # Set signal handlers to deal with CTRL+C presses and other ways to kill this process.
    # We do this to close the web browser window and cleanup resources:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Define the command-line arguments that the app supports:
    import argparse
    parser=argparse.ArgumentParser(description="Encrypt or Decrypt secrets.")
    parser.add_argument("--version", \
                            action="version", \
                            version=SlackActive.__version__)
    parser.add_argument("-e", "--encrypt", \
                            dest="__ENCRYPT", \
                            required=False, \
                            metavar="<string>", \
                            help="encrypt a string")
    # Parse the command-line arguments:
    __ARGS=parser.parse_args()

    # Run the app.
    # The app may run for days without any problem until at some point Slack expires the session and kicks us out.
    # Slack then basically just wants us to log in again.
    # We can try detect the session timeout and restart the app when that happens to do the auto login and keep going.
    _loop = True
    while _loop:
        try:
            slacker = SlackActive()
            slacker.log("==================")
            slacker.log(slacker.version())
            slacker.loadConfig()
            # See if we need to execute something from the command line arguments:
            if __ARGS.__ENCRYPT:
                slacker.log(f"Need to encrypt: {__ARGS.__ENCRYPT}")
                slacker.encryptPassword(__ARGS.__ENCRYPT)
                exit(0)
            # No 'one of' task to execute.  Load the web browser and do the thing this app was built for:
            slacker.loadWebBrowser()
            slacker.stayActive()
        except SlackTimeout as ex:
            slacker.log(f"Slack kicked us out! -> {ex}")
            slacker.log("restarting...")
        except Exception as ex:
            slacker.log(f"Exception! -> {ex}")
            # Slack did not just kick us out after a while. Do not restart the loop.
            # ToDo: We should add some sort of notification here to let the user know the app is no longer running!!
            _loop = False
        finally:
            slacker.end()