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
# Name:        simulator.py
# Purpose:     Creates a virtual class for representing all Spice Simulators
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-12-2016
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

import sys
from abc import ABC, abstractmethod
from pathlib import Path
import subprocess

if sys.version_info.major >= 3 and sys.version_info.minor >= 6:
    def run_function(command, timeout=None):
        result = subprocess.run(command, timeout=timeout)
        return result.returncode

else:
    def run_function(command, timeout=None):
        return subprocess.call(command, timeout=timeout)

class Simulator(ABC):

    @classmethod
    @abstractmethod
    def get_default_simulator(cls):
        """This method needs to be overriden by the sub-class. It should return a simulator executable that can be
        passed into the subprocess run method"""
        raise NotImplementedError("This method should be overriden by a subclass. And that class be used.")

    @classmethod
    def create_from(cls, path_to_exe):
        """
        Creates a simulator class from a path to the simulator executable
        :param path_to_exe:
        :type path_to_exe: pathlib.Path or str
        :return: a class instance representing the Spice simulator
        :rtype: LTspiceSimulator
        """
        plib_path_to_exe = Path(path_to_exe)
        if plib_path_to_exe.exists():
            if sys.platform == 'darwin':
                process_name = plib_path_to_exe.stem
            else:
                process_name = plib_path_to_exe.name
            return cls([plib_path_to_exe.as_posix()], process_name)
        else:
            raise FileNotFoundError(f"Provided exe file was not found '{path_to_exe}'")

    def __init__(self, spice_exe, process_name):
        """This is a generic initialization for this class. It may be overriden, but it should be always invoked by
        the superclass."""
        if not isinstance(spice_exe, list):
            raise TypeError("spice_exe must be a list of strings that can be passed into the subprocess call")

        self.spice_exe = spice_exe
        self.cmdline_switches = []
        self.process_name = process_name

    def clear_command_line_switches(self):
        """Clear all the command line switches added previously"""
        self.cmdline_switches.clear()

    def add_command_line_switch(self, switch, path=''):
        """
        Adds a command line switch to the spice tool command line call.

        :param switch: switch to be added.
        :type switch: str
        :param path: path to the file related to the switch being given.
        :type path: str, optional
        :return: Nothing
        :rtype: None
        """
        self.cmdline_switches.append(switch)
        if path is not None:
            self.cmdline_switches.append(path)


    def run(self, netlist_file, timeout):
        """This method implements the call for the simulation of the netlist file. This should be overriden by its
        subclass"""
        ...



