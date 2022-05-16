#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
# Name:        SpiceEditor.py
# Purpose:     Class made to update Generic Spice Netlists
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     30-08-2020
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import os
import traceback
import re
import logging
from math import log, floor
from typing import Union, Optional, List
from PyLTSpice.detect_encoding import detect_encoding

__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2021, Fribourg Switzerland"

END_LINE_TERM = '\n'

# A Spice netlist can only have one of the instructions below, otherwise an error will be raised
UNIQUE_SIMULATION_DOT_INSTRUCTIONS = ('.AC', '.DC', '.TRAN', '.NOISE', '.DC', '.TF')

SPICE_DOT_INSTRUCTIONS = (
    '.BACKANNO',
    '.END',
    '.ENDS',
    '.FERRET', # Downloads a File from a given URL
    '.FOUR',  # Compute a Fourier Component after a .TRAN Analysis
    '.FUNC', '.FUNCTION',
    '.GLOBAL',
    '.IC',
    '.INC', '.INCLUDE',  # Include another file
    '.LIB', # Include a Library
    '.LOADBIAS', # Load a Previously Solved DC Solution
     # These Commands are part of the contraption Programming Language of the Arbitrary State Machine
    '.MACHINE', '.STATE', '.RULE', '.OUTPUT', '.ENDMACHINE',
    '.MEAS', '.MEASURE',
    '.MODEL',
    '.NET', # Compute Network Parameters in a .AC Analysis
    '.NODESET',  # Hints for Initial DC Solution
    '.OP',
    '.OPTIONS',
    '.PARAM', '.PARAMS',
    '.SAVE', '.SAV',
    '.SAVEBIAS',
    '.STEP',
    '.SUBCKT',
    '.TEXT',
    '.WAVE', # Write Selected Nodes to a .Wav File

)

REPLACE_REGXES = {
    'A': r"",  # Special Functions, Parameter substitution not supported
    'B': r"^(?P<designator>B§?[VI]?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Behavioral source
    'C': r"^(?P<designator>C§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>({)?(?(5).*}|([0-9\.E+-]+(Meg|[kmuµnpf])?F?))).*$",  # Capacitor
    'D': r"^(?P<designator>D§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>\w+).*$",  # Diode
    'I': r"^(?P<designator>I§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Current Source
    'E': r"^(?P<designator>E§?\w+)(?P<nodes>(\s+\S+){2,4}\s+(?P<value>.*)$",  # Voltage Dependent Voltage Source
                                                        # this only supports changing gain values
    'F': r"^(?P<designator>F§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Current Dependent Current Source
                                                        # TODO: this implementation replaces everything after the 2
                                                        #       first nets
    'G': r"^(?P<designator>G§?\w+)(?P<nodes>(\s+\S+){2,4})\s+(?P<value>.*)$",  # Voltage Dependent Current Source
                                                        # this only supports changing gain values
    'H': r"^(?P<designator>H§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Voltage Dependent Current Source
                                                        # TODO: this implementation replaces everything after the 2
                                                        #       first nets
    'I': r"^(?P<designator>I§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Current Source
                                                        # TODO: this implementation replaces everything after the 2
                                                        #       first nets
    'J': r"^(?P<designator>J§?\w+)(?P<nodes>(\s+\S+){3})\s+(?P<value>\w+).*$",  # JFET
    'K': r"^(?P<designator>K§?\w+)(?P<nodes>(\s+\S+){2,4})\s+(?P<value>[\+\-]?[0-9\.E+-]+[kmuµnpf]?).*$",  # Mutual Inductance
    'L': r"^(?P<designator>L§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>({)?(?(5).*}|([0-9\.E+-]+(Meg|[kmuµnpf])?H?))).*$",  # Inductance
    'M': r"^(?P<designator>M§?\w+)(?P<nodes>(\s+\S+){3,4})\s+(?P<value>\w+).*$",  # MOSFET TODO: Parameters substitution not supported
    'O': r"^(?P<designator>O§?\w+)(?P<nodes>(\s+\S+){4})\s+(?P<value>\w+).*$",  # Lossy Transmission Line TODO: Parameters substitution not supported
    'Q': r"^(?P<designator>Q§?\w+)(?P<nodes>(\s+\S+){3})\s+(?P<value>\w+).*$",  # Bipolar TODO: Parameters substitution not supported
    'R': r"^(?P<designator>R§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>({)?(?(5).*}|([0-9\.E+-]+(Meg|[kmuµnpf])?R?))).*$", # Resistors
    'S': r"^(?P<designator>S§?\w+)(?P<nodes>(\s+\S+){4})\s+(?P<value>.*)$",  # Voltage Controlled Switch
    'T': r"^(?P<designator>T§?\w+)(?P<nodes>(\s+\S+){4})\s+(?P<value>.*)$",  # Lossless Transmission
    'U': r"^(?P<designator>U§?\w+)(?P<nodes>(\s+\S+){3})\s+(?P<value>.*)$",  # Uniform RC-line
    'V': r"^(?P<designator>V§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Voltage Source
                                                        # TODO: this implementation replaces everything after the 2
                                                        #       first nets
    'W': r"^(?P<designator>W§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Current Controlled Switch
                                                        # TODO: this implementation replaces everything after the 2
                                                        #       first nets
    'X': r"^(?P<designator>X§?\w+)(?P<nodes>(\s+\S+){1,99})\s+(?P<value>\w+)(\s+\w+\s*=\s*\S+)*\s*$",  # Sub-circuit, Parameter substitution not supported
    'Z': r"^(?P<designator>Z§?\w+)(?P<nodes>(\s+\S+){3})\s+(?P<value>\w+).*$",  # MESFET and IBGT. TODO: Parameters substitution not supported
}

