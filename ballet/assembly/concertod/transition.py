#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. module:: transition
   :synopsis: this file contains the Transition class.
"""

import threading

from ballet.executor.logger.time_logger import log_time_value, TimestampType, TimestampPeriod


class Transition:
    """This Transition class is used to create a transition.

        A transition is an action, represented by the 'run' function. This
        action is performed between a source and destination dock, each of
        which is attached to a place.

        This is an abstract class that need to be override. In particular,
        the method 'run' must be override
    """

    """
    BUILD TRANSITION
    """

    def __init__(self, name, src, dst, bhv, idset, func, args, component):
        self.transition_name = name
        self.src_place = None
        if src is not None:
            self.src_place = src.get_name()
        self.dst_place = dst.get_name()
        self.behavior = bhv
        self.dst_idset = idset  # TODO: what is it
        self.code = func
        self.args = args
        self._component = component
        self.src_dock = None
        if src is not None:
            self.src_dock = src.create_output_dock(self)
        self.dst_dock = dst.create_input_dock(self)
        self.thread = None

    @property
    def obj_id(self):
        return f"{self._component.name}_{self.transition_name}"

    def to_json(self):
        return {
            "transition_name": self.transition_name
        }

    def set_name(self, name):
        """
        This method set the name of the transition

        :param name: tha name (string) to set
        """
        self.transition_name = name

    def get_name(self):
        """
        This method returns the name of the transition

        :return: name (string)
        """
        return self.transition_name

    def get_dst_idset(self):
        return self.dst_idset

    def get_src_dock(self):
        """
        This method returns the source dock of the transition

        :return: the source dock self.src_dock
        """
        return self.src_dock

    def get_dst_dock(self):
        """
        This method returns the destination dock of the transition

        :return: the destination dock self.dst_dock
        """
        return self.dst_dock

    def get_behavior(self):
        """
        This method returns the behavior of the transition

        :return: behavior (string)
        """
        return self.behavior

    def execute_user_function(self, user_function, arguments):
        try:
            log_time_value(TimestampType.TRANSITION, TimestampPeriod.START, user_function.__name__)
            user_function(*arguments)
            log_time_value(TimestampType.TRANSITION, TimestampPeriod.END, user_function.__name__)
        except Exception as e:
            self._component.thread_safe_report_error(self, repr(e))

    def start_thread(self, gantt_tuple, dryrun):
        """
        This method creates the thread of the transition

        :return: the Thread of the transition
        """
        if not dryrun:
            self.thread = threading.Thread(target=self.execute_user_function, args=(self.code, self.args))
            if gantt_tuple is not None:
                (gantt_chart, args) = gantt_tuple
                gantt_chart.start_transition(*args)
            self.thread.start()
        else:
            pass

    def join_thread(self, gantt_tuple, dryrun):
        """
        This method tries to join self.thread. The default behavior has no
        timeout.

        :return: True if the tread has been joined, False othwise
        """
        if not dryrun:
            if not self.thread.is_alive():
                self.thread.join()
                if gantt_tuple is not None:
                    (gantt_chart, args) = gantt_tuple
                    gantt_chart.stop_transition(*args)
                return True
            else:
                return False
        else:
            return True
