#!/usr/bin/env python3
# ======================================================================================================== #
# Little app to keep me 'active' in Slack ... even when I'm "slacking" ;-)                                 #
#                                                                                                          #
# Arguments:                                                                                               #
#    --encrypt <string> | -e <string>        :encrypt a string so that we can copy/paste it into our yaml  #
#    --key <string> | -k <string>            :optional 2ndary encryption key                               #
#    --test                                  :test the app all the way up to the loading of the webbrowser.#
#                                             This can be helpfull to validate the configuration file.     #
#                                                                                                          #
# -------------------------------------------------------------------------------------------------------- #
# Going with Selenium because we need more than just web scraping.  We need to provide user input as if    #
# the user is interacting with the web pages!                                                              #
#                                                                                                          #
# Install the Selenium and Webdriver Manager packages (see requirements.txt):                              #
# (make sure to have Selenium v4 or greater installed!)                                                    #
#   pip install selenium webdriver-manager cerberus pyyaml pycryptodome                                    #
# or                                                                                                       #
#   conda install -c conda-forge selenium webdriver-manager cerberus pyyaml pycryptodome                   #
#                                                                                                          #
# Run as a process in the background:                                                                      #
#   /> nohup /<...>/jcreyf/stuff/slack_stay_active/slack_active.py 2>&1 > ~/tmp/slack_active.log &         #
# ======================================================================================================== #
#  2018-01-01  v0.1  jcreyf  Initial version                                                               #
#  2022-06-01  v0.2  jcreyf  Lost the old code.  Rewriting and pushing to public GitHub for the fun of it. #
#  2022-06-21  v1.0  jcreyf  This has been running stable for long enough!                                 #
#                            Adding signal handlers to close the web browser when the process is killed.   #
#  2022-06-23  v1.1  jcreyf  Add password encryption.                                                      #
#  2022-07-01  v1.2  jcreyf  Make it possible to select which version of the Chrome web driver to use.     #
#  2022-07-18  v1.3  jcreyf  Make the webpage resize optional (as in ignoring any errors if it fails)      #
#                            Also make the Okta 2FA step optional (adding a check for it and only go       #
#                            go through the 2FA step if it looks like we need it.                          #
#  2022-10-26  v1.4  jcreyf  - add config for activation times (when to set yourself online/offline and on #
#                            what days).  This will make it easier to run the tool as a daemon in the      #
#                            background and still come over believable instead of showing online 24/7      #
#                            every day of the week all year long;                                          #
#                            - make the webpage resize configurable;                                       #
#                            - validate and normalize the config-file;                                     #
#                            - add the '--test' CLI flag to test the app without loading the web page;     #
#  2022-11-04  v1.5  jcreyf  - auto-detect config file changes and auto-reload the app when this happens;  #
#                            - add a 'hidden' flag to the webbrowser configuration.  The 'debug'-flag was  #
#                              used to determine if we should show or hide the window but are moving that  #
#                              to its own flag now;                                                        #
#  2022-11-16  v1.6  jcreyf  - add sending email notifications (sms through text gateways);                #
#                            - save the process ID in a file for easier support from the command line;     #
# ======================================================================================================== #
# ToDo:
#   - add system notifications in case there are issues since this app may run in the background:
#     https://github.com/ms7m/notify-py
#   - get the zoom to work!  The ChromeDriver seems to be ignoring everything I try or is resetting it all
#
import os
import sys
import time
import selenium
import yaml
import signal
import ast
import pprint           # Used to pretty-print the config;
import smtplib, ssl     # Used for email notifications;

from datetime import datetime
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
# We need the webdriver_manager to auto-download drivers:
# This is not a Selenium package!  https://github.com/SergeyPirogov/webdriver_manager
from webdriver_manager.chrome import ChromeDriverManager
# Needed to validate and normalize the config-file:
from cerberus import Validator
# Needed to determine if we should trigger an event based on time-of-day and day-in-year:
from time_exclusions import TimeExclusions
# Needed for email notifications:
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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


