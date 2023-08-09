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
# Created:     23-12-2016
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

from collections import OrderedDict
from typing import Iterable, Union, Optional

from .sim_runner import AnyRunner
from ..editor.base_editor import BaseEditor, ComponentNotFoundError
from ..sim.simulator import Simulator


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


class FailureMode(SimAnalysis):
    """
    This Class will replace each component on the circuit for their failure modes and launch a simulation.

    The following failure modes are built-in:

        * Resistors, Capacitors, Inductors and Diodes
            # Open Circuit
            # Short Circuit

        * Transistors
            # Open Circuit (All pins)
            # Short Circuit (All pins)
            # Short Circuit Base-Emitter (Bipolar) / Gate-Source (MOS)
            # Short Circuit Collector-Emitter (Bipolar) / Drain-Source (MOS)

        * Integrated Circuits
            # The failure modes are defined by the user by using the add_failure_mode() method
    """
    def __init__(self, circuit_file: Union[str, BaseEditor], simulator: Optional[Simulator] = None,
                 runner: Optional[AnyRunner] = None):
        SimAnalysis.__init__(self, circuit_file, simulator, runner)
        self.resistors = self.editor.get_components('R')
        self.capacitors = self.editor.get_components('C')
        self.inductors = self.editor.get_components('L')
        self.diodes = self.editor.get_components('D')
        self.bipolars = self.editor.get_components('Q')
        self.mosfets = self.editor.get_components('M')
        self.subcircuits = self.editor.get_components('X')
        self.user_failure_modes = OrderedDict()

    def add_failure_circuit(self, component, sub_circuit):
        if not component.startswith('X'):
            raise RuntimeError("The failure modes addition only works with sub circuits")
        if component not in self.subcircuits:
            raise ComponentNotFoundError()
        raise NotImplementedError("TODO")  # TODO: Implement this

    def add_failure_mode(self, component, short_pins: Iterable, open_pins: Iterable):
        if not component.startswith('X'):
            raise RuntimeError("The failure modes addition only works with subcircuits")
        if component not in self.subcircuits:
            raise ComponentNotFoundError()
        raise NotImplementedError("TODO")  # TODO: Implement this

    def run_all(self):
        for resistor in self.resistors:
            # Short Circuit
            self.editor.set_component_value(resistor, '1f')  # replaces the resistor with a one femto-Ohm
            self.simulations[f"{resistor}_S"] = self.simulator.run()
            # Open Circuit
            self.editor.remove_component(resistor)
            self.simulations[f"{resistor}_O"] = self.simulator.run()
            self.editor.reset_netlist()

        for two_pin_comps in (self.capacitors, self.inductors, self.diodes):
            for two_pin_component in two_pin_comps:
                # Open Circuit
                cinfo = self.editor.get_component_info(two_pin_component)
                self.editor.remove_component(two_pin_component)
                self.simulations[f"{two_pin_component}_O"] = self.simulator.run()
                # Short Circuit
                self.editor.netlist[cinfo['line']] = f"Rfmea_short_{two_pin_component}{cinfo['nodes']} 1f"
                self.simulations[f"{two_pin_component}_S"] = self.simulator.run()
                self.editor.reset_netlist()
