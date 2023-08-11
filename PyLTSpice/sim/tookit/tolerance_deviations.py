#!/usr/bin/env python
# coding=utf-8
from dataclasses import dataclass
from typing import Union, Optional, Dict

from editor.base_editor import BaseEditor
# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        montecarlo.py
# Purpose:     Classes to automate Monte-Carlo simulations
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     10-08-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

from .sim_analysis import SimAnalysis, AnyRunner, Simulator
from enum import Enum


class DeviationType(Enum):
    """Enum to define the type of deviation"""
    tolerance = 'tolerance'
    minmax = 'minmax'


@dataclass
class ComponentDeviation:
    """Class to store the deviation of a component"""
    max_val: float
    min_val: float = 0.0
    typ: DeviationType = DeviationType.tolerance
    distribution: str = 'uniform'

    @classmethod
    def from_tolerance(cls, tolerance: float, distribution: str = 'uniform'):
        return cls(tolerance, -tolerance, DeviationType.tolerance, distribution)

    @classmethod
    def from_min_max(cls, min_val: float, max_val: float, distribution: str = 'uniform'):
        return cls(min_val, max_val, DeviationType.minmax, distribution)


class ToleranceDeviations(SimAnalysis):
    """Class to automate Monte-Carlo simulations"""
    devices_with_deviation_allowed = ('R', 'C', 'L', 'V', 'I')

    def __init__(self, circuit_file: Union[str, BaseEditor], runner: Optional[AnyRunner] = None):
        super().__init__(circuit_file, runner)
        self.default_tolerance = {prefix: ComponentDeviation(0) for prefix in self.devices_with_deviation_allowed}
        self.device_deviations: Dict[str, ComponentDeviation] = {}
        self.parameter_deviations: Dict[str, ComponentDeviation] = {}
        self.testbench_prepared = False
        self.num_runs = 0

    def set_tolerance(self, ref: str, new_tolerance: float, distribution: str = 'uniform'):
        """
        Sets the tolerance for a given component. If only the prefix is given, the tolerance is set for all.
        The valid prefixes that can be used are: R, C, L, V, I
        """
        if ref in self.devices_with_deviation_allowed:
            self.default_tolerance[ref] = ComponentDeviation.from_tolerance(new_tolerance, distribution)
        else:
            if ref in self.editor.get_components(ref[0]):
                self.device_deviations[ref] = ComponentDeviation.from_tolerance(new_tolerance, distribution)

    def set_tolerances(self, new_tolerances: dict, distribution: str = 'uniform'):
        """
        Sets the tolerances for a set of components. The dictionary keys are the references and the values are the
        tolerances. If only the prefix is given, the tolerance is set for all components with that prefix. See
        set_tolerance method.
        """
        for ref, tol in new_tolerances.items():
            self.set_tolerance(ref, tol, distribution)

    def set_deviation(self, ref: str, min_val, max_val: float, distribution: str = 'uniform'):
        """
        Sets the deviation for a given component. This establishes a min and max value for the component.
        Optionally a distribution can be specified. The valid distributions are: uniform or normal (gaussian).
        """
        self.device_deviations[ref] = ComponentDeviation.from_min_max(min_val, max_val, distribution)

    def get_components(self, prefix: str):
        if prefix == '*':
            return (cmp for cmp in self.editor.get_components() if cmp[0] in self.devices_with_deviation_allowed)
        return self.editor.get_components(prefix)

    def get_component_value_deviation_type(self, ref: str) -> (float, ComponentDeviation):
        if ref[0] not in self.devices_with_deviation_allowed:
            raise ValueError("The reference must be a valid component type")
        value = self.editor.get_component_value(ref)
        if len(value) == 0:  # This covers empty strings
            return value, ComponentDeviation.from_tolerance(0.0)
        if ref in self.device_deviations:
            return value, self.device_deviations[ref]
        elif ref[0] in self.default_tolerance:
            return value, self.default_tolerance[ref[0]]
        else:
            return value, ComponentDeviation.from_tolerance(0.0)

    def set_component_value(self, ref: str, new_value: str):
        self.editor.set_component_value(ref, new_value)

    def set_parameter_deviation(self, ref: str,  min_val, max_val: float, distribution: str = 'uniform'):
        self.parameter_deviations[ref] = ComponentDeviation.from_min_max(min_val, max_val, distribution)

    def get_parameter_value_deviation_type(self, param: str) -> (float, ComponentDeviation):
        value = self.editor.get_parameter(param)
        return value, self.parameter_deviations[param]

    def save_netlist(self, filename: str):
        if self.testbench_prepared is False:
            self.prepare_testbench()
        self.editor.write_netlist(filename)

    def prepare_testbench(self):
        raise RuntimeError("This method should be implemented in the derived class")

    def run(self, max_runs_per_sim: int = 512,  **kwargs):
        """
        Runs the simulations. See runner.run for details on keyword arguments.
        :param max_runs_per_sim: Maximum number of runs per simulation. If the number of runs is higher than this number,
        the simulation is split in multiple runs.
        """
        self.reset_netlist()
        self.prepare_testbench()
        self.editor.remove_instruction(".step param run -1 %d 1" % self.num_runs)  # Needs to remove this instruction
        for sim_no in range(-1, self.num_runs, max_runs_per_sim):
            run_stepping = ".step param run {} {} 1 ".format(sim_no, sim_no + max_runs_per_sim)
            self.editor.add_instruction(run_stepping)
            sim = self.runner.run(self.editor, **kwargs)
            self.simulations.append(sim)
            self.editor.remove_instruction(run_stepping)
