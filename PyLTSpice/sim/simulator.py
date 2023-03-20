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
    """Pure static class template for Spice simulators. This class only defines the interface of the subclasses.
    The variables below shall be overridden by the subclasses. Instantiating this class will raise a TypeError
    exception.
    """
    spice_exe = []
    process_name = ""

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
                cls.process_name = plib_path_to_exe.stem
            else:
                cls.process_name = plib_path_to_exe.name
            cls.spice_exe = [plib_path_to_exe.as_posix()]
            return cls
        else:
            raise FileNotFoundError(f"Provided exe file was not found '{path_to_exe}'")

    def __init__(self, spice_exe: list, process_name: str):
        raise TypeError("This is a pure abstract class merely for the purposes of giving the programmer a guideline.")

    @classmethod
    @abstractmethod
    def run(cls, netlist_file, cmd_line_switches, timeout):
        """This method implements the call for the simulation of the netlist file. This should be overriden by its
        subclass"""
        raise NotImplementedError("This method must be overriden in a subclass")

    @classmethod
    @abstractmethod
    def valid_switch(cls, switch, switch_param) -> bool:
        """This method validates that a switch exist and is valid. This should be overriden by its subclass."""
        raise NotImplementedError("This method must be overriden in a subclass")
