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
# Name:        sim_analysis.py
# Purpose:     Classes to automate Monte-Carlo, FMEA or Worst Case Analysis
#              be updated by user instructions
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     06-07-2021
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

from collections import OrderedDict
from functools import wraps
from typing import Union, Optional

from ..sim_runner import AnyRunner
from ..simulator import Simulator
from ...editor.base_editor import BaseEditor
from ...log.ltsteps import LTSpiceLogReader
from ...log.logfile_data import LogfileData


class SimAnalysis(object):
    """
    Base class for making Monte-Carlo, Extreme Value Analysis (EVA) or Failure Mode and Effects Analysis.
    As a base class, a certain number of assertions must be made on the simulation results that will make the pass/fail.

    Note: For the time being only measurements done with .MEAS are possible. At a later stage the parsing of RAW files
    will be possible, although, it seems that the later solution is less computing intense.
    """

    def __init__(self, circuit_file: Union[str, BaseEditor], runner: Optional[AnyRunner] = None):
        if isinstance(circuit_file, str):
            from ...editor.spice_editor import SpiceEditor
            self.editor = SpiceEditor(circuit_file)
        else:
            self.editor = circuit_file
        self._runner = runner
        self.simulations = []
        self.num_runs = 0

    @property
    def runner(self):
        if self._runner is None:
            from ...sim.sim_runner import SimRunner
            self._runner = SimRunner()
        return self._runner

    @runner.setter
    def runner(self, new_runner: AnyRunner):
        self._runner = new_runner

    def run(self, **kwargs):
        """
        Runs the simulations. See runner.run() method for details on keyword arguments.
        """
        sim = self.runner.run(self.editor, **kwargs)
        if sim is not None:
            self.simulations.append(sim)
            self.runner.wait_completion()
            if 'callback' in kwargs:
                return sim.get_results()

    @wraps(BaseEditor.reset_netlist)
    def reset_netlist(self):
        self.editor.reset_netlist()

    def cleanup_files(self):
        """Clears all simulation files. Typically used after a simulation run and analysis."""
        self.runner.file_cleanup()

    def simulation(self, index: int):
        """Returns a simulation object"""
        return self.simulations[index]

    def __getitem__(self, item):
        return self.simulations[item]

    def read_logfiles(self) -> LogfileData:
        """Reads the log files and returns a dictionary with the results"""
        all_stepset = {}
        all_dataset = OrderedDict()
        for sim in self.simulations:
            if sim is None:
                continue
            log_results = LTSpiceLogReader(sim.log_file)
            for param in log_results.stepset:
                if param not in all_stepset:
                    all_stepset[param] = log_results.stepset[param]
                else:
                    all_stepset[param].extend(log_results.stepset[param])
            for param in log_results.dataset:
                if param not in all_dataset:
                    all_dataset[param] = log_results.dataset[param]
                else:
                    all_dataset[param].extend(log_results.dataset[param])
        # Now reusing the last log_results object to store the results
        return LogfileData(all_stepset, all_dataset)