PARAM_REGX = r"%s\s*(=\s*)?(?P<value>[\w*/\.+-/{}()]*)"
SUBCIRCUIT_DIVIDER = ':'

def format_eng(value) -> str:
    """
    Helper function for formating value with the SI qualifiers.  That is, it will use

        * p for pico (10E-12)
        * n for nano (10E-9)
        * u for micro (10E-6)
        * m for mili (10E-3)
        * k for kilo (10E+3)
        * Meg for Mega (10E+6)


    :param value: float value to format
    :type value: float
    :return: String wiht the formatted value
    :rtype: str
    """
    if value == 0.0:
        return "0.0"  # This avoids a problematic log(0)
    e = floor(log(abs(value), 1000))
    if -5 <= e < 0:
        suffix = "fpnum"[e]
    elif e == 0:
        suffix = ''
    elif e == 1:
        suffix = "k"
    elif e == 2:
        suffix = 'Meg'
    else:
        return '{:E}'.format(value)
    return '{:g}{:}'.format(value* 1000**-e, suffix)


def scan_eng(value: str) -> float:
    """
    Converts a string to a float, considering SI multipliers

        * f for femto (10E-15)
        * p for pico (10E-12)
        * n for nano (10E-9)
        * u or µ for micro (10E-6)
        * m for mili (10E-3)
        * k for kilo (10E+3)
        * Meg for Mega (10E+6)

    The extra unit qualifiers such as V for volts or F for Farads are ignored.


    :param value: string to be converted to float
    :type value: str
    :return:
    :rtype: float
    :raises: ValueError when the value cannot be converted.
    """
    # Search for the last digit on the string. Assuming that all after the last number are SI qualifiers and units.
    x = len (value)
    while x > 0:
        if value[x-1] in "0123456789":
            break
        x -= 1
    suffix = value[x:]  # this is the non numeric part at the end
    f = float(value[:x])  # this is the numeric part. Can raise ValueError.

    if suffix[0] in "fpnuµmk":
        return f * {
            'f': 1.0e-15,
            'p': 1.0e-12,
            'n': 1.0e-09,
            'u': 1.0e-06,
            'µ': 1.0e-06,
            'm': 1.0e-03,
            'k': 1.0e+03,
        }[suffix[0]]
    elif suffix.startswith("Meg"):
        return f * 1E6
    else:
        raise f


def get_line_command(line) -> str:
    """
    Retrives the type of SPICE command in the line.
    Starts by removing the leading spaces and the evaluates if it is a comment, a directive or a component.
    """
    if isinstance(line, str):
        for i in range(len(line)):
            ch = line[i]
            if ch == ' ' or ch == '\t':
                continue
            else:
                ch = ch.upper()
                if ch in REPLACE_REGXES:  # A circuit element
                    return ch
                elif ch == '+':
                    return '+'  # This is a line continuation.
                elif ch in "#;*\n\r":  # It is a comment or a blank line
                    return "*"
                elif ch == '.':  # this is a directive
                    j = i + 1
                    while j < len(line) and (line[j] not in (' ', '\t', '\r', '\n')):
                        j += 1
                    return line[i:j].upper()
                else:
                    raise SyntaxError('Unrecognized command in line "%s"' % line)
    elif isinstance(line, SpiceCircuit):
        return ".SUBCKT"
    else:
        raise SyntaxError('Unrecognized command in line "{}"'.format(line))


