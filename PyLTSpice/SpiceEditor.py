#!/usr/bin/env python
# -------------------------------------------------------------------------------
# Name:        SpiceEditor.py
# Purpose:     Class made to update Generic Spice Netlists
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     30-08-2020
# Licence:     lGPL v3
# -------------------------------------------------------------------------------
import os
import traceback
import re
import logging
from typing import Union, Optional

__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2020, Fribourg Switzerland"

END_LINE_TERM = '\n'

# A Spice netlist can only have one of the instructions below, otherwise an error will be raised
UNIQUE_SIMULATION_DOT_instructionS = ('.AC', '.DC', '.TRAN', 'NOISE', '.DC', '.TF')

REPLACE_REGXES = {
    'B': r"^(B[VI]\w+)(\s+[\w\+\-]+){2}\s+(?P<value>.*)$",  # Behavioral source
    'C': r"^(C\w+)(\s+[\w\+\-]+){2}\s+(?P<value>({)?(?(3).*}|([0-9\.E+-]+(Meg|[kmup])?R?))).*$",  # Capacitor
    'D': r"^(D\w+)(\s+[\w\+\-]+){2}\s+(?P<value>\w+).*$",  # Diode
    'I': r"^(I\w+)(\s+[\w\+\-]+){2}\s+(?P<value>.*)$",  # Current Source
    'J': r"^(J\w+)(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # JFET
    'K': r"^(K\w+)(\s+[\w\+\-]+){2:4}\s+(?P<value>[\+\-]?[0-9\.E+-]+[kmup]?).*$",  # Mutual Inductance
    'L': r"^(L\w+)(\s+[\w\+\-]+){2}\s+(?P<value>({)?(?(3).*}|([0-9\.E+-]+(Meg|[kmup])?R?))).*$",  # Inductance
    'M': r"^(M\w+)(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # MOSFET
    'Q': r"^(Q\w+)(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # Bipolar
    'R': r"^(R\w+)(\s+[\w\+\-]+){2}\s+(?P<value>({)?(?(3).*}|([0-9\.E+-]+(Meg|[kmup])?R?))).*$",  # Resistors
    'V': r"^(V\w+)(\s+[\w\+\-]+){2}\s+(?P<value>.*)$",  # Voltage Source
    'X': r"^(X\w+)(\s+[\w\+\-]+){1,99}\s+(?P<value>\w+)(\s+\w+\s*=\s*\S+)*$",  # Sub-circuit
}

PARAM_REGX = r"%s\s*=\s*(?P<value>[\w*/\.+-/{}()]*)"


def _get_group_regxstr(regstr, param):
    """(Private function. Not to be used directly)
    Helper function to parse regular expressions."""
    a = regstr.find("(?P<%s>" % param)
    if a != -1:
        b = a + 1
        parenthesis_count = 0
        while b < len(regstr):
            if regstr[b] == ')':
                if parenthesis_count == 0:
                    return regstr[a:b + 1]
                else:
                    parenthesis_count -= 1
            elif regstr[b] == '(':
                parenthesis_count += 1
            b += 1
    return None


def _is_unique_instruction(instruction):
    """(Private function. Not to be used directly)
    Returns true if the instruction is one of the unique instructions"""
    cmd = instruction.upper()
    for directive in UNIQUE_SIMULATION_DOT_instructionS:
        if cmd.startswith(directive):
            return True
    return False


class ComponentNotFoundError(Exception):
    """Component Not Found Error"""