class SecurityException(Exception):
    """
    Custom exception to deal with credential issues.
    The given password may fail to decrypt.
    """
    pass


class NotificationTypes:
    """
    Class to hold a list of supported notification types.
    """
    APP_START = 'send_app_start'
    APP_END = 'send_app_end'
    APP_RESTART = 'send_app_restart'
    FIRST_RUN_OF_DAY = 'send_app_first_run_of_day'
    SET_ONLINE = 'send_app_set_online'
    SET_OFFLINE = 'send_app_set_offline'


class SlackActive:
    """
    Class to load the Slack web page and click on the message textbox as if the user is ready to start typing.
    The click will set the user state to "active" in Slack.
    This class allows to set a number of seconds after which to auto-repeat the click in the message textbox
    and go in an endless loop and thus keep the user in "active" state.
    """

    __version__ = "v1.6 - 2022-11-16"

    @staticmethod
    def version() -> str:
        """ Static app version details """
        return f"{os.path.basename(__file__)}: {SlackActive.__version__}"


    def __init__(self):
        """ Constructor, initializing properties with default values. """
        self._configFile = None             # Full path to the config-file;
        self._configDate = None             # Modification date of the config-file;
        self._settings = {}                 # Dictionary with our settings loaded from the config-file;
        self._timeexclusion = None          # Object that decides if the current time is a valid trigger time;
        self._testMode = False              # Is the app running in test mode?
        self._clickPreviousCheck = False    # Did we click during previous time check?


    def __del__(self):
        """ Destructor will close the web browser and cleanup. """
#        self.end()
        pass


    def end(self):
        """ Method to close the web browser and cleanup resources. """
        # Close the webbrowser window (if we have one):
        if hasattr(self, '_webbrowser'):
            self.log("Closing the web browser...")
            try:
                self._webbrowser.quit()
                self._webbrowser = None
            except:
                pass

        # Send a notification that the app is no longer running (not when in test mode):
        if not self.testMode:
            self.notify(msg="The application stopped running!", msg_type=NotificationTypes.APP_END)

        # Try to delete the PID-file (ignore potential issues):
        try:
            os.remove(f"{os.path.dirname(os.path.realpath(__file__))}/slack_active.pid")
        except:
            pass


    @property
    def configFile(self) -> str:
        return self._configFile

    @configFile.setter
    def configFile(self, path: str):
        self._configFile = path


    @property
    def configDate(self) -> time:
        return self._configDate


    @property
    def debug(self) -> bool:
        return self._settings['config']['debug']

    @debug.setter
    def debug(self, flag: bool):
        self._settings['config']['debug'] = flag


    @property
    def enabled(self) -> bool:
        return self._settings['config']['enabled']

    @enabled.setter
    def enabled(self, flag: bool):
        self._settings['config']['enabled'] = flag


    @property
    def testMode(self) -> bool:
        return self._testMode

    testMode.setter
    def testMode(self, flag: bool):
        self._testMode = flag


    @property
    def clickRandom(self) -> bool:
        return self._settings['config']['click']['random']

    @clickRandom.setter
    def clickRandom(self, flag: bool):
        self._settings['config']['click']['random'] = flag


    @property
    def clickSeconds(self) -> int:
        return self._settings['config']['click']['seconds']

    @clickSeconds.setter
    def clickSeconds(self, value: int):
        self._settings['config']['click']['seconds'] = value


    @property
    def slackURL(self) -> str:
        return self._settings['config']['slack']['org_url']

    @slackURL.setter
    def slackURL(self, value: str):
        self._settings['config']['slack']['org_url'] = value


    @property
    def slackWorkspace(self) -> str:
        return self._settings['config']['slack']['workspace']

    @slackWorkspace.setter
    def slackWorkspace(self, value: str):
        self._settings['config']['slack']['workspace'] = value


    @property
    def slackUserName(self) -> str:
        return self._settings['config']['slack']['username']

    @slackUserName.setter
    def slackUserName(self, value: str):
        self._settings['config']['slack']['username'] = value


    @property
    def slackPassword(self) -> str:
        return self._settings['config']['slack']['password']

    @slackPassword.setter
    def slackPassword(self, value: str):
        self._settings['config']['slack']['password'] = value


    @property
    def encryptionKey(self) -> str:
        return self._settings['config']['slack']['encryption_key']

    @encryptionKey.setter
    def encryptionKey(self, value: str):
        self._settings['config']['slack']['encryption_key'] = value


    @property
    def webbrowserDataDir(self) -> str:
        return self._settings['config']['webbrowser']['data_dir']

    @webbrowserDataDir.setter
    def webbrowserDataDir(self, value: str):
        """
        Set the Google Chrome user profile dir:
        (see "Profile Path" when you navigate to "chrome://version" in your browser)
        Mac:   ~/Library/Application Support/Google/Chrome/Default
        Linux: ~/.config/google-chrome/default
        """
