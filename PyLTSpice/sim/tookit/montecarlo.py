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

from .tolerance_deviations import ToleranceDeviations, DeviationType


class Montecarlo(ToleranceDeviations):
    """Class to automate Monte-Carlo simulations"""

    def prepare_testbench(self, num_runs: int = 1000):
        """Prepares the simulation by setting the tolerances for the components"""
        min_max_uni_func = False
        min_max_norm_func = False
        tol_uni_func = False
        tol_norm_func = False
        for ref in self.get_components('*'):
            val, dev = self.get_component_value_deviation_type(ref)  # get there present value
            new_val = val
            if dev.typ == DeviationType.tolerance:
                tolstr = ('%f' % dev.max_val).rstrip('0').rstrip('.')
                if dev.distribution == 'uniform':
                    new_val = "{utol(%s,%s)}" % (val, tolstr)  # calculate expression for new value
                    tol_uni_func = True
                elif dev.distribution == 'normal':
                    new_val = "{ntol(%s,%s)}" % (val, tolstr)
                    tol_norm_func = True
            elif dev.typ == DeviationType.minmax:
                if dev.distribution == 'uniform':
                    new_val = "{urng(%s, %s,%s)}" % (val, dev.min_val, dev.max_val)  # calculate expression for new value
                    min_max_uni_func = True
                elif dev.distribution == 'normal':
                    new_val = "{nrng(%s,%s,%s)}" % (val, dev.min_val, dev.max_val)
                    min_max_norm_func = True

            if new_val != val:  # Only update the value if it has changed
                self.set_component_value(ref, new_val)  # update the value

        for param in self.parameter_deviations:
            val, dev = self.get_parameter_value_deviation_type(param)
            new_val = val
            if dev.typ == DeviationType.tolerance:
                if dev.distribution == 'uniform':
                    new_val = "{utol(%s,%f)}" % (val, dev.max_val)
                    tol_uni_func = True
                elif dev.distribution == 'normal':
                    new_val = "{ntol(%f,%f)}" % (val, dev.max_val)
                    tol_norm_func = True
            elif dev.typ == DeviationType.minmax:
                if dev.distribution == 'uniform':
                    new_val = "{urng(%s,%f,%f)}" % (val, (dev.max_val+dev.min_val)/2, (dev.max_val-dev.min_val)/2)
                    min_max_uni_func = True
                elif dev.distribution == 'normal':
                    new_val = "{nrng(%s,%f,%f)}" % (val, (dev.max_val+dev.min_val)/2, (dev.max_val-dev.min_val)/6)
                    min_max_norm_func = True
            else:
                continue
            self.editor.set_parameter(param, new_val)

        if tol_uni_func:
            self.editor.add_instruction(".function utol(nom,tol) if(run<0, nom, mc(nom,tol))")

        if tol_norm_func:
            self.editor.add_instruction(".function ntol(nom,tol) if(run<0, nom, nom*(1+gauss(tol/3)))")

        if min_max_uni_func:
            self.editor.add_instruction(".function urng(nom,mean,df2) if(run<0, nom, mean*flat(df2))")

        if min_max_norm_func:
            self.editor.add_instruction(".function nrng(nom,mean,df23) if(run<0, nom, mean*(1+gauss(df2)))")

        self.num_runs = num_runs
        self.editor.add_instruction(".step param run -1 %d 1" % num_runs)
        self.editor.set_parameter('run', -1)
        self.testbench_prepared = True
