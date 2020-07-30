from typing import Iterable
from PyLTSpice.LTSpiceBatch import SimCommander


class StepInfo(object):
    def __init__(self, what: str, elem: str, iter: Iterable):
        self.what = what
        self.elem = elem
        self.iter = iter


class SimStepper(object):

    def __init__(self, sim_commander: SimCommander):
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
        self.sim_commander = sim_commander
        self.iter_list = []

    def add_param_sweep(self, param: str, iterable: Iterable):
        """Adds a dimension to the simulation"""
        self.iter_list.append(StepInfo("param", param, iterable))

    def add_value_sweep(self, comp: str, iterable: Iterable):
        # The next line raises an ComponentNotFoundError if the component doesn't exist
        _ = self.sim_commander.get_component_value(comp)
        self.iter_list.append(StepInfo("component", comp, iterable))

    def add_model_sweep(self, comp: str, iterable: Iterable):
        # The next line raises an ComponentNotFoundError if the component doesn't exist
        _ = self.sim_commander.get_component_value(comp)
        self.iter_list.append(StepInfo("model", comp, iterable))

    def run_all(self):
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
                    self.sim_commander.set_parameter(self.iter_list[iter_no].elem, value)
                elif self.iter_list[iter_no].what == 'component':
                    self.sim_commander.set_component_value(self.iter_list[iter_no].elem, value)
                elif self.iter_list[iter_no].what == 'model':
                    self.sim_commander.set_element_model(self.iter_list[iter_no].elem, value)
                else:
                    # TODO: develop other sweeps
                    raise ValueError("Not Supported sweep")
                iter_no += 1
            if iter_no < 0:
                break
            self.sim_commander.run()
            iter_no = len(self.iter_list) - 1  # Resets the counter to start next iteration
        # Now waits for the simulations to end    
        self.sim_commander.wait_completion()


if __name__ == "__main__":
    from PyLTSpice.sweep_iterators import *

    class TestSim(object):
        def run(self):
            print("Run")

        def set_parameter(self, param, value):
            print("Setting Param", param, " to ", value)

        def set_component_value(self, comp, value):
            print("Setting Component", comp, " to ", value)

        def set_element_model(self, comp, value):
            print("Setting Element", comp, " to ", value)

        def get_component_value(self, comp):
            pass

    testsim = TestSim()
    test = SimStepper(testsim)
    test.add_param_sweep("param#1", range(1, 3))
    test.add_value_sweep("R1", sweep_log(0.1, 10, 10))
    test.add_model_sweep("D1", ("model1", "model2"))
    test.run_all()
