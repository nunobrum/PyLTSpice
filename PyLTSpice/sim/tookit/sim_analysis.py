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

    def __init__(self, circuit_file: Union[str, BaseEditor], simulator: Optional[Simulator] = None,
                 runner: Optional[AnyRunner] = None):
        if isinstance(circuit_file, str):
            from ..editor.spice_editor import SpiceEditor
            self.editor = SpiceEditor(circuit_file)
        else:
            self.editor = circuit_file
        if simulator is None:
            from ..sim.ltspice_simulator import LTspice
            self.simulator = LTspice()
        else:
            self.simulator = simulator
        if runner is None:
            from ..sim.sim_runner import SimRunner
            self.runner = SimRunner(parallel_sims=1, timeout=None, verbose=False, output_folder=None)
        self.simulations = OrderedDict()

