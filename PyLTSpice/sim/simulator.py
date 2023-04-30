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
        """Normalizing OS subprocess function calls between different platforms. This function is used for python 3.6
        and higher versions."""
        result = subprocess.run(command, timeout=timeout)
        return result.returncode

else:
    def run_function(command, timeout=None):
        """Normalizing OS subprocess function calls between different platforms. This is the old function that was used
        for python version prior to 3.6"""
        return subprocess.call(command, timeout=timeout)


class SpiceSimulatorError(Exception):
    """Generic Simulator Error Exceptions"""
    ...


class Simulator(ABC):
    """Pure static class template for Spice simulators. This class only defines the interface of the subclasses.
    The variables below shall be overridden by the subclasses. Instantiating this class will raise a SpiceSimulatorError
    exception.

    A typical subclass for a Windows installation is:

    .. code-block:: python

        class MySpiceWindowsInstallation(Simulator):
            spice_exe = ['<path to your own ltspice installation>']
            process_name = "<name of the process on Windows Task Manager>"


    or on a Linux distribution:

    .. code-block:: python

        class MySpiceLinuxInstallation(Simulator):
            spice_exe = ['<wine_command', '<path to your own ltspice installation>']
            process_name = "<name of the process>"


    The subclasses should then implement at least the run() function as a classmethod.
    
    .. code-block:: python
        
        @classmethod
        def run(cls, netlist_file, cmd_line_switches, timeout):
            '''This method implements the call for the simulation of the netlist file. '''
            cmd_run = cls.spice_exe + ['-Run'] + ['-b'] + [netlist_file] + cmd_line_switches
            return run_function(cmd_run, timeout=timeout)


    The ``run_function()`` can be imported from the simulator.py with
    ``from PyLTSpice.sim.simulator import run_function`` instruction.
    """
    spice_exe = []
    process_name = ""

    @classmethod
    def create_from(cls, path_to_exe, process_name=None):
        """
        Creates a simulator class from a path to the simulator executable
        :param path_to_exe:
        :type path_to_exe: pathlib.Path or str
        :param process_name: assigning a process_name to be used for killing phantom processes
        :return: a class instance representing the Spice simulator
        :rtype: LTspice
        """
        plib_path_to_exe = Path(path_to_exe)
        if plib_path_to_exe.exists():
            if process_name is None:
                if sys.platform == 'darwin':
                    cls.process_name = plib_path_to_exe.stem
                else:
                    cls.process_name = plib_path_to_exe.name
            else:
                cls.process_name = process_name
            cls.spice_exe = [plib_path_to_exe.as_posix()]
            return cls
        else:
            raise FileNotFoundError(f"Provided exe file was not found '{path_to_exe}'")

    def __init__(self):
        raise SpiceSimulatorError("This class is not supposed to be instanced.")

    @classmethod
    @abstractmethod
    def run(cls, netlist_file, cmd_line_switches, timeout):
        """This method implements the call for the simulation of the netlist file. This should be overriden by its
        subclass."""
        ...

    @classmethod
    @abstractmethod
    def valid_switch(cls, switch, switch_param) -> list:
        """This method validates that a switch exist and is valid. This should be overriden by its subclass."""
        ...
