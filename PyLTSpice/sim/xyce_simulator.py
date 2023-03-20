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
# Name:        xyce_simulator.py
# Purpose:     Tool used to launch NGspice simulations in batch mode.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     14-03-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

import logging
import sys
import os

from pathlib import Path
from typing import Union

from .simulator import Simulator, run_function


class XyceSimulator(Simulator):
    """Stores the simulator location and command line options and runs simulations."""

    _args = {
        # TODO: Complete this list
    }

    @classmethod
    def get_default_simulator(cls):
        """Searches on the any usual locations for a simulator"""
        raise FileNotFoundError("A suitable exe file was not found. Please locate the spice simulator "
                                "executable and pass it to the SimCommander object by using the 'create_from()'"
                                " class method.")

    @classmethod
    def valid_switch(cls, switch, path='') -> bool:
        """
        Validates a command line switch. The following options are available for Xyce:

            * 'raw' : Specifies a raw file


        :param switch: switch to be added. If the switch is not on the list above, it should be correctly formatted with
        the preceding '-' switch
        :type switch: str
        :param path: path to the file related to the switch being given.
        :type path: str, optional
        :return: Nothing
        :rtype: None
        """
        if switch in cls._args:
            switches = cls._args[switch]
            switches = [switch.replace('<path>', path) for switch in switches]
            return switches
        else:
            raise ValueError("Invalid swich for class ")

    @classmethod
    def run(cls, netlist_file, cmd_line_switches, timeout):
        cmd_run = cls.spice_exe + ['-b'] + [netlist_file] + cmd_line_switches
        # start execution
        return run_function(cmd_run, timeout=timeout)


