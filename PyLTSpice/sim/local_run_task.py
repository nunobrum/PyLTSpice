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
import os
from pathlib import Path
import threading
import time
import traceback
from time import sleep
from typing import Callable, Union, Any, Tuple
from warnings import warn

from .simulator import clock_function, Simulator

END_LINE_TERM = '\n'

logging.basicConfig(filename='SpiceBatch.log', level=logging.INFO)


class RunTask(threading.Thread):
    """This is an internal Class and should not be used directly by the User."""

    def __init__(self, simulator: Simulator, run_no, netlist_file: 'Path', callback: Callable[['Path', 'Path'], Any],
                 timeout=None, verbose=True):
        self.start_time = None
        self.verbose = verbose
        self.timeout = timeout  # Thanks to Daniel Phili for implementing this

        threading.Thread.__init__(self)
        self.setName("sim%d" % run_no)
        self.simulator = simulator
        self.run_no = run_no
        self.netlist_file = netlist_file
        self.callback = callback
        self.retcode = -1  # Signals an error by default
        self.raw_file = None
        self.log_file = None

    def run(self):
        # Setting up
        logger = logging.getLogger("sim%d" % self.run_no)
        logger.setLevel(logging.INFO)

        # Running the Simulation

        self.start_time = clock_function()
        if self.verbose:
            print(time.asctime(), ": Starting simulation %d" % self.run_no)

        # start execution
        self.retcode = self.simulator.run(self.netlist_file, self.timeout)

        # print simulation time
        sim_time = time.strftime("%H:%M:%S", time.gmtime(clock_function() - self.start_time))
        self.log_file = self.netlist_file.with_suffix('.log')

        # Cleanup everything
        if self.retcode == 0:
            # simulation successful
            logger.info("Simulation Successful. Time elapsed: %s" % sim_time)
            if self.verbose:
                print(time.asctime() + ": Simulation Successful. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))

            self.raw_file = self.netlist_file.with_suffix('.raw')

            if self.raw_file.exists() and self.log_file.exists():
                if self.callback:
                    if self.verbose:
                        print("Simulation Finished. Calling...{}(rawfile, logfile)".format(self.callback.__name__))
                    try:
                        self.callback(self.raw_file, self.log_file)
                    except Exception as err:
                        error = traceback.format_tb(err)
                        logger.error(error)
                else:
                    if self.verbose:
                        print('Simulation Finished. No Callback function given')
            else:
                logger.error("Simulation Raw file or Log file were not found")
        else:
            # simulation failed

            logger.warning(time.asctime() + ": Simulation Failed. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))
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


