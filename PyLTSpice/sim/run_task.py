#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        run_task.py
# Purpose:     Class used for a spice tool using a process call
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-12-2016
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
"""
Internal classes not to be used directly by the user
"""
__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2023, Fribourg Switzerland"

from pathlib import Path
import sys
import threading
import time
import traceback
from time import sleep
from typing import Callable, Union, Any, Tuple, Type
import logging
_logger = logging.getLogger("PyLTSpice.RunTask")

from .process_callback import ProcessCallback
from .simulator import Simulator

END_LINE_TERM = '\n'

if sys.version_info.major >= 3 and sys.version_info.minor >= 6:
    clock_function = time.perf_counter
else:
    clock_function = time.clock


def format_time_difference(time_diff):
    """Formats the time difference in a human readable format, stripping the hours or minutes if they are zero"""
    seconds_difference = int(time_diff)
    milliseconds = int((time_diff - seconds_difference) * 1000)
    hours, remainder = divmod(seconds_difference, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours == 0:
        if minutes == 0:
            return f"{int(seconds):02d}.{milliseconds:04d} secs"
        else:
            return f"{int(minutes):02d}:{int(seconds):02d}.{milliseconds:04d}"
    else:
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.{milliseconds:04d}"


class RunTask(threading.Thread):
    """This is an internal Class and should not be used directly by the User."""

    def __init__(self, simulator: Simulator, runno, netlist_file: Path,
                 callback: Union[Type[ProcessCallback], Callable[[Path, Path], Any]],
                 switches, timeout=None, verbose=True):
        super().__init__(name=f"RunTask#{runno}")
        self.start_time = None
        self.stop_time = None
        self.verbose = verbose
        self.switches = switches
        self.timeout = timeout  # Thanks to Daniel Phili for implementing this
        self.simulator = simulator
        self.runno = runno
        self.netlist_file = netlist_file
        self.callback = callback
        self.retcode = -1  # Signals an error by default
        self.raw_file = None
        self.log_file = None
        self.callback_return = None

    def print_info(self, logger_fun, message):
        message = f"RunTask #{self.runno}:{message}"
        logger_fun(message)
        if self.verbose:
            print(f"{time.asctime()} {logger_fun.__name__}: {message}{END_LINE_TERM}")

    def run(self):
        # Running the Simulation

        self.start_time = clock_function()
        self.print_info(_logger.info, ": Starting simulation %d" % self.runno)

        # start execution
        self.retcode = self.simulator.run(self.netlist_file.absolute().as_posix(), self.switches, self.timeout)
        self.stop_time = clock_function()
        # print simulation time with format HH:MM:SS.mmmmmm

        # Calculate the time difference
        sim_time = format_time_difference(self.stop_time - self.start_time)
        # Format the time difference
        self.log_file = self.netlist_file.with_suffix('.log')

        # Cleanup everything
        if self.retcode == 0:
            # simulation successful
            self.print_info(_logger.info, "Simulation Successful. Time elapsed: %s" % sim_time)
            self.raw_file = self.netlist_file.with_suffix('.raw')

            if self.raw_file.exists() and self.log_file.exists():
                if self.callback:
                    self.print_info(_logger.info, "Simulation Finished. Calling...{}(rawfile, logfile)".format(
                            self.callback.__name__))
                    try:
                        return_or_process = self.callback(self.raw_file, self.log_file)
                    except Exception as err:
                        error = traceback.format_tb(err.__traceback__)
                        self.print_info(_logger.error, error)
                    else:
                        if isinstance(return_or_process, ProcessCallback):
                            proc = return_or_process
                            proc.start()
                            self.callback_return = proc.queue.get()
                            proc.join()
                        else:
                            self.callback_return = return_or_process
                    finally:
                        callback_start_time = self.stop_time
                        self.stop_time = clock_function()
                        self.print_info(_logger.info, "Callback Finished. Time elapsed: %s" % format_time_difference(
                                self.stop_time - callback_start_time))
                else:
                    self.print_info(_logger.info, 'Simulation Finished. No Callback function given')
            else:
                self.print_info(_logger.error, "Simulation Raw file or Log file were not found")
        else:
            # simulation failed
            self.print_info(_logger.warning, ": Simulation Failed. Time elapsed: %s" % sim_time)
            if self.log_file.exists():
                self.log_file = self.log_file.replace(self.log_file.with_suffix('.fail'))

    def get_results(self) -> Union[None, Any, Tuple[str, str]]:
        """
        Returns the simulation outputs if the simulation and callback function has already finished.
        If the simulation is not finished, it simply returns None. If no callback function is defined, then
        it returns a tuple with (raw_file, log_file). If a callback function is defined, it returns whatever
        the callback function is returning.
        """
        if self.is_alive():
            return None

        if self.retcode == 0:  # All finished OK
            if self.callback:
                return self.callback_return
            else:
                return self.raw_file, self.log_file
        else:
            return '', ''

    def wait_results(self) -> Union[Any, Tuple[str, str]]:
        """
        Waits for the completion of the task and returns a tuple with the raw and log files.
        :returns: Tuple with the path to the raw file and the path to the log file
        :rtype: tuple(str, str)
        """
        while self.is_alive() or self.retcode == -1:
            sleep(0.1)
        return self.get_results()