class SpiceEditor(object):

    def __init__(self, netlist_file):
        self.logger = logging.getLogger("LTCommander")
        self.netlist = []
        self.netlist_file = netlist_file

    def _getline_startingwith(self, substr):
        """Internal function. Do not use."""
        substr_upper = substr.upper()
        for line_no, line in enumerate(self.netlist):
            line_upcase = line.upper()
            if line_upcase.startswith(substr_upper):
                return line_no
        return -1

    def _get_param_line(self, param):
        """Internal function. Do not use."""
        prm = param.upper()
        search_param = re.compile("%s\s*=" % prm)  # process everything in uppercase (Spice is case insensitive)
        in_param_line = False  # This is needed to process multi-line commands
        for line_no, line in enumerate(self.netlist):
            line_upcase = line.lstrip(' ').upper()  # Everything in uppercase
            if in_param_line or line_upcase.startswith('.PARAM '):
                if search_param.search(line_upcase):
                    return line_no
                elif line.endswith('+'):  # processes next line independent if it starts with .PARAM
                    in_param_line = True
                else:
                    in_param_line = False
            else:
                in_param_line = False
        else:
            return -1

    def _set_model_and_value(self, component, value):
        """Internal function. Do not use."""
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regxstr = REPLACE_REGXES.get(prefix, None)  # Obtain RegX to make the update

        if regxstr is None:
            print("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            print("Got '{}'".format(component))
            return

        if isinstance(value, str):
            regxvaluestr = _get_group_regxstr(regxstr, 'value')
            regexvalue = re.compile(regxvaluestr, re.IGNORECASE)
            m = regexvalue.match(value)
            if m is None:
                raise ValueError("Value is not in the good format. Expecting ""{}"". Got ""{}""".format(regxvaluestr,
                                                                                                        value))
        else:
            value = str(value)

        line_no = self._getline_startingwith(component)
        if line_no != -1:  # The component was found
            regex = re.compile(regxstr, re.IGNORECASE)
            line = self.netlist[line_no]
            m = regex.match(line)
            if m is None:
                raise NotImplementedError('Unsupported line "{}"\nExpected format is "{}"'.format(line, regxstr))
                # print("Unsupported line ""{}""".format(line))
            else:
                start = m.start('value')
                end = m.end('value')
                line = line[:start] + value + line[end:]
                self.netlist[line_no] = line
        else:
            error_msg = "Component '%s' not found in netlist" % component
            self.logger.error(error_msg)
            raise ComponentNotFoundError(error_msg)

    def _get_component_info(self, component) -> Optional[dict]:
        """Internal function. Do not use."""
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regxstr = REPLACE_REGXES.get(prefix, None)  # Obtain RegX to make the update

        if regxstr is None:
            self.logger.warning("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            self.logger.warning("Got '{}'".format(component))
            return None

        line_no = self._getline_startingwith(component)
        if line_no != -1:  # The component was found
            regex = re.compile(regxstr, re.IGNORECASE)
            line = self.netlist[line_no]
            m = regex.match(line)
            if m is None:
                error_msg = 'Unsupported line "{}"\nExpected format is "{}"'.format(line, regxstr)
                self.logger.error(error_msg)
                raise NotImplementedError(error_msg)
                # print("Unsupported line ""{}""".format(line))
            else:
                info = m.groupdict()
                return info
        else:
            error_msg = "Component '%s' not found in netlist" % component
            self.logger.error(error_msg)
            raise ComponentNotFoundError(error_msg)

    def add_instruction(self, instruction: str) -> None:
        """Serves to add SPICE instructions to the simulation netlist. For example:
                  .tran 10m ; makes a transient simulation
                  .meas TRAN Icurr AVG I(Rs1) TRIG time=1.5ms TARG time=2.5ms" ; Establishes a measuring
                  .step run 1 100, 1 ; makes the simulation run 100 times

        Parameters
        ----------
        instruction : str
            Spice instruction to add to the netlist. This instruction will be added at the end of the netlist,
            typically just before the .BACKANNO statement

        Returns
        -------
        Nothing
        """
        if _is_unique_instruction(instruction):
            # Before adding new instruction, delete previously set unique instructions
            i = 0
            while i < len(self.netlist):
                line = self.netlist[i]
                if _is_unique_instruction(line):
                    self.netlist[i] = instruction
                    break
                else:
                    i += 1
        else:
            # check whether the instruction is already there (dummy proofing)
            if instruction not in self.netlist:
                # Insert before backanno instruction
                try:
                    line = self.netlist.index('.backanno')
                except ValueError:
                    line = len(self.netlist) - 2  # This is where typically the .backanno instruction is
                self.netlist.insert(line, instruction)

    def add_instructions(self, *instructions):
        """Adds a list of instructions to the SPICE NETLIST.
        Example:
            LTC.add_instructions(
                ".STEP run -1 1023 1",
                ".dc V1 -5 5"
            )"""
        for instruction in instructions:
            self.add_instruction(instruction)

    def remove_instruction(self, *instruction):
        """Usage a previously added instructions.
        Example:
            LTC.remove_instruction(".STEP run -1 1023 1")
        """
        self.netlist.remove(instruction)

    def get_parameter(self, param :str) -> str:
        """Retrieves a Parameter from the Netlist"""
        param_def =  self.netlist[self._get_param_line(param)]
        regx = re.compile(PARAM_REGX % param, re.IGNORECASE)
        m = regx.search(param_def, re.IGNORECASE)
        return m.group('value')

    def set_parameter(self, param: str, value: Union[str, int, float]) -> None:
        """Adds a parameter to the SPICE netlist.
        Usage:
            LTC.set_parameter("TEMP", 80)

        This adds onto the netlist the following line:
            .PARAM TEMP=80
        This is an alternative to the set_parameters which is more pythonic in it's usage,
        and allows setting more than one parameter at once.

        Parameters
        ----------
        param : str
            Spice Parameter name to be added or updated.
        value : str, int or float
            Parameter Value to be set.


        Returns
        ------
        Nothing
        """
        param_line = self._get_param_line(param)
        if param_line == -1:  # Was not found
            # the last two lines are typically (.backano and .end)
            insert_line = len(self.netlist) - 2
            self.netlist.insert(insert_line, '.PARAM {}={}  ; Batch instruction'.format(param, value))
        else:
            regx = re.compile(PARAM_REGX % param, re.IGNORECASE)
            line = self.netlist[param_line]
            m = regx.search(line)
            start, stop = m.span()
            self.netlist[param_line] = line[:start] + "{}={}".format(param, value) + line[stop:]

    def set_parameters(self, **kwargs):
        """Adds one or more parameters to the netlist.
        Usage:
            for temp in (-40, 25, 125):
                for freq in sweep_log(1, 100E3,)
            LTC.set_parameters(TEMP=80, freq=freq)
        """
        for param in kwargs:
            self.set_parameter(param, kwargs[param])

    def set_component_value(self, device: str, value: Union[str, int, float]) -> None:
        """Changes the value of a component, such as a Resistor, Capacitor or Inductor.
        Usage:
            LTC.set_component_value('R1', '3.3k')

        Parameters
        ----------
        device : str
            Reference of the circuit element to be updated.
        value : str, int or float
            value to be be set on the given circuit element

        Raises
        ------
        ComponentNotFoundError - In case the component is not found
        ValueError - In case the value doesn't correspond to the expected format
        NotImplementedError - In case the circuit element is defined in a format which is not supported by this version.
                            If this is the case, use GitHub to start a ticket.
                            https://github.com/nunobrum/PyLTSpice
        """
        self._set_model_and_value(device, value)

    def set_element_model(self, element: str, model: str) -> None:
        """Changes the value of a circuit element, such as a diode model or a voltage supply.
        Usage:
            LTC.set_element_model('D1', '1N4148')
            LTC.set_element_model('V1' "SINE(0 1 3k 0 0 0)")

        Parameters
        ----------
        element : str
            Reference of the circuit element to be updated.
        model : str
            model name of the device to be updated

        Raises
        ------
        ComponentNotFoundError - In case the component is not found
        ValueError - In case the model format contains irregular characters
        NotImplementedError - In case the circuit element is defined in a format which is not supported by this version.
                            If this is the case, use GitHub to start a ticket.
                            https://github.com/nunobrum/PyLTSpice
        """
        self._set_model_and_value(element, model)

    def get_component_value(self, element: str) -> str:
        """
        Returns the value of a component retrieved from the netlist.

        Parameters
        ----------
        element : str
            Reference of the circuit element to search for.

        Returns
        -------
        : str
            value of the circuit element .
        """
        return self._get_component_info(element)['value']

    def set_component_values(self, **kwargs):
        """Adds one or more components on the netlist.
        Usage:
            LTC.set_component_values(R1=330, R2="3.3k", R3="1Meg", V1="PWL(0 1 30m 1 30.001m 0 60m 0 60.001m 1)")
        """
        for value in kwargs:
            self.set_component_value(value, kwargs[value])

    def get_components(self, prefixes='*') -> list:
        """Returns a list of components that match the list of prefixes indicated on the parameter prefixes.
        In case prefixes is left empty, it returns all the ones that are defined by the REPLACE_REGEXES.
        The list will contain the designators of all components found. """
        answer = []
        if prefixes == '*':
            prefixes = ''.join(REPLACE_REGXES.keys())
        for line in self.netlist:
            prefix = line.upper()[0]
            if prefix in prefixes:
                # regexvalue = re.compile(REPLACE_REGXES[prefix], re.IGNORECASE)
                # m = regexvalue.match(line)
                i=1
                while line[i] not in (' ', '\t'):  # detects the first space of tab which means end of designator
                    i += 1
                answer.append(line[:i])  # Appends only the designators
        return answer

    def remove_component(self, designator):
        line = self._getline_startingwith(designator)
        del self.netlist[line]  # Deletes the line

    def get_all_nodes(self):
        """TODO: Implement a function that retrieves all nodes existing on a Netlist"""

    def write_netlist(self, run_netlist_file: str):
        """
        Writes the netlist will all the requested updates into a file named <run_netlist_file>.

        Parameters
        ----------
        run_netlist_file :str
            File name of the netlist file.

        Returns
        -------
        Nothing
        """
        for i, line in enumerate(self.netlist):
            if not line.endswith(END_LINE_TERM):
                self.netlist[i] = line + END_LINE_TERM
        f = open(run_netlist_file, 'w')
        f.writelines(self.netlist)
        f.close()

    def reset_netlist(self):
        """
        Removes all previous edits done to the netlist, i.e. resets it to the original state.

        Parameters
        ----------
        None

        Returns
        -------
        Nothing
        """
        if os.path.exists(self.netlist_file):
            try:
                f = open(self.netlist_file, 'r')
                self.netlist = f.readlines()
                f.close()
                for i, line in enumerate(self.netlist):
                    self.netlist[i] = line.rstrip(END_LINE_TERM)
            except IOError as err:
                self.netlist = None
                error_msg = traceback.format_tb(err)
                self.logger.error(error_msg)
            except Exception as err:
                error_msg = traceback.format_tb(err)
                self.logger.error(error_msg)
                self.netlist = None


if __name__ == '__main__':
    E = SpiceEditor('..\\tests\\Batch_Test.net')
    E.reset_netlist()
    print(E.get_component_value('R1'))
    print("Setting 1.23k")
    E.set_parameter("I1", "1.23k")
    print(E.get_parameter('I1'))
    print("Setting {freq*(10/5.0})")
    E.set_parameters(I1="{freq*(10/5.0})")
    print(E.get_parameter('I1'))
    print(E.get_components())
    print(E.get_components('RC'))
    print('\n'.join(E.netlist))
