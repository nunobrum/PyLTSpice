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
# Name:        ngspice_simulator.py
# Purpose:     Tool used to launch NGspice simulations in batch mode.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-02-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

from pathlib import Path

from .simulator import Simulator, run_function


class NGspiceSimulator(Simulator):
    """Stores the simulator location and command line options and runs simulations."""
    spice_exe = ["C:/Apps/NGSpice64/bin/ngspice.exe"]
    process_name = "ngspice.exe"
    ngspice_args = {
        '-a'            : ['-a'],
        '--autorun'     : ['--autorun'],  # run the loaded netlist
        '-b'            : ['-b'],
        '--batch'       : ['--batch'],  # process FILE in batch mode
        '-c'            : ['-c', '<FILE>'],  #
        '--circuitfile' : ['--circuitfile', '<FILE>'],  # set the circuitfile
        '-D'            : ['-D', 'var_value'],  #
        '--define'      : ['--define', 'var_value'],  # define variable to true/[value]
        '-i'            : ['-i'],  #
        '--interactive' : ['--interactive'],  # run in interactive mode
        '-n'            : ['-n'],  #
        '--no-spiceinit': ['--no-spiceinit'],  # don't load the local or user's config file
        '-o'            : ['-o', '<FILE>'],  #
        '--output'      : ['--output', '<FILE>'],  # set the outputfile
        '-p'            : ['-p'],  #
        '--pipe'        : ['--pipe'],  # run in I/O pipe mode
        '-q'            : ['-q'],  #
        '--completion'  : ['--completion'],  # activate command completion
        '-r'            : ['-r'],  #
        '--rawfile'     : ['--rawfile', '<FILE>'],  # set the rawfile output
        '--soa-log'     : ['--soa-log', '<FILE>'],  # set the outputfile for SOA warnings
        '-s'            : ['-s'],  #
        '--server'      : ['--server'],  # run spice as a server process
        '-t'            : ['-t', '<TERM>'],  #
        '--term'        : ['--term', '<TERM>'],  # set the terminal type
        '-h'            : ['-h'],  #
        '--help'        : ['--help'],  # display this help and exit
        '-v'            : ['-v'],  #
        '--version'     : ['--version'],  # output version information and exit
    }
    default_run_switches = ['-b', '-o', '-r', '-a']

    @classmethod
    def valid_switch(cls, switch, parameter='') -> list:
        """
        Validates a command line switch. The following options are available for NGSpice:

        :param switch: switch to be added. If the switch is not on the list above, it should be correctly formatted with
                    the preceding '-' switch
        :type switch: str
        :param parameter: parameter for the switch
        :type parameter: str, optional
        :return: the correct formatting for the switch
        :rtype: list
        """
        ret = []  # This is an empty switch
        if switch in cls.ngspice_args:
            if switch in cls.default_run_switches:
                print(f"Switch {switch} is already in the default switches")
                return ret
            switch_list = cls.ngspice_args[switch]
            if len(switch_list) == 2:
                param_token = switch_list[1]
                if param_token == '<FILE>':
                    ret = [switch_list[0], parameter]
                elif param_token == '<TERM>':
                    ret = [switch_list[0], parameter]
                else:
                    print(f"Invalid parameter {parameter} for switch '{switch}'")
            else:
                ret = switch_list
        else:
            print(f"Invalid Switch {switch}")
        return ret

    @classmethod
    def run(cls, netlist_file, cmd_line_switches, timeout):
        logfile = Path(netlist_file).with_suffix('.log').as_posix()
        rawfile = Path(netlist_file).with_suffix('.raw').as_posix()
        cmd_run = cls.spice_exe + cmd_line_switches + ['-b'] + ['-o'] + [logfile] + ['-r'] + [rawfile] + [netlist_file]
        # start execution
        return run_function(cmd_run, timeout=timeout)


