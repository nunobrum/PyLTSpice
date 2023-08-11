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

from ...sim.sim_runner import AnyRunner
from ...editor.base_editor import BaseEditor
from ...sim.simulator import Simulator


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
        Runs the simulations. See runner.run for details on keyword arguments.
        """
        sim = self.runner.run(self.editor, **kwargs)
        self.simulations.append(sim)

    @wraps(BaseEditor.reset_netlist)
    def reset_netlist(self):
        self.editor.reset_netlist()
        self.num_runs = 0
