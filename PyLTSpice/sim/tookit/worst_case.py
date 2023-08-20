#!/usr/bin/env python
# coding=utf-8
from typing import Union, Optional

from ...editor.base_editor import BaseEditor
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

from .tolerance_deviations import ToleranceDeviations, DeviationType


class WorstCaseAnalysis(ToleranceDeviations):
    """Class to automate Monte-Carlo simulations"""

    def set_component_deviation(self, ref: str, index):
        val, dev = self.get_component_value_deviation_type(ref)  # get there present value
        new_val = val
        if dev.typ == DeviationType.tolerance:
            new_val = "{wc(%s,%g,%d)}" % (val, dev.max_val, index)  # calculate expression for new value
        elif dev.typ == DeviationType.minmax:
            new_val = "{wc1(%s,%g,%g,%d)}" % (val, dev.min_val, dev.max_val, index)  # calculate expression for new value

        if new_val != val:
            self.set_component_value(ref, new_val)  # update the value

    def prepare_testbench(self, *args, **kwargs):
        """Prepares the simulation by setting the tolerances for the components"""
        index = 0
        for ref in self.device_deviations:
            self.set_component_deviation(ref, index)
            index += 1
        for ref in self.parameter_deviations:
            val, dev = self.get_parameter_value_deviation_type(ref)
            new_val = val
            if dev.typ == DeviationType.tolerance:
                new_val = "{wc(%s,%g,%d)}" % (val, dev.max_val, index)  # calculate expression for new value
            elif dev.typ == DeviationType.minmax:
                new_val = "{wc1(%s,%g,%g,%d)}" % (val, dev.min_val, dev.max_val, index)
            if new_val != val:
                self.editor.set_parameter(ref, new_val)
            index += 1

        for prefix in self.default_tolerance:
            for ref in self.get_components(prefix):
                if ref not in self.device_deviations:
                    self.set_component_deviation(ref, index)
                    index += 1

        self.editor.add_instruction(".function binary(run,idx) floor(run/(2**idx))-2*floor(run/(2**(idx+1)))")
        self.editor.add_instruction(".function wc(nom,tol,idx) {nom*if(binary(run,idx),1-tol,1+tol)}")
        self.editor.add_instruction(".function wc1(nom,min,max,idx) {nom*if(binary(run,idx),min,max)}")
        self.num_runs = 2**index - 1
        self.editor.add_instruction(".step param run -1 %d 1" % self.num_runs)
        self.editor.set_parameter('run', -1)  # in case the step is commented.
        self.testbench_prepared = True