# ToDo: should we check if the directory exists?
        self._settings['config']['webbrowser']['data_dir'] = value


    @property
    def webbrowserHidden(self) -> bool:
        return self._settings['config']['webbrowser']['hidden']

    @webbrowserHidden.setter
    def webbrowserHidden(self, flag: bool):
        self._settings['config']['webbrowser']['hidden'] = flag


    @property
    def webbrowserPosition(self) -> str:
        return self._settings['config']['webbrowser']['window_position']

    @webbrowserPosition.setter
    def webbrowserPosition(self, value: str):
# ToDo: should we do some data validation here to make sure we got a valid coordinate?
        self._settings['config']['webbrowser']['window_position'] = value


    @property
    def webbrowserSize(self) -> str:
        return self._settings['config']['webbrowser']['window_size']

    @webbrowserSize.setter
    def webbrowserSize(self, value: str):
# ToDo: should we do some data validation here to make sure we got valid size values?
        self._settings['config']['webbrowser']['window_size'] = value


    @property
    def webbrowserVersion(self) -> str:
        return self._settings['config']['webbrowser']['chrome_version']

    @webbrowserVersion.setter
    def webbrowserVersion(self, value: str):
        self._settings['config']['webbrowser']['chrome_version'] = value


    @property
    def webpageSize(self) -> str:
        return self._settings['config']['webbrowser']['page_size']

    @webpageSize.setter
    def webpageSize(self, value: str):
