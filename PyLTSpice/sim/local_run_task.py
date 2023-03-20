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
# Name:        local_run_task.py
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

import logging
from pathlib import Path
import sys
import threading
import time
import traceback
from time import sleep
from typing import Callable, Union, Any, Tuple


from .simulator import Simulator

END_LINE_TERM = '\n'

logging.basicConfig(filename='SpiceBatch.log', level=logging.INFO)

if sys.version_info.major >= 3 and sys.version_info.minor >= 6:
    clock_function = time.process_time
else:
    clock_function = time.clock


class RunTask(threading.Thread):
    """This is an internal Class and should not be used directly by the User."""

    def __init__(self, simulator: Simulator, runno, netlist_file: Path, callback: Callable[[Path, Path], Any],
                 switches, timeout=None, verbose=True):
        super().__init__(name=f"RunTask#{runno}")
        self.start_time = None
        self.stop_time = None
        self.verbose = verbose
        self.switches = switches
        self.timeout = timeout  # Thanks to Daniel Phili for implementing this

        threading.Thread.__init__(self)
        self.setName("sim%d" % runno)
        self.simulator = simulator
        self.runno = runno
        self.netlist_file = netlist_file
        self.callback = callback
        self.retcode = -1  # Signals an error by default
        self.raw_file = None
        self.log_file = None
        self.callback_return = None

    def print_info(self, logger_fun, message):
        logger_fun(message)
        if self.verbose:
            print(f"{time.asctime()} {logger_fun.__name__}: {message}", end=END_LINE_TERM)

    def run(self):
        # Setting up
        logger = logging.getLogger("sim%d" % self.runno)
        logger.setLevel(logging.INFO)

        # Running the Simulation

        self.start_time = clock_function()
        self.print_info(logger.info, ": Starting simulation %d" % self.runno)

        # start execution
        self.retcode = self.simulator.run(self.netlist_file, self.switches, self.timeout)
        self.stop_time = clock_function()
        # print simulation time
        sim_time = time.strftime("%H:%M:%S", time.gmtime(self.stop_time - self.start_time))
        self.log_file = self.netlist_file.with_suffix('.log')

        # Cleanup everything
        if self.retcode == 0:
            # simulation successful
            self.print_info(logger.info, "Simulation Successful. Time elapsed: %s" % sim_time)
            self.raw_file = self.netlist_file.with_suffix('.raw')

            if self.raw_file.exists() and self.log_file.exists():
                if self.callback:
                    self.print_info(logger.info, "Simulation Finished. Calling...{}(rawfile, logfile)".format(self.callback.__name__))
                    try:
                        self.callback_return = self.callback(self.raw_file, self.log_file)
                    except Exception as err:
                        error = traceback.format_tb()
                        self.print_info(logger.error, error)
                else:
                    self.print_info(logger.info, 'Simulation Finished. No Callback function given')
            else:
                self.print_info(logger.error, "Simulation Raw file or Log file were not found")
        else:
            # simulation failed
            self.print_info(logger.warning, ": Simulation Failed. Time elapsed: %s" % sim_time)
            if self.log_file.exists():
                self.log_file = self.log_file.replace(self.log_file.with_suffix('.fail'))

    def wait_results(self) -> Tuple[str, str]:
        """
        Waits for the completion of the task and returns a tuple with the raw and log files.
        :returns: Tupple with the path to the raw file and the path to the log file
        :rtype: tuple(str, str)
        """
        while self.is_alive() or self.retcode == -1:
            sleep(0.1)
        if self.retcode == 0:  # All finished OK
            return self.raw_file, self.log_file
        else:
            return '', ''


