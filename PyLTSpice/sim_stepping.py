#!/usr/bin/env python

# -------------------------------------------------------------------------------
# Name:        sim_stepping.py
# Purpose:     Spice Simulation Library intended to automate the exploring of
#              design corners, try different models and different parameter
#              settings.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     31-07-2020
# Licence:     lGPL v3
# -------------------------------------------------------------------------------

__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"

from typing import Callable, Any
from typing import Iterable
from PyLTSpice.LTSpiceBatch import SimCommander


class StepInfo(object):
    def __init__(self, what: str, elem: str, iter: Iterable):
        self.what = what
        self.elem = elem
        self.iter = iter


class SimStepper(SimCommander):

    def __init__(self, spice_file: str, parallel_sims=4, renaming_mask=None):
        """This class is intended to be used for simulations with many parameter sweeps. This provides a more user-
        friendly interface than the SimCommander class when there are many parameters to be found. Using the
        SimCommander class a loop needs to be added for each dimension of the simulations.
        A typical usage would be as follows:
        ```
        LTC = SimCommander("my_circuit.asc")
        for dmodel in ("BAT54", "BAT46WJ")
            LTC.set_element_model("D1", model)  # Sets the Diode D1 model
            for res_value1 in sweep(2.2, 2,4, 0.2):  # Steps from 2.2 to 2.4 with 0.2 increments
                LTC.set_component_value('R1', res_value1)  # Updates the resistor R1 value to be 3.3k
                for temperature in sweep(0, 80, 20):  # Makes temperature step from 0 to 80 degrees in 20 degree steps
                    LTC.set_parameters(temp=80)  # Sets the simulation temperature to be 80 degrees
                    for res_value2 in (10, 25, 32):
                        LTC.set_component_value('R2', res_value2)  # Updates the resistor R2 value to be 3.3k
                        LTC.run()

        LTC.wait_completion()  # Waits for the LTSpice simulations to complete
        ```

        With SimStepper the same thing can be done as follows, resulting in a more cleaner code.

        ```
        Stepper = SimStepper("my_circuit.asc")
        Stepper.add_model_sweep('D1', "BAT54", "BAT46WJ")
        Stepper.add_component_sweep('R1', sweep(2.2, 2,4, 0.2))  # Steps from 2.2 to 2.4 with 0.2 increments
        Stepper.add_parameter_sweep('temp', sweep(0, 80, 20))  # Makes temperature step from 0 to 80 degrees in 20
                                                               # degree steps
        Stepper.add_component_sweep('R2', (10, 25, 32)) #  Updates the resistor R2 value to be 3.3k
        Stepper.run_all()

        ```

        Another advantage of using SimStepper is that it can optionally use the .SAVEBIAS in the first simulation and
        then use the .LOADBIAS command at the subsequent ones to speed up the simulation times.
        """
        SimCommander.__init__(self, spice_file, parallel_sims)
        self.iter_list = []

    def add_param_sweep(self, param: str, iterable: Iterable):
        """Adds a dimension to the simulation, where the param is swept."""
        self.iter_list.append(StepInfo("param", param, iterable))

    def add_value_sweep(self, comp: str, iterable: Iterable):
        """Adds a dimension to the simulation, where a component value is swept."""
        # The next line raises an ComponentNotFoundError if the component doesn't exist
        _ = self.get_component_value(comp)
        self.iter_list.append(StepInfo("component", comp, iterable))

    def add_model_sweep(self, comp: str, iterable: Iterable):
        """Adds a dimension to the simulation, where a component model is swept."""
        # The next line raises an ComponentNotFoundError if the component doesn't exist
        _ = self.get_component_value(comp)
        self.iter_list.append(StepInfo("model", comp, iterable))

    def total_number_of_simulations(self):
        """Returns the total number of simulations foreseen."""
        total = 1
        for step in self.iter_list:
            total *= len(step.iter)
        return total

    def run_all(self, callback: Callable[[str, str], Any] = None, use_loadbias='Auto'):
        assert use_loadbias in ('Auto', 'Yes', 'No'), "use_loadbias argument must be 'Auto', 'Yes' or 'No'"
        if (use_loadbias == 'Auto' and self.total_number_of_simulations() > 10) or use_loadbias == 'Yes':
            # It will choose to use .SAVEBIAS/.LOADBIAS if the number of simulaitons is higher than 10
            # TODO: Make a first simulation and storing the bias
            pass
        iter_no = 0
        iterators = [iter(step.iter) for step in self.iter_list]
        while True:
            while 0 <= iter_no < len(self.iter_list):
                try:
                    value = iterators[iter_no].__next__()
                except StopIteration:
                    iterators[iter_no] = iter(self.iter_list[iter_no].iter)
                    iter_no -= 1
                    continue
                if self.iter_list[iter_no].what == 'param':
                    self.set_parameter(self.iter_list[iter_no].elem, value)
                elif self.iter_list[iter_no].what == 'component':
                    self.set_component_value(self.iter_list[iter_no].elem, value)
                elif self.iter_list[iter_no].what == 'model':
                    self.set_element_model(self.iter_list[iter_no].elem, value)
                else:
                    # TODO: develop other types of sweeps EX: add .STEP instruction
                    raise ValueError("Not Supported sweep")
                iter_no += 1
            if iter_no < 0:
                break
            # TODO: Implement the renaming Mask, so the output filename is written according to user instructions
            SimCommander.run(self, callback=callback)  # Like this a recursion is avoided
            iter_no = len(self.iter_list) - 1  # Resets the counter to start next iteration
        # Now waits for the simulations to end
        self.wait_completion()

    def run(self):
        """Rather uses run_all instead"""
        self.run_all()


if __name__ == "__main__":
    from PyLTSpice.sweep_iterators import *

    test = SimStepper("mydesign.asc")
    test.add_param_sweep("param#1", range(1, 3))
    test.add_value_sweep("R1", sweep_log(0.1, 10, 10))
    test.add_model_sweep("D1", ("model1", "model2"))
    test.run_all()

