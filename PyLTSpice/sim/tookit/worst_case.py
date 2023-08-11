#!/usr/bin/env python
# coding=utf-8
from typing import Union, Optional

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

from .tolerance_deviations import ToleranceDeviations
from ..sim_runner import AnyRunner
from ..simulator import Simulator


class WorstCaseAnalysis(ToleranceDeviations):
    """Class to automate Monte-Carlo simulations"""

    def __init__(self, circuit_file: Union[str, BaseEditor], runner: Optional[AnyRunner] = None):
        super().__init__(circuit_file, runner)

    def prepare_testbench(self):
        """Prepares the simulation by setting the tolerances for the components"""
        index = 0
        for ref in self.device_deviations:
            val, dev = self.get_component_value_deviation_type(ref)  # get there present value
            new_val = val
            if dev.typ == 'toleration':
                tolstr = ('%f' % dev.max_value).rstrip('0').rstrip('.')
                new_val = "{wc(%s,%s,%d)}" % (val, tolstr, index)  # calculate expression for new value
            elif dev.typ == 'minmax':
                new_val = "{wc1(%s,%s,%s,%d)}" % (val, dev.min_value, dev.max_value, index)  # calculate expression for new value
            if new_val != val:
                self.set_component_value(ref, new_val)  # update the value
            index += 1

        self.editor.add_instruction(".function binary(run,idx) floor(run/(2**idx))-2*floor(run/(2**(idx+1)))")
        self.editor.add_instruction(".function wc(nom,tol,idx) {nom*if(binary(run,idx),1+tol,1-tol)}")
        self.editor.add_instruction(".function wc1(nom,min,max,idx) {nom*if(binary(run,idx),max,min}")
        self.num_runs = 2**index - 1
        self.editor.add_instruction(".step param run -1 %d 1" % self.num_runs)
        self.editor.set_parameter('run', -1)  # in case the step is commented.