# ToDo: need to do validation here!
        self._settings['config']['webbrowser']['page_size'] = value


    @property
    def hostname(self) -> str:
        return self._settings['config']['hostname']


    def log(self, msg: str):
        """ Method to log messages.

        We have to assume that this process may be running in the background and that output is piped to
        a log-file.  Because of that, make sure we flush the stdout buffer to keep tails in sync with the
        real world.
        """
        print(f"{datetime.now().strftime('%m/%d %H:%M:%S')}: {msg}", flush=True)


    def logDebug(self, msg: str):
        if self.debug:
            self.log(f"DEBUG: {msg}")


    def saveProcessID(self):
        """ Method to save the PID of this process to a file.
        
        It's sometimes handy to have the process ID for command-line operation.
        We could of course get the PID through the ps-command but why no save it to be sure!?
        """
        try:
            pid_file_path = f"{os.path.dirname(os.path.realpath(__file__))}/slack_active.pid"
            pid = os.getpid()
            with open(pid_file_path, 'w') as pid_file:
                self.log(f"PID: {pid} -> {pid_file_path}")
                pid_file.write(f"{pid}\n")
        except:
            pass


    def loadConfig(self):
        """ Method to load the config-file for this app.

        We expect the file to be called 'slack_active.yaml' and sit in the same directory as the app.
        The file layout:
            ---
            config:
            enabled: true
            debug: false
            hostname: <name>
            click:
                random: True
                seconds: 300
            slack:
                org_url: <url>
                workspace: <workspace name>
                username: <userID>
                password: <secret>
            webbrowser:
                data_dir: <directory>
                hidden: false
                window_position: 5,10
                window_size: 300,500
                page_size: 75%
                chrome_version: "latest"
            times:
                - name: Regular Work Week
                  start: 08:45
                  start_random_minutes: 15
                  stop: 18:00
                  stop_random_minutes: 30
                  days: Mo,Tu,We,Th
                - name: Summer Hours
                  start: 08:45
                  start_random_minutes: 15
                  stop: 13:00
                  stop_random_minutes: 30
                  days: Fr
            exclusions:
                - name: End Year
                  date_from: 2022-12-25
                  date_to: 2023-01-02
                  yearly: true
                - name: PTO
                  date_from: 2022-11-01
                  date_to: 2022-11-01
            notifications:
                - enabled: true
                  email_from: "<email_address>"
                  email_to: "<email_address>"
                  email_subject: "<subject line>"
                  smtp_server: "smtp.gmail.com"
                  smtp_port: 465
                  password: "<secret>"
                  send_app_start: true
                  send_app_end: true
                  send_app_restart: true
                  send_app_first_run_of_day: true
                  send_app_set_online: true
                  send_app_set_offline: true
        """
        # Figure out this app's directory and add the name of the config-file to load:
        self.configFile = f"{os.path.dirname(os.path.realpath(__file__))}/slack_active.yaml"
        self.log(f"Load config: {self.configFile}")
        # Load the config file:
        with open(self.configFile, "r") as stream:
            try:
                _settings = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print("Failed to read the config file!")
                print(e)
                sys.exit(1)
        # Get the modification time of the config-file.
        # We'll use this to detect file changes and dynamically reload the config when it changes.
        self._configDate = os.path.getmtime(self.configFile)

        # Load the schema definition file so that we can validate the config-file:
        # I could have used Pydantic for this but I wanted to do this with Cerberus.
        _configSchemaFile = f"{os.path.dirname(os.path.realpath(__file__))}/config.schema"
        self.log(f"Load schema definition: {_configSchemaFile}")
        with open(_configSchemaFile, 'r') as stream:
            try:
                _config_schema_definition = stream.read()
                # Remove comment-lines and turn the string into a dict:
                # (using eval() could be used too but is not secure since it can execute commands in strings!)
                _config_schema_definition = ast.literal_eval(_config_schema_definition)
            except Exception as e:
                print("Failed to read the config schema definition file!")
                print(e)
                sys.exit(1)

        # Validate the config:
        self.log(f"Validating config...")
        validator = Validator(_config_schema_definition, purge_unknown = True)
        if validator.validate(_settings):
            # The config is fine.  Normalize it to add potential missing optional settings:
            self._settings = validator.normalized(_settings)
        else:
            # The config has issues!
            print("The config has issues!!!")
            print(validator.errors)
            sys.exit(1)

        # Try set the encryption key from either the command-line of from the environment variable
        # if it's not set in the config-file:
        if self.encryptionKey == '':
            if cli_key == None:
                try:
                    self.encryptionKey = os.environ['JC_SECRETS_KEY']
                except Exception as e:
                    self.log("We don't have the encryption key!")
                    self.log("Add it to the config-file or set environment variable: JC_SECRETS_KEY")
                    sys.exit(1)
            else:
                self.encryptionKey = cli_key

        # Set the hostname if it isn't set in the config-file:
        if self.hostname == '':
            self._settings['config']['hostname'] = os.uname()[1]

        # Create an instance of the class that will check for each click if the current time falls within a
        # valid work window:
        self._timeexclusion = TimeExclusions()
        self._timeexclusion.debug=self.debug
        if "times" in self._settings['config']:
            self._timeexclusion.times = self._settings['config']['times']
        if "exclusions" in self._settings['config']:
            self._timeexclusion.exclusions = self._settings['config']['exclusions']
        if self.debug:
            self._timeexclusion.logTimes()
            self._timeexclusion.logExclusions()

        # Display the configuration settings:
        if self.debug:
            self.logDebug(f"Config:\n{pprint.pformat(self._settings)}")

        self.log(f"Host: {self.hostname}")
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
        self.log(f"  hidden: {self.webbrowserHidden}")
        self.log(f"  Chrome version to use: {self.webbrowserVersion}")
        self.log(f"  data directory: {self.webbrowserDataDir}")
        self.log(f"  window at pos: {self.webbrowserPosition}; width/height: {self.webbrowserSize} pixels (webpage size: {self.webpageSize})")


    def encryptPassword(self, value: str, key: str = None) -> str:
        """ Method to encrypt the Slack credentials.

        Arguments:
            value (str): the string to encrypt;
            key (str): the key to encrypt the string with;

        Returns:
            str: the encrypted and encoded string;

        Raises:
            multiple potential exceptions during either the encryption or encoding process;
        """
        cipher = AES_256_CBC(key=self.encryptionKey, verbose=self.debug)
        enc = cipher.encrypt(value)
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
        # Decrypt the credential.
        # Doing this all the way at the beginning since this is a crucial piece that may fail for whatever reason
        # and there's no point if even trying if we don't have decryptable credentials:
        self.logDebug("Get credentials...")
        cipher = AES_256_CBC(key=self.encryptionKey, verbose=self.debug)
        _decryptedPassword = cipher.decrypt(self.slackPassword)
        if _decryptedPassword == None or _decryptedPassword == "":
            raise SecurityException("Failed to decrypt the password!  Is the key set correctly (JC_SECRETS_KEY)?")

        self.logDebug("Configure web browser...")
        chrome_options = Options()
        # Find a list of arguments here:
        #   https://chromedriver.chromium.org/capabilities
        #   https://peter.sh/experiments/chromium-command-line-switches/
        chrome_options.add_argument(f"window-position={self.webbrowserPosition}")
        chrome_options.add_argument(f"window-size={self.webbrowserSize}")
        # 2022-10-27: the ChromeDriver is ignoring these zoom settings:
        chrome_options.add_argument("force-device-scale-factor=0.75")
        chrome_options.add_argument("high-dpi-support=0.75")
        # Set the Google Chrome user profile dir.
        # This enables us to save the session information and with that, bypass a bunch of redirection and authentication
        # hoops if we want to run this frequently.  The browser will only force us through the Okta auth when the session
        # expired and we don't have valid cookies.
        # (see "Profile Path" when you navigate to "chrome://version" in your browser)
        #   Mac:   ~/Library/Application Support/Google/Chrome/Default
        #   Linux: ~/.config/google-chrome/default
        chrome_options.add_argument(f"user-data-dir='{self.webbrowserDataDir}'")
        # Hide the info bar at the top of the window that says:
        #   "Chrome is being controlled by automated test software"
        # (this flag will or may get removed at some point)
        chrome_options.add_argument("--disable-infobars")

        if self.webbrowserHidden:
            # Run the web browser hidden in the background.
            # Set the option to hide it:
            chrome_options.add_argument("--headless")

        self.logDebug("Open web browser...")
        # ChromeDriverManager docs:
        #   https://chromedriver.chromium.org/home
        #   https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
        #   https://github.com/SergeyPirogov/webdriver_manager
        # Download the wanted Chrome web driver (if not present yet on your machine).
        # The WebDriverManager will download some version of the chrome driver if it's not there yet on disk.
        # By default, the version will be 'latest' but we can set it to some specific version if the latest version
        # has bugs and is acting up or is behaving differently for some reason.
        # The driver is by default installed in:
        #   ~/.wdm/drivers/chromedriver/mac64/

        # For some reason, the ChromeDriver download url is different for MacOS vs. Linux.
        # Mac needs to have the version set to 'None' to pull the latest version, while it needs to be: 'latest' for Linux:
        if sys.platform == "linux":
            _chrome_version = "latest"
        else:
            _chrome_version = None

        if not self.webbrowserVersion == "latest":
            _chrome_version = self.webbrowserVersion

        # We need to ignore all this if we're running the app on a Raspberry PI!
        # Google no longer builds ARM versions for the Linux32 platforms, so we can't dynamically download.
        # The Raspbian project has custom built versions that we can install through:
        #   /> sudo apt-get install chromium-chromedriver
        # Simple detection mechanism to see if we're running this on a Pi:
        # (we could also parse the data out of "os.uname()")
        if os.name == 'posix':
            sys.log("Running on a Raspberry PI...")
        else:
            # Run this on non-RPi devices:
            _chrome_service = Service(ChromeDriverManager(version=_chrome_version).install())

        # Open the web browser:
        self._webbrowser = webdriver.Chrome(service=_chrome_service, options=chrome_options)
        # 2022-07-01: The above line started throwing this exception for some dark reason after upgrading to Chrome v103.0.5060.53:
        #             -> unknown error: cannot determine loading status
        #                from unknown error: unexpected command response
        #             The web browser got updated and maybe there was a conflict between my browser and Selenium ChromeDriver?
        #             I updated everything to no avail.  I then added this line to see if that worked ... and YES!  WEIRD!!!
