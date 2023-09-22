# -*- coding: utf-8 -*-
import json
import time
from typing import List, Any, Callable
from datetime import datetime
from contextlib import contextmanager

from ballet.executor.logger.debug_logger import log, log_once

"""
.. module:: executor_utils
   :synopsis: this file contains utility classes.
"""


class Messages:
    """
    This class is not instantiated. It is used for valid, warning, and fail
    color-printed messages.
    """

    @staticmethod
    def ok():
        return '\033[1;30;42m'

    @staticmethod
    def warning():
        return '\033[1;30;43m'

    @staticmethod
    def fail():
        return '\033[1;30;41m'

    @staticmethod
    def endc():
        return '\033[0m'


# global list of colors used for printing colors of components
COLORS = ['\33[35m',  # magenta
          '\33[36m',  # cyan
          '\33[31m',  # red
          '\33[32m',  # green
          '\33[33m',  # yellow
          '\33[34m',  # blue
          ]


class Printer:
    def __init__(self, show: bool = True):
        self._show = show

    def tprint(self, message: str, flush: bool = False):
        if self._show:
            self.st_tprint(message, flush)

    def err_tprint(self, message: str, flush: bool = True):
        if self._show:
            self.st_err_tprint(message, flush)

    @staticmethod
    def _format_tprint(message: str):
        now = datetime.now()
        hour = ("%d" % now.hour).rjust(2, '0')
        minute = ("%d" % now.minute).rjust(2, '0')
        second = ("%d" % now.second).rjust(2, '0')
        ms = ("%d" % (now.microsecond / 1000)).rjust(3, '0')
        return "[%s:%s:%s:%s] %s" % (hour, minute, second, ms, message)

    @staticmethod
    def st_tprint(message: str, flush: bool = False):
        from sys import stdout
        formatted_message = Printer._format_tprint(message)
        log.debug(formatted_message)
        if flush:
            stdout.flush()

    @staticmethod
    def print(message: str):
        log.debug(message)

    @staticmethod
    def st_err_tprint(message: str, flush: bool = True):
        from sys import stderr
        formatted_message = Printer._format_tprint(message)
        log.error(formatted_message)
        if flush:
            stderr.flush()


class TimeManager:
    """
    Used to exit an assembly when the time is up
    """
    def __init__(self, waiting_rate):
        self.waiting_rate = float(waiting_rate)
        self.duration = None
        self.initial_ending_time = None
        self.waiting_rate_ending_time = None

    def start(self, duration: float):
        self.duration = duration  # TODO: see if it's useful to set it
        self.initial_ending_time = time.time() + duration
        self.waiting_rate_ending_time = time.time() + duration * self.waiting_rate

    def get_time_left(self):
        return round(self.initial_ending_time - time.time(), 2)

    def is_initial_time_up(self):
        return self.initial_ending_time <= time.time()

    def is_waiting_rate_time_up(self):
        return self.waiting_rate_ending_time <= time.time()


def remove_if(l: List[Any], remove_cond: Callable[[Any], bool]):
    i = 0
    while i < len(l):
        if remove_cond(l[i]):
            del l[i]
            continue
        i += 1


def empty_transition():
    pass


@contextmanager
def timeout(time):
    import signal
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError


class GoingSleepingException(Exception):
    def __init__(self):
        super(GoingSleepingException, self).__init__()


node_num_assembly_name = ["server", "dep0", "dep1", "dep2", "dep3", "dep4", "dep5", "dep6", "dep7", "dep8", "dep9", "dep10", "dep11"]


class TimeCheckerAssemblies:
    def __init__(self, uptimes_nodes_file_path):
        self.start_time = None
        self.min_uptime = None
        with open(uptimes_nodes_file_path) as f:
            self.uptime_nodes = json.load(f)

    def set_start_time(self):
        self.start_time = time.time()

    def set_min_uptime(self, min_uptime):
        self.min_uptime = min_uptime

    def is_node_awake_now(self, component_name, round_reconf):
        log_once.debug(f"Checking if node for assembly {component_name} is up")
        uptime, duration = self.uptime_nodes[node_num_assembly_name.index(component_name)][round_reconf]
        seconds_elapsed = self.get_seconds_elapsed()
        if uptime <= seconds_elapsed <= (uptime + duration):
            log_once.debug(f"Node {component_name} is up. Current time: {int(seconds_elapsed)}. Times awakening: {uptime} - {uptime + duration}")
            return True
        log_once.debug(f"Node {component_name} is not up. Current time: {int(seconds_elapsed)}. Times awakening: {uptime} - {uptime + duration}")
        return False

    def get_seconds_elapsed(self):
        return time.time() - self.start_time + self.min_uptime