def _first_token_upped(line):
    """
    (Private function. Not to be used directly)
    Returns the first non space character in the line. If a point '.' is found, then it gets the primitive associated.
    """
    i = 0
    while i < len(line) and line[i] in (' ', '\t'):
        i += 1
    j = i
    while i < len(line) and not (line[i] in (' ', '\t')):
        i += 1
    return line[j:i].upper()

def _is_unique_instruction(instruction):
    """
    (Private function. Not to be used directly)
    Returns true if the instruction is one of the unique instructions
    """
    cmd = get_line_command(instruction)
    return cmd in UNIQUE_SIMULATION_DOT_INSTRUCTIONS


class ComponentNotFoundError(Exception):
    """Component Not Found Error"""

class ParameterNotFoundError(Exception):
    """ParameterNotFound Error"""


class SpiceCircuit(object):
    """
    The Spice Circuit represents subcircuits within a SPICE circuit and since subcircuits can have subcircuits inside
    them, it serves as base for the top level netlist.
    This hierchical approach helps to encapsulate and protect parameters and components from a edits made a a higher
    level.
    The information is stored in a python list, each line of the SPICE netlist is an item of the list. A Subcircuit
    is represented as a SpiceCircuit object.
    """

    def __init__(self):
        self.subcircuits = {}
        self.netlist = []
        self.logger = logging.getLogger("SpiceCircuit")

    def _getline_startingwith(self, substr: str) -> int:
        """Internal function. Do not use."""
        # This function returns the line number that starts with the substr string.
        # If the line is not found, then -1 is returned.
        substr_upper = substr.upper()
        for line_no, line in enumerate(self.netlist):
            if isinstance(line, list):  # If it is a subcircuit it will simply ignore it.
                continue
            line_upcase = _first_token_upped(line)
            if line_upcase == substr_upper:
                return line_no
        error_msg = "line starting with '%s' not found in netlist" % substr
        self.logger.error(error_msg)
        raise ComponentNotFoundError(error_msg)

    def _add_lines(self, line_iter):
        """Internal function. Do not use.
        Add a list of lines to the netlist."""
        for line in line_iter:
            cmd = get_line_command(line)
            if cmd == '.SUBCKT':
                sub_circuit = SpiceCircuit()
                sub_circuit.netlist.append(line)
                # Advance to the next non nested .ENDS
                finished = sub_circuit._add_lines(line_iter)
                if finished:
                    self.netlist.append(sub_circuit)
                else:
                    return False
            elif cmd == '+':
                assert len(self.netlist) > 0, "ERROR: The first line cannot be starting with a +"
                self.netlist[-1] += line  # Appends to the last line
            else:
                self.netlist.append(line)
                if cmd[:4] == '.END':  # True for either .END and .ENDS primitives
                    return True  # If an subcircuit is ended correctly, returns True
        return False  # If a subcircuit ends abruptly, returns False

    def _write_lines(self, f):
        """Internal function. Do not use."""
        # This helper function writes the contents of Subcircuit to the file f
        for command in self.netlist:
            if isinstance(command, SpiceCircuit):
                command._write_lines(f)
            else:
                f.write(command)

    def _get_param_line(self, param: str) -> int:
        """Internal function. Do not use."""
        search_param = re.compile(PARAM_REGX % param, re.IGNORECASE)  # Spice is case insensitive
        in_param_line = False  # This is needed to process multi-line commands
        line_no = 0
        while line_no < len(self.netlist):
            line = self.netlist[line_no]
            if isinstance(line, SpiceCircuit):  # If it is a subcircuit it will simply ignore it.
                line_no += 1
                continue
            cmd = get_line_command(line)
            if cmd == '.PARAM':
                if search_param.search(line):
                    return line_no
            line_no += 1
        else:
            raise ParameterNotFoundError(f'Parameter "{param}" not found')

    def _get_subcircuit(self, subckt_name: str) -> 'SubCircuit':
        """Internal function. Do not use."""
        line_no = 0
        reg_subckt = re.compile(r".SUBCKT\s+{}".format(subckt_name), re.IGNORECASE)
        reg_lib = re.compile(r"^\.(LIB|INC)\s+(.*)$")
        libs_list = []
        while line_no < len(self.netlist):
            line = self.netlist[line_no]
            if isinstance(line, SpiceCircuit):  # If it is a subcircuit it will simply ignore it.
                m = reg_subckt.match(line.netlist[0])
                if m:
                    return line
            else:
                m = reg_lib.match(line)
                if m:     # For compatibility issues not using the walruss operator here
                    libs_list = m.group(1)
            line_no += 1
        # If we reached here is because the subciruit was not found. Search for it in declared libraries
        for lib in libs_list:
            if os.path.exists(lib):
                lib_filename = lib
            else:
                lib_filename = os.path.join(os.path.expanduser('~'),"Documents\\LTspiceXVII\\lib\\sub", lib)
                if not os.path.exists(lib_filename):
                    continue
            # If it reached here, we have a valid lib_filename
            subckt = SpiceEditor.find_subckt_in_lib(lib_filename, subckt_name)
            if subckt:
                return subckt
        else:
            # The search was not successful
            raise SubcircuitNotFoundError(f'Subcircuit "{subckt_name}" not found')


    def _set_model_and_value(self, component, value):
        """Internal function. Do not use."""
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regxstr = REPLACE_REGXES.get(prefix, None)  # Obtain RegX to make the update

        if regxstr is None:
            print("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            print("Got '{}'".format(component))
            return

        regex = re.compile(regxstr, re.IGNORECASE)
        if prefix == 'X':  # Relaces a component inside of a subciruit
            if SUBCIRCUIT_DIVIDER in component:
                subcircuit_ref, component = component.split(SUBCIRCUIT_DIVIDER, 2)
                line_no = self._getline_startingwith(subcircuit_ref)
                sub_circuit_instance = self.netlist[line_no]

                m = regex.search(sub_circuit_instance)
                if m:
                    subcircuit_name = m.group('value')  # last_token of the line before Params:

                    sub_circuit = self._get_subcircuit(subcircuit_name)
                    if sub_circuit:
                        # TODO:
                        #  1. Make a copy of the subcircuit in the netlist.
                        #  2. Memorize that the copy is relative to that particular instance
                        #  3. Change the copy of the subcircuit related to that particular instance.
                        sub_circuit._set_model_and_value(component, value)
                    return
                raise ComponentNotFoundError(component)
        #  prefix not None and prefix != 'X and sub
        if isinstance(value, (int, float)):
            value = format_eng(value)

        line_no = self._getline_startingwith(component)

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

    def get_component_info(self, component) -> dict:
        """
        Retrieves the component information as defined in the corresponding REGEX. The line number is also added.

        :param component: Reference of the component
        :type component: str
        :return: Dictionary with the component information
        :rtype: dict
        :raises: NotImplementedError when the line doesn't match the expected REGEX.
        """
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regxstr = REPLACE_REGXES.get(prefix, None)  # Obtain RegX to make the update

        if regxstr is None:
            self.logger.warning("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            self.logger.warning("Got '{}'".format(component))
            raise NotImplementedError("Unsuported prefex {}".format(prefix))

        line_no = self._getline_startingwith(component)
        regex = re.compile(regxstr, re.IGNORECASE)
        line = self.netlist[line_no]
        m = regex.match(line)
        if m is None:
            error_msg = 'Unsupported line "{}"\nExpected format is "{}"'.format(line, regxstr)
            self.logger.error(error_msg)
            raise NotImplementedError(error_msg)

        info = m.groupdict()
        info['line'] = line_no  # adding the line number to the component information
        return info

    def get_parameter(self, param: str) -> str:
        """
        Retrieves a Parameter from the Netlist

        :param param: Name of the parameter to be retrieved
        :type param: str
        :return: Value of the parameter being sought
        :rtype: str
        :raises: ParameterNotFoundError - In case the component is not found
        """
        param_def = self.netlist[self._get_param_line(param)]
        regx = re.compile(PARAM_REGX % param, re.IGNORECASE)
        m = regx.search(param_def, re.IGNORECASE)
        return m.group('value')

    def set_parameter(self, param: str, value: Union[str, int, float]) -> None:
        """Adds a parameter to the SPICE netlist.

        Usage: ::

         LTC.set_parameter("TEMP", 80)

        This adds onto the netlist the following line: ::

         .PARAM TEMP=80

        This is an alternative to the set_parameters which is more pythonic in it's usage,
        and allows setting more than one parameter at once.

        :param param: Spice Parameter name to be added or updated.
        :type param: str

        :param value: Parameter Value to be set.
        :type value: str, int or float

        :return: Nothing
        """
        try:
            param_line = self._get_param_line(param)
        except ParameterNotFoundError:
            # Was not found
            # the last two lines are typically (.backano and .end)
            insert_line = len(self.netlist) - 2
            self.netlist.insert(insert_line, '.PARAM {}={}  ; Batch instruction'.format(param, value) + END_LINE_TERM)
        else:
            regx = re.compile(PARAM_REGX % param, re.IGNORECASE)
            line = self.netlist[param_line]
            m = regx.search(line)
            if m:
                start, stop = m.span()
                self.netlist[param_line] = line[:start] + "{}={}".format(param, value) + line[stop:]
            else:
                raise ParameterNotFoundError

    def set_parameters(self, **kwargs):
        """Adds one or more parameters to the netlist.
        Usage: ::

            for temp in (-40, 25, 125):
                for freq in sweep_log(1, 100E3,):
                    LTC.set_parameters(TEMP=80, freq=freq)

        :key param_name:
            Key is the parameter to be set. values the ther corresponding values. Values can either be a str; an int or
            a float.

        :returns: Nothing
        """
        for param in kwargs:
            self.set_parameter(param, kwargs[param])

    def set_component_value(self, device: str, value: Union[str, int, float]) -> None:
        """Changes the value of a component, such as a Resistor, Capacitor or Inductor. For components inside
        subcircuits, use the subcirciut designator prefix with ':' as separator (Example X1:R1)
        Usage: ::

            LTC.set_component_value('R1', '3.3k')
            LTC.set_component_value('X1.C1', '10u')

        :param device: Reference of the circuit element to be updated.
        :type device: str
        :param value:
            value to be be set on the given circuit element. Float and integer values will automatically
            formatted as per the engineering notations 'k' for kilo, 'm', for mili and so on.
        :type value: str, int or float
        :raises:
            ComponentNotFoundError - In case the component is not found

            ValueError - In case the value doesn't correspond to the expected format

            NotImplementedError - In case the circuit element is defined in a format which is not supported by this
            version.

            If this is the case, use GitHub to start a ticket.  https://github.com/nunobrum/PyLTSpice
        """
        self._set_model_and_value(device, value)

    def set_element_model(self, element: str, model: str) -> None:
        """Changes the value of a circuit element, such as a diode model or a voltage supply.
        Usage: ::

            LTC.set_element_model('D1', '1N4148')
            LTC.set_element_model('V1' "SINE(0 1 3k 0 0 0)")

        :param element: Reference of the circuit element to be updated.
        :type element: str
        :param model: model name of the device to be updated
        :type model: str

        :raises:
            ComponentNotFoundError - In case the component is not found

            ValueError - In case the model format contains irregular characters

            NotImplementedError - In case the circuit element is defined in a format which is not supported by this version.

            If this is the case, use GitHub to start a ticket.  https://github.com/nunobrum/PyLTSpice
        """
        self._set_model_and_value(element, model)

    def get_component_value(self, element: str) -> str:
        """
        Returns the value of a component retrieved from the netlist.

        :param element: Reference of the circuit element to get the value.
        :type element: str

        :return: value of the circuit element .
        :rtype: str

        :raises: ComponentNotFoundError - In case the component is not found

                 NotImplementedError - for not supported operations
        """
        return self.get_component_info(element)['value']

    def get_component_floatvalue(self, element: str) -> str:
        """
        Returns the value of a component retrieved from the netlist.

        :param element: Reference of the circuit element to get the value in float format.
        :type element: str

        :return: value of the circuit element in float type
        :rtype: float

        :raises: ComponentNotFoundError - In case the component is not found

                 NotImplementedError - for not supported operations
        """
        return scan_eng(self.get_component_info(element)['value'])

    def get_component_nodes(self, elemment: str) -> List[str]:
        """
        Returns the nodes to which the component is attached to.

        :param elemment: Reference of the circuit element to get the nodes.
        :type elemment: str
        :return: List of nodes
        :rtype: list
        """
        nodes = self.get_component_info(element)['nodes']
        nodes = nodes.replace('\t', '')  # Remove any tabs if they exist
        nodes = nodes.replace('\r', '')  # Remove carriage returns
        nodes = nodes.replace('\n', '')  # Remove new lines
        # nodes = nodes.replace('+', '')  # Rem
        nodes = nodes.split(' ')  # Remove any spaces if they exist
        while('' in nodes):  # remove empty elements on the list
            nodes.remove('')
        return nodes

    def set_component_values(self, **kwargs):
        """
        Adds one or more components on the netlist. The argument is in the form of a key-value pair where each
        component designator is the key and the value is value to be set in the netlist.

        Usage 1: ::

         LTC.set_component_values(R1=330, R2="3.3k", R3="1Meg", V1="PWL(0 1 30m 1 30.001m 0 60m 0 60.001m 1)")

        Usage 2: ::

         value_settings = {'R1': 330, 'R2': '3.3k', 'R3': "1Meg", 'V1': 'PWL(0 1 30m 1 30.001m 0 60m 0 60.001m 1)'}
         LTC.set_component_values(**value_settings)

        :key <comp_ref>:
            The key is the component designator (Ex: V1) and the value is the value to be set. Values can either be
            strings; integers or floats

        :return: Nothing
        :raises: ComponentNotFoundError - In case one of the component is not found.
        """
        for value in kwargs:
            self.set_component_value(value, kwargs[value])

    def get_components(self, prefixes='*') -> list:
        """
        Returns a list of components that match the list of prefixes indicated on the parameter prefixes.
        In case prefixes is left empty, it returns all the ones that are defined by the REPLACE_REGEXES.
        The list will contain the designators of all components found.

        :param prefixes:
            Type of prefixes to search for. Examples: 'C' for capacitors; 'R' for Resistors; etc... See prefixes
            in SPICE documentation for more details.
            The default prefix is '*' which is a special case that returns all components.
        :type prefixes: str

        :return:
            A list of components matching the prefixes demanded.
        """
        answer = []
        if prefixes == '*':
            prefixes = ''.join(REPLACE_REGXES.keys())
        for line in self.netlist:
            if isinstance(line, SpiceCircuit):  # Only gets components from the main netlist,
                                                # it currently skips sub-circuits
                continue

            prefix = get_line_command(line)
            if prefix in prefixes:
                # regexvalue = re.compile(REPLACE_REGXES[prefix], re.IGNORECASE)
                # m = regexvalue.match(line)
                i = 1
                while line[i] not in (' ', '\t'):  # detects the first space of tab which means end of designator
                    i += 1
                answer.append(line[:i])  # Appends only the designators
        return answer

    def remove_component(self, designator: str):
        """
        Removes a component from  the design.
        Note: Current implemetation only alows removal of a component from the main netlist, not from a sub-circuit.

        :param designator: Component reference in the design. Ex: V1, C1, R1, etc...
        :type designator: str

        :return: Nothing
        :raises: ComponentNotFoundError - When the component doesn't exist on the netlist.
        """
        line = self._getline_startingwith(designator)
        self.netlist[line] = ''  # Blanks the line

    def get_all_nodes(self):
        # TODO: Implement a function that retrieves all nodes existing on a Netlist
        raise NotImplementedError("'get_all_nodes()' function not implemented")


class SpiceEditor(SpiceCircuit):
    """
    This class implements interfaces to manipulate SPICE netlist files. The class doesn't update the netlist file
    itself. After implementing the modifications the user should call the "write_netlist" method to write a new
    netlist file.
    :param netlist_file: Name of the .NET file to process
    """
    def __init__(self, netlist_file, encoding='autodetect'):
        SpiceCircuit.__init__(self)
        self.netlist_file = netlist_file
        if encoding == 'autodetect':
            self.encoding = detect_encoding(netlist_file)
        else:
            self.encoding = encoding

    def add_instruction(self, instruction: str) -> None:
        """Serves to add SPICE instructions to the simulation netlist. For example:

        .. code-block:: text

                  .tran 10m ; makes a transient simulation
                  .meas TRAN Icurr AVG I(Rs1) TRIG time=1.5ms TARG time=2.5ms" ; Establishes a measuring
                  .step run 1 100, 1 ; makes the simulation run 100 times

        :param instruction:
            Spice instruction to add to the netlist. This instruction will be added at the end of the netlist,
            typically just before the .BACKANNO statement
        :type instruction: str
        :return: Nothing
        """
        if not instruction.endswith(END_LINE_TERM):
            instruction += END_LINE_TERM
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

        # check whether the instruction is already there (dummy proofing)
        # TODO: if adding a .MODEL or .SUBCKT it should verify if it already exists and update it.
        if instruction not in self.netlist:
            # Insert before backanno instruction
            try:
                line = self.netlist.index('.backanno')
            except ValueError:
                line = len(self.netlist) - 2  # This is where typically the .backanno instruction is
            self.netlist.insert(line, instruction)

    def add_instructions(self, *instructions)->None:
        """Adds a list of instructions to the SPICE NETLIST.
        Example:
        ::

            LTC.add_instructions(
                ".STEP run -1 1023 1",
                ".dc V1 -5 5"
            )

        :param instructions: Argument list of instructions to add
        :type instructions: list
        :returns: Nothing
        """
        for instruction in instructions:
            self.add_instruction(instruction)

    def remove_instruction(self, instruction)->None:
        """Usage a previously added instructions.
        Example: ::

            LTC.remove_instruction(".STEP run -1 1023 1")

        :param instructions The list of instructions to remove. Each instruction is of the type 'str'
        :type instruction: str
        :returns: Nothing
        TODO: This only works with a full line instruction. Make it more inteligent so it recognizes .models, .param
        and .subckt
        """
        # Because the netlist is stored containing the end of line terminations and because they are added when they
        # they are added to the netlist.
        if not instruction.endswith(END_LINE_TERM):
            instruction += END_LINE_TERM

        self.netlist.remove(instruction)

    def write_netlist(self, run_netlist_file: str)->None:
        """
        Writes the netlist will all the requested updates into a file named <run_netlist_file>.
        :param run_netlist_file: File name of the netlist file.
        :type run_netlist_file: str
        :return Nothing
        """
        f = open(run_netlist_file, 'w', encoding=self.encoding)
        lines = iter(self.netlist)
        for line in lines:
            if isinstance(line, SpiceCircuit):
                line._write_lines(f)
            else:
                f.write(line)
        f.close()

    def reset_netlist(self)->None:
        """
        Removes all previous edits done to the netlist, i.e. resets it to the original state.

        :returns: Nothing
        """
        self.netlist = []
        if os.path.exists(self.netlist_file):
            with open(self.netlist_file, 'r', encoding=self.encoding, errors='replace') as f:
                lines = iter(f)  # Creates an iterator object to consume the file
                finished = self._add_lines(lines)
                if not finished:
                    raise SyntaxError("Netlist with missing .END or .ENDS statements")
                else:
                    for remainig_lines in lines:
                        print("Ignoring %s" % remainig_lines)
        else:
            self.logger.error("Netlist file not found")

    @staticmethod
    def find_subckt_in_lib(library, subckt_name) -> 'SpiceEditor':
        """Finds returns a Subckt from a library file"""
        # TODO: Implement This
        #  1. Find encoding
        #  2. scan the file
        #  3. Return an instance of SpiceEditor
        return None

if __name__ == '__main__':
    E = SpiceEditor('..\\tests\\Editor_Test.net')
    E.reset_netlist()
    print(E.get_component_value('R1'))
    print("Setting R1 to 10k")
    E.set_component_value('R1', 10000)
    print("Setting parameter I1 1.23k")
    E.set_parameter("I1", "1.23k")
    print(E.get_parameter('I1'))
    print("Setting {freq*(10/5.0})")
    E.set_parameters(I2="{freq*(10/5.0})")
    print(E.get_parameter('I2'))
    print(E.get_components())
    print(E.get_components('RC'))
    print("Setting C1 to 1µF")
    E.set_component_value("C1", '1µF')
    print("Setting C4 to 22nF")
    E.set_component_value("C4", 22e-9)
    print("Setting C3 to 120nF")
    E.set_component_value("C3", '120n')
    print(E.get_component_floatvalue("C1"))
    print(E.get_component_floatvalue("C3"))
    print(E.get_component_floatvalue("C4"))
    E.set_parameters(
            test_exiting_param_set1=24,
            test_exiting_param_set2=25,
            test_exiting_param_set3=26,
            test_exiting_param_set4=27,
            test_add_parameter=34.45,)
    E.write_netlist("..\\tests\\test_spice_editor.net")