# ToDo: Need to keep debugging and take this out again!
        self._webbrowser.get("file:///")
        try:
            # Now navigate to the Slack web page and wait for it to be loaded:
            self.logDebug(f"Load web page: {self.slackURL}")
            self._webbrowser.get(self.slackURL)
            WebDriverWait(self._webbrowser, timeout=600).until(EC.presence_of_element_located((By.XPATH, "//html")))
        except Exception as err:
            self.logDebug(err)
            raise Exception("We got a timeout!  It's taking too long to load the page.")

        # We may already be on the Slack page at this point if we had a valid session and cookies in our Chrome cache.
        # Let's see if we can see the Slack textbox that we use to type a message in:
        # (it might make more sense to simply grep for the CSS selector in the HTML code at this point)
        try:
            self.logDebug("See if the page has a valid Slack text input box...")
            WebDriverWait(driver=self._webbrowser, timeout=30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-qa='message_input']")))
            _found = True
        except:
            _found = False

        if not _found:
            self.logDebug("We're not on the correct Slack page yet!")
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

            # 2022-07-18: For some dark reason, the 'Sign In' didn't require 2FA through Okta this time!
            #             This means that there are circumstances where the Okta 2FA gets skipped.
            #             Let's just wait for the 2FA page since we almost always have to go through it.
            #             We can determine if we can skip it after we get a timeout and turns out our final
            #             webpage got loaded instead of the 2FA page.
            self.logDebug("  Okta verify...")
            try:
                # We're now at the "Okta Verify" page (most of the time):
                #   <label for="input82" data-se-for-name="autoPush" class>Send push automatically</label>
                #
                #   <input class="button button-primary" type="submit" value="Send Push" data-type="save">
                okta_verify = webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
                # No timeout, so we got the 2FA page.  Click the damn thing!
                okta_verify.click()
            except TimeoutException as te:
                # We're not getting the 2FA page.  Lets see if we got the final page that has the testing input box:
                if EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-qa='message_input']")):
                    self.logDebug("  -> Okta 2FA skipped!")
                else:
                    # Nope, we're not on the final webpage yet.  Raise the TimeOut exception:
                    self.logDebug("TimeOut on the Okta verification step!")
                    raise te

            # See if we have access to the text input box at the bottom of the page:
            #   <div data-qa="message_input" data-message-input="true" data-channel-id="GEUFXD8AY" data-view-context="message-pane"
            #        data-min-lines="1" class="c-texty_input_unstyled ql-container focus">
            webwait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-qa='message_input']")))

        # Resize the webpage
        # 2022-07-18: Ran into this error here since upgrading to Chrome v103.0.5060.114:
        #             -> javascript error: Cannot read properties of null (reading 'style')
        #             The resize is just a nice to have.  Ignoring any potential errors here:
        self.logDebug(f"Resize webpage to: {self.webpageSize}")
        try:
            self._webbrowser.execute_script(f"document.body.style.zoom='{self.webpageSize}'")
            self._webbrowser.refresh()
        except Exception:
            self.logDebug("There was an issue resizing the webpage")

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
            self.logDebug("click!")
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

        # We're on the page that we need.  Let's wait and make sure everything is loaded and ready for us to start clicking:
        msg_box = WebDriverWait(self._webbrowser, timeout=60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-qa='message_input']")))
        self.logDebug("Slack page loaded and ready...")
        # Loop forever, clicking the textbox every so many seconds:
        _seconds = self.clickSeconds
        while True:
            # Click the Slack textbox if we're in a working time window:
            if self._timeexclusion.checkNow():
                self.clickTextbox()
                # Send a notification if state of online vs. offline changes:
                if not self._clickPreviousCheck:
                    self.notify(msg='Setting you online now', msg_type=NotificationTypes.SET_ONLINE)
                self._clickPreviousCheck = True
            else:
                # Send a notification if state of online vs. offline changes:
                if self._clickPreviousCheck:
                    self.notify(msg='Setting you offline now', msg_type=NotificationTypes.SET_OFFLINE)
                self._clickPreviousCheck = False

            # Send a notification if this is the first check of the day.
            # The user can use that notification as sign the app is still running.
            if self._timeexclusion.isNewDay:
                self.notify(msg=self._timeexclusion.dayMessage, msg_type=NotificationTypes.FIRST_RUN_OF_DAY)
            # Check and see if the config-file got updated before we continue.
            # We need to restart with the new config if it changed!
            if self.configFileChanged():
                # Breaking out of this loop will kick us back to the main application loop, which will restart the app:
                break
            # Get a new number of seconds if we need random behavior:
            if self.clickRandom:
                _seconds = randint(1, self.clickSeconds)
            time.sleep(_seconds)


    def configFileChanged(self) -> bool:
        """ Method to check if the config-file changed after starting the app.
        
        We want to auto-restart the app whenever the config-file got updated.
        """
        # Get the current modification time of the config-file and compare to what it was when we loaded the config:
        _configDate = os.path.getmtime(self.configFile)
        if _configDate != self.configDate:
            self.log("The config-file changed.  We need to reload the app!")
            return True


    def notify(self, msg: str, msg_type: str = ''):
        """ Method to send notifications.

        Individual message types can be disabled in the config.
        Supported message types (defined in class: NotificationTypes):
            '' (default) -> generic message
            'send_app_start'
            'send_app_end'
            'send_app_restart'
            'send_app_first_run_of_day'
            'send_app_set_online'
            'send_app_set_offline'
        """
        # Only continue if we have notification mechanisms configured:
        if self._settings['config']['notifications'] != None:
            # We have configuration(s).  Loop through them and see if we have one for email:
            for notification_method in self._settings['config']['notifications']:
                # Individual message types can be enabled/disabled.  Determine that flag here:
                if msg_type == '':
                    type_enabled = True
                else:
                    type_enabled = notification_method[msg_type]
                # Send a notification if enabled:
                if notification_method['enabled'] and type_enabled:
                    if "email_to" in notification_method.keys():
                        self.sendEmail(notification_method, msg)


    def sendEmail(self, config: dict, msg: str):
        """ Method to send emails.
        
        This method is specifically setup to send email through Google Mail.
        Make sure to have an "Application Password" generated for this app.  See:
          https://support.google.com/accounts/answer/185833?visit_id=638036529563689035-1605844469&p=InvalidSecondFactor&rd=1
        """
        self.log("Sending notification email...")
        try:
            context = ssl.create_default_context()
            # Decrypt the credential:
            cipher = AES_256_CBC(key=self.encryptionKey, verbose=self.debug)
            _decryptedPassword = cipher.decrypt(config['password'])
            if _decryptedPassword == None or _decryptedPassword == "":
                raise SecurityException("Failed to decrypt the email password!  Is the key set correctly (JC_SECRETS_KEY)?")

            message = MIMEMultipart("alternative")
            message["Subject"] = f'{config["email_subject"]} - {self.hostname}'
            message["From"] = config['email_from']
            message["To"] = config['email_to']

            _text = f"""\
            {msg}
            Host: {self.hostname}
            """

            msg = msg.replace("\n", "<br>")
            _html = f"""\
            <html>
            <body>
                <p><b>{msg}</b><br>
                Host: {self.hostname}</p>
            </body>
            </html>
            """

            # Add HTML/plain-text parts to MIMEMultipart message.
            # The email client will try to render the last part first.
            message.attach(MIMEText(_text, "plain"))
            message.attach(MIMEText(_html, "html"))

            with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], context=context) as emailServer:
                emailServer.login(config['email_from'], _decryptedPassword)
                emailServer.sendmail(from_addr=config['email_from'], \
                                    to_addrs=config['email_to'], \
                                    msg=message.as_string())
        except Exception as e:
            # Not being able to send a notification is not critical!  Just log the issue:
            self.log(f"Failed to send notification:\n{msg}")
            self.log(f"The exception -> {str(ex)}")
        finally:
            del _decryptedPassword


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
    parser.add_argument("--test", \
                            action="store_true", \
                            help="Test the app without opening a webbrowser and accessing Slack")
    parser.add_argument("-e", "--encrypt", \
                            dest="__ENCRYPT", \
                            required=False, \
                            metavar="<string>", \
                            help="encrypt a string")
    parser.add_argument("-k", "--key", \
                            dest="__KEY", \
                            required=False, \
                            metavar="<string>", \
                            help="encryption key (you can also set env var 'JC_SECRETS_KEY')")
    # Parse the command-line arguments:
    __ARGS=parser.parse_args()

    # Pull out the values that we want:
    encrypt=__ARGS.__ENCRYPT
    cli_key=__ARGS.__KEY
    TEST=__ARGS.test

    if TEST:
        print("** TEST MODE **")

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
            slacker.saveProcessID()
            slacker.testMode = TEST
            slacker.loadConfig()
            # See if we need to execute something from the command line arguments:
            if encrypt:
                slacker.log(f"Need to encrypt: {encrypt}")
                if cli_key != None:
                    slacker.encryptionKey=cli_key
                print(slacker.encryptPassword(encrypt))
                exit(0)
            # No 'one of' task to execute.  Load the web browser and do the thing this app was built for:
            # (if we're not in TEST mode)
            if slacker.testMode:
                # TEST mode goes through all steps of the app up to the opening of the webbrowser.
                # So don't do that here and exit out of the loop:
                _loop = False
                # Test the time exclusion check:
                slacker.log("Test time exclusions...")
                flag = slacker._timeexclusion.checkTime(datetime.now())
                slacker.log(f"timeCheck: {flag}")
                # Test notifications:
                slacker.log("Sending a test notification...")
                slacker.notify("This is a test")
            else:
                slacker.loadWebBrowser()
                slacker.stayActive()
        except SlackTimeout as ex:
            slacker.log(f"Slack kicked us out! -> {ex}")
            slacker.log("restarting...")
            slacker.notify(msg=f"Slack kicked us out!\n-> {type(ex)}: {ex}\nAuto-restarting the tool now...", msg_type='send_app_restart')
        except Exception as ex:
            slacker.log(f"Exception! -> {type(ex)}: {ex}")
            slacker.notify(msg=f"The app ran into a non-recoverable exception!\n-> {type(ex)}: {ex}\nI can't auto-restart!  YOU NEED TO LOOK INTO THIS AND MANUALLY RESTART THE TOOL!!!")
            # Slack did not just kick us out after a while. Do not restart the loop.
            # It may be that decryption of the credential failed.
            # ToDo: We should add some sort of notification here to let the user know the app is no longer running!!
            _loop = False
        finally:
            slacker.end()