from collections import OrderedDict
from typing import Iterable
from .SpiceBatch import SimCommander
from .SpiceEditor import ComponentNotFoundError


class SimAnalysis(object):
    """
    Base class for making Monte-Carlo, Extreme Value Analysis (EVA) or Failure Mode and Effects Analysis.
    As a base class, a certain number of assertions must be made on the simulation results that will make the pass/fail.

    Note: For the time being only measurements done with .MEAS are possible. At a later stage the parsing of RAW files
    will be possible, although, it seems that the later solution is less computing intense.
    """

    def __init__(self, circuit_file: str, parallel_sims=4):
        self.simulator = SimCommander(circuit_file, parallel_sims=parallel_sims)
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
    def __init__(self, circuit_file: str, parallel_sims=4):
        SimAnalysis.__init__(self, circuit_file, parallel_sims=parallel_sims)
        self.resistors = self.simulator.get_components('R')
        self.capacitors = self.simulator.get_components('C')
        self.inductors = self.simulator.get_components('L')
        self.diodes = self.simulator.get_components('D')
        self.bipolars = self.simulator.get_components('Q')
        self.mosfets = self.simulator.get_components('M')
        self.subcircuits = self.simulator.get_components('X')
        self.user_failure_modes = OrderedDict()

    def add_failure_circuit(self, component, sub_circuit):
        if not component.startswith('X'):
            raise RuntimeError("The failure modes addition only works with subcircuits")
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
            self.simulator.set_component_value(resistor, '1f')  # replaces the resistor with a one femto-Ohm
            self.simulations[f"{resistor}_S"] = self.simulator.run()
            # Open Circuit
            self.simulator.remove_component(resistor)
            self.simulations[f"{resistor}_O"] = self.simulator.run()
            self.simulator.reset_netlist()

        for two_pin_comps in (self.capacitors, self.inductors, self.diodes):
            for two_pin_component in two_pin_comps:
                # Open Circuit
                cinfo = self.simulator.get_component_info(two_pin_component)
                self.simulator.remove_component(two_pin_component)
                self.simulations[f"{two_pin_component}_O"] = self.simulator.run()
                # Short Circuit
                self.simulator.netlist[cinfo['line']] = f"Rfmea_short_{two_pin_component}{cinfo['nodes']} 1f"
                self.simulations[f"{two_pin_component}_S"] = self.simulator.run()
                self.simulator.reset_netlist()
