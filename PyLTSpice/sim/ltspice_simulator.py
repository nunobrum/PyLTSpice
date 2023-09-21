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
# Name:        ltspice_simulator.py
# Purpose:     Represents a LTspice tool and it's command line options
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-12-2016
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import sys
import os

from pathlib import Path
from typing import Union
import logging
_logger = logging.getLogger("PyLTSpice.LTSpiceSimulator")

from .simulator import Simulator, run_function


class LTspice(Simulator):
    """Stores the simulator location and command line options and is responsible for generating netlists and running
    simulations."""

    """Searches on the any usual locations for a simulator"""
    if sys.platform == "linux":
        spice_folder = os.environ.get("LTSPICEFOLDER")
        spice_executable = os.environ.get("LTSPICEEXECUTABLE")

        if spice_folder and spice_executable:
            spice_exe = ["wine", os.path.join(spice_folder, spice_executable)]
            process_name = spice_executable
        elif spice_folder:
            spice_exe = ["wine", os.path.join(spice_folder, "/XVIIx64.exe")]
            process_name = "XVIIx64.exe"
        elif spice_executable:
            default_folder = os.path.expanduser(
                "~/.wine/drive_c/Program Files/LTC/LTspiceXVII"
            )
            spice_exe = ["wine", os.path.join(default_folder, spice_executable)]
            process_name = spice_executable
        else:
            default_folder = os.path.expanduser(
                "~/.wine/drive_c/Program Files/LTC/LTspiceXVII"
            )
            spice_exe = ["wine", os.path.join(default_folder, "XVIIx64.exe")]
            process_name = "XVIIx64.exe"
    elif sys.platform == "darwin":
        spice_exe = ['/Applications/LTspice.app/Contents/MacOS/LTspice']
        process_name = "XVIIx64"
    else:  # Windows
        for exe in (  # Placed in order of preference. The first to be found will be used.
                os.path.expanduser(r"~\AppData\Local\Programs\ADI\LTspice\LTspice.exe"),
                r"C:\Program Files\ADI\LTspice\LTspice.exe",
                r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe",
                r"C:\Program Files (x86)\LTC\LTspiceIV\scad3.exe",  # Legacy LTspice IV
        ):
            if os.path.exists(exe):
                _logger.debug(f"Using LTspice installed in : '{exe}' ")
                spice_exe = [exe]
                break
        else:
            spice_exe = []
            _logger.error("================== ALERT! ====================")
            _logger.error("Unable to find a LTSpice executable.")
            _logger.error("A specific location of the LTSPICE can be set")
            _logger.error("using the create_from(<location>) class method")
            _logger.error("==============================================")

        process_name = "XVIIx64.exe"

    ltspice_args = {
        'alt' : ['-alt'],  # Set solver to Alternate.
        'ascii'     : ['-ascii'],  # Use ASCII.raw files. Seriously degrades program performance.
        # 'batch': ['-b <path>'], # Used by run command: Run in batch mode.E.g. "ltspice.exe-b deck.cir" will leave the data infile deck.raw
        'big'       : ['-big'],  # Start as a maximized window.
        'encrypt'   : ['-encrypt'],
        # Encrypt a model library.For 3rd parties wishing to allow people to use libraries without
        # revealing implementation details. Not used by AnalogDevices models.
        'fastaccess': ['-FastAccess'],  # Batch conversion of a binary.rawfile to Fast Access format.
        'FixUpSchematicFonts': ['-FixUpSchematicFonts'],
                       # Convert the font size field of very old user - authored schematic text to the modern default.
        'FixUpSymbolFonts': ['-FixUpSymbolFonts'],
                       # Convert the font size field of very old user - authored symbols to the modern default.
                       # See Changelog.txt for application hints.

        'ini'       : ['- ini', '<path>'],  # Specify an .ini file to use other than %APPDATA%\LTspice.ini
        'I'   : ['-I<path>'],  # Specify a path to insert in the symbol and file search paths.
                                     # Must be the last specified option.
                                     # No space between "-I" and < path > is allowed.
        'max'       : ['-max'],  # Synonym for -big
        'netlist'   : ['-netlist'],  # Batch conversion of a schematic to a netlist.
        'norm'      : ['-norm'],  # Set solver to Normal.
        'PCBnetlist': ['-PCBnetlist'],  # Batch conversion of a schematic to a PCB format netlist.
        #'run'       : ['-Run', '-b', '{path}'],  # Start simulating the schematic opened on the command line without
        #                                         # pressing the Run button.
        'SOI'       : ['-SOI'],  # Allow MOSFET's to have up to 7 nodes even in subcircuit expansion.
        'sync'      : ['-sync'],  # Update component libraries
        'uninstall' : ['-uninstall'],  # Please don't. Executes one step of the uninstallation process.

    }

    @classmethod
    def valid_switch(cls, switch, path='') -> list:
        """
        Validates a command line switch. The following options are available for LTSpice:

            * 'alt' : Set solver to Alternate.

            * 'ascii'     : Use ASCII.raw files. Seriously degrades program performance.

            * 'encrypt'   : Encrypt a model library.For 3rd parties wishing to allow people to use libraries without
                            revealing implementation details. Not used by AnalogDevices models.

            * 'fastaccess': Batch conversion of a binary.rawfile to Fast Access format.

            * 'FixUpSchematicFonts' : Convert the font size field of very old user - authored schematic text to the
                                    modern default.

            * 'FixUpSymbolFonts' : Convert the font size field of very old user - authored symbols to the modern
                default. See Changelog.txt for application hints.

            * 'ini <path>' : Specify an .ini file to use other than %APPDATA%\LTspice.ini

            * 'I<path>' : Specify a path to insert in the symbol and file search paths. Must be the last specified
                option.

            * 'netlist'   :  Batch conversion of a schematic to a netlist.

            * 'normal'    :  Set solver to Normal.

            * 'PCBnetlist':  Batch conversion of a schematic to a PCB format netlist.

            * 'SOI'       :  Allow MOSFET's to have up to 7 nodes even in subcircuit expansion.

            * 'sync'      : Update component libraries

            * 'uninstall' :  Executes one step of the uninstallation process. Please don't.


        :param switch: switch to be added. If the switch is not on the list above, it should be correctly formatted with
                       the preceding '-' switch
        :type switch: str
        :param path: path to the file related to the switch being given.
        :type path: str, optional
        :return: Nothing
        :rtype: None
        """
        if switch in cls.ltspice_args:
            switches = cls.ltspice_args[switch]
            switches = [switch.replace('<path>', path) for switch in switches]
            return switches
        else:
            raise ValueError("Invalid switch for class ")

    @classmethod
    def run(cls, netlist_file, cmd_line_switches, timeout):
        if sys.platform == 'darwin':
            cmd_run = cls.spice_exe + ['-b'] + [netlist_file] + cmd_line_switches
        else:
            cmd_run = cls.spice_exe + ['-Run'] + ['-b'] + [netlist_file] + cmd_line_switches
        # start execution
        return run_function(cmd_run, timeout=timeout)

    @classmethod
    def create_netlist(cls, circuit_file: Union[str, Path]) -> Path:
        # prepare instructions, two stages used to enable edits on the netlist w/o open GUI
        # see: https://www.mikrocontroller.net/topic/480647?goto=5965300#5965300
        circuit_file = Path(circuit_file)
        if sys.platform == 'darwin':
            NotImplementedError("In this platform LTSpice doesn't have netlist generation capabilities")
        cmd_netlist = cls.spice_exe + ['-netlist'] + [circuit_file.as_posix()] + cmd_line_switches
        # print(f'Creating netlist file from "{circuit_file}"', end='...')
        error = run_function(cmd_netlist)

        if error == 0:
            netlist = circuit_file.with_suffix('.net')
            if netlist.exists():
                _logger.debug("OK")
                return netlist
        msg = "Failed to create netlist"
        # print(msg)
        _logger.error(msg)
        raise RuntimeError(msg)
