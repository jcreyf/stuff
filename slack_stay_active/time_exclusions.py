import os
from datetime import datetime

class TimeExclusions:
    """
    Class to check if the current time falls within a valid trigger window.
    """

    __version__ = "v1.0 - 2022-11-03"

    @staticmethod
    def version() -> str:
        """ Static app version details """
        return f"{os.path.basename(__file__)}: {TimeExclusions.__version__}"


    def __init__(self, times: dict, exclusions: dict):
        """ Constructor, initializing properties with default values. """
        self._debug = False                 # Debug logging level;
        self._times = times                 # Dictionary with date/time windows;
        self._exclusions = exclusions       # Dictionary with date exclusion windows;


    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, flag: bool):
        self._debug = flag


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


    def logTimes(self):
        # Did we get 'times'?
        if len(self._times) > 0:
            for time_range in self._times:
                self.log(f"Time Range: {time_range['name']}")
                self.log(f"  start time: {time_range['start']} (random {time_range['start_random_minutes']} min)")
                self.log(f"  stop time: {time_range['stop']} (random {time_range['stop_random_minutes']} min)")
                self.log(f"  week days: {time_range['days']}")
        else:
            self.log("No 'times' configured.  Using defaults (24/7)")


    def logExclusions(self):
        # Did we get any 'exclusions'?
        if len(self._exclusions) > 0:
            for exclusion in self._exclusions:
                self.log(f"Exclusion: {exclusion['name']}")
                self.log(f"  from: {exclusion['date_from']}")
                self.log(f"  to: {exclusion['date_to']}")
                if 'yearly' in exclusion.keys():
                    self.log(f"  yearly: {exclusion['yearly']}")
                else:
                    self.log(f"  yearly: No")
        else:
            self.log("No runtime 'exclusions'.")


    def checkNow(self) -> bool:
        self.logDebug(f"Check now: {datetime.now().strftime('%m/%d %H:%M:%S')}")
        return True
