import os
from datetime import datetime

class TimeExclusions:
    """
    Class to check if the current time falls within a valid trigger window.
    If there's no time window configured, then we assume that all days are 24/7 trigger days.
    """

    __version__ = "v1.0 - 2022-11-03"

    @staticmethod
    def version() -> str:
        """ Static app version details """
        return f"{os.path.basename(__file__)}: {TimeExclusions.__version__}"


    def __init__(self, times: dict, exclusions: dict):
        """ Constructor, initializing properties with default values. """
        self._days = ["Mo","Tu","We","Th","Fr","Sa","Su"]
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
        return self.checkTime(datetime.now())


    def checkTime(self, timestamp: datetime) -> bool:
        dayOfWeek = self._days[timestamp.weekday()]
        self.logDebug(f"Check: {timestamp.strftime('%m/%d %H:%M:%S')} - weekday: {dayOfWeek}")
        # Check if this day falls in an 'exclusions' windows:
        if self._exclusions != None and len(self._exclusions) > 0:
            # We have 'exclusions' configuration, so we can't assume all weeks are the same.
            # See if the date falls in an exclusion window:
            self.logDebug("Checking 'exclusion' windows...")
            for _exclusion in self._exclusions:
                # We need to strip off the year from the date if this exclusion happens yearly:
                if _exclusion['yearly']:
                    self.logDebug("This is a yearly exclusion")

                if _exclusion['date_from'] <= timestamp.date() <= _exclusion['date_to']:
                    # This is an exclusion day on which we don't work!
                    self.logDebug(f"'{timestamp.date()}' falls in exclusion window: '{_exclusion['name']}'")
                    return False
            self.logDebug("Not an exclusion day")

        # Check the time of day against the 'times' configurations:
        if self._times == None or len(self._times) == 0:
            # We don't have any 'times' configuration, so we need to assume 24/7 operation:
            self.logDebug("There are no 'times' configurations, so all days are valid 24/7")
            return True

        self.logDebug("Checking 'times' windows...")
        found_before = False
        timeWindow = None
        for _time in self._times:
            if dayOfWeek in _time['days']:
                if found_before:
                    self.log(f"WARNING: We have multiple 'times' configurations for the same weekday '{dayOfWeek}'! ('{_time['name']}')")
                else:
                    timeWindow = _time
                    self.logDebug(f"day found in times config: '{_time['name']}' ({_time['days']})")
                    found_before = True

        if timeWindow == None:
            # We didn't find a time window config for this date!
            # We do have configurations for other days though, so we need to assume there's no operation on this specific weekday.
            self.logDebug("This is not a work day!")
            return False
        else:
            # We have a valid time window config to check.
            # Convert the time strings to time objects:
            _time = timestamp.time()
            _start = datetime.strptime(timeWindow['start'], '%H:%M').time()
            _stop = datetime.strptime(timeWindow['stop'], '%H:%M').time()
            self.logDebug(f"Compare '{_time}' against '{_start}' and '{_stop}'")
            # Now figure out where the time to check falls within the day:
            if _time < _start:
                self.logDebug("time is before start time!")
                return False
            else:
                if _time > _stop:
                    self.logDebug("time is past stop time!")
                    return False
                else:
                    self.logDebug("time is during work hours")
                    return True