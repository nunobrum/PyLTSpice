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
# Name:        qspice_simulator.py
# Purpose:     Represents QSPICE
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     26-08-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import sys
import os

from pathlib import Path
import logging
_logger = logging.getLogger("PyLTSpice.QSpiceSimulator")

from .simulator import Simulator, run_function


class Qspice(Simulator):
    """Stores the simulator location and command line options and is responsible for generating netlists and running
    simulations."""

    """Searches on the any usual locations for a simulator"""
    if sys.platform == "linux":
        raise NotImplementedError("QSPICE is not available for Linux")
    elif sys.platform == "darwin":
        raise NotImplementedError("QSPICE is not available for MacOS")
    else:  # Windows
        for exe in (  # Placed in order of preference. The first to be found will be used.
                os.path.expanduser(r"~\AppData\Local\Programs\Qspice\QSPICE64.exe"),
                r"C:\Program Files\QSPICE\QSPICE64.exe",
        ):
            if os.path.exists(exe):
                _logger.debug(f"Using Qspice installed in : '{exe}' ")
                spice_exe = [exe]
                break
        else:
            spice_exe = []
            _logger.error("================== ALERT! ====================")
            _logger.error("Unable to find the QSPICE executable.")
            _logger.error("A specific location of the LTSPICE can be set")
            _logger.error("using the create_from(<location>) class method")
            _logger.error("==============================================")

        process_name = "QSPICE64.exe"

    qspice_args = {
        'ASCII'     : ['-ASCII'],  # Use ASCII file format for the output data(.qraw) file.
        'binary'    : ['-binary'],  # Use binary file format for the output data(.qraw) file.
        'BSIM1'    : ['-BSIM1'],  # Use the charge-conserving BSIM1 charge model for MOS1, MOS2, and MOS3.
        'Meyer'    : ['-Meyer'],  # Use the Meyer Capacitance model for MOS1, MOS2, and MOS3.
        'o'         : ['-o', '<path>'],  # Specify the name of a file for the console output.
        # 'p'         : ['-p'],  # Take the netlist piped from stdin. Not used in this implementation.
        'ProtectSelections': ['-ProtectSelections', '<path>'],  # Protect sections marked with .prot/.unprot with encryption.
        'ProtectSubcircuits': ['-ProtectSubcircuits', '<path>'],  # Protect the body of subcircuits with encryption.
        'r'       : ['-r', '<path>'],  # Specify the name of the output data(.qraw) file.
    }

    @classmethod
    def valid_switch(cls, switch, path='') -> list:
        """
        Validates a command line switch. The following options are available for QSPICE:
            * 'ASCII': Use ASCII file format for the output data(.qraw) file.

            * 'binary': Use binary file format for the output data(.qraw) file.

            * 'BSIM1': Use the charge-conserving BSIM1 charge model for MOS1, MOS2, and MOS3.

            * 'Meyer': Use the Meyer Capacitance model for MOS1, MOS2, and MOS3.

            * 'o <path>': Specify the name of a file for the console output.

            * 'ProtectSelections <path>': Protect sections marked with .prot/.unprot with encryption.

            * 'ProtectSubcircuits <path>': Protect the body of subcircuits with encryption.

            * 'r <path>': Specify the name of the output data(.qraw) file.


        :param switch: switch to be added. If the switch is not on the list above, it should be correctly formatted with
                       the preceding '-' switch
        :type switch: str
        :param path: path to the file related to the switch being given.
        :type path: str, optional
        :return: Nothing
        :rtype: None
        """
        if switch in cls.qspice_args:
            switches = cls.qspice_args[switch]
            switches = [switch.replace('<path>', path) for switch in switches]
            return switches
        else:
            raise ValueError("Invalid switch for class ")

    @classmethod
    def run(cls, netlist_file, cmd_line_switches, timeout):
        raw_file = Path(netlist_file).with_suffix('.raw').as_posix()
        log_file = Path(netlist_file).with_suffix('.log').as_posix()
        cmd_run = cls.spice_exe + ['-o', log_file] + ['-r', raw_file] + [netlist_file] + cmd_line_switches
        # start execution
        return run_function(cmd_run, timeout=timeout)

