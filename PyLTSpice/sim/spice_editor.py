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
# Name:        spice_editor.py
# Purpose:     Class made to update Generic Spice Netlists
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import os
from pathlib import Path
import traceback
import re
import logging
from math import log, floor
from typing import Union, List, Callable, Any
from ..utils.detect_encoding import detect_encoding

__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2021, Fribourg Switzerland"

END_LINE_TERM = '\n'  #: This controls the end of line terminator used
SUBCIRCUIT_DIVIDER = ':'  #: This controls the Subcircuit divider when setting component values inside subcircuits.
                          # Ex: Editor.set_component_value('XU1:R1', '1k')

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
    'C': r"^(?P<designator>C§?\w+)(?P<nodes>(\s+\S+){2})(?P<model>\s+\w+)?\s+(?P<value>({)?(?(6).*}|([0-9\.E+-]+(Meg|[kmuµnpf])?F?))).*$",  # Capacitor
    'D': r"^(?P<designator>D§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>\w+).*$",  # Diode
    'E': r"^(?P<designator>E§?\w+)(?P<nodes>(\s+\S+){2,4})\s+(?P<value>.*)$",  # Voltage Dependent Voltage Source
                                                        # this only supports changing gain values
    'F': r"^(?P<designator>F§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Current Dependent Current Source
                                                        # This implementation replaces everything after the 2 first nets
    'G': r"^(?P<designator>G§?\w+)(?P<nodes>(\s+\S+){2,4})\s+(?P<value>.*)$",  # Voltage Dependent Current Source
                                                        # This only supports changing gain values
    'H': r"^(?P<designator>H§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Voltage Dependent Current Source
                                                        # This implementation replaces everything after the 2 first nets
    'I': r"^(?P<designator>I§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Current Source
                                                        # This implementation replaces everything after the 2 first nets
    'J': r"^(?P<designator>J§?\w+)(?P<nodes>(\s+\S+){3})\s+(?P<value>\w+).*$",  # JFET
    'K': r"^(?P<designator>K§?\w+)(?P<nodes>(\s+\S+){2,4})\s+(?P<value>[\+\-]?[0-9\.E+-]+[kmuµnpf]?).*$",  # Mutual Inductance
    'L': r"^(?P<designator>L§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>({)?(?(5).*}|([0-9\.E+-]+(Meg|[kmuµnpf])?H?))).*$",  # Inductance
    'M': r"^(?P<designator>M§?\w+)(?P<nodes>(\s+\S+){3,4})\s+(?P<value>\w+).*$",  # MOSFET TODO: Parameters substitution not supported
    'O': r"^(?P<designator>O§?\w+)(?P<nodes>(\s+\S+){4})\s+(?P<value>\w+).*$",  # Lossy Transmission Line TODO: Parameters substitution not supported
    'Q': r"^(?P<designator>Q§?\w+)(?P<nodes>(\s+\S+){3,4})\s+(?P<value>\w+).*$",  # Bipolar TODO: Parameters substitution not supported
    'R': r"^(?P<designator>R§?\w+)(?P<nodes>(\s+\S+){2})(?P<model>\s+\w+)?\s+(?P<value>({)?(?(6).*}|([0-9\.E+-]+(Meg|[kmuµnpf])?R?)\d*)).*$", # Resistors
    'S': r"^(?P<designator>S§?\w+)(?P<nodes>(\s+\S+){4})\s+(?P<value>.*)$",  # Voltage Controlled Switch
    'T': r"^(?P<designator>T§?\w+)(?P<nodes>(\s+\S+){4})\s+(?P<value>.*)$",  # Lossless Transmission
    'U': r"^(?P<designator>U§?\w+)(?P<nodes>(\s+\S+){3})\s+(?P<value>.*)$",  # Uniform RC-line
    'V': r"^(?P<designator>V§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Voltage Source
                                                        # This implementation replaces everything after the 2 first nets
    'W': r"^(?P<designator>W§?\w+)(?P<nodes>(\s+\S+){2})\s+(?P<value>.*)$",  # Current Controlled Switch
                                                        # This implementation replaces everything after the 2 first nets
    'X': r"^(?P<designator>X§?\w+)(?P<nodes>(\s+\S+){1,99}?)\s+(?P<value>\w+)(\s+params:)?(?P<params>(\s+\w+\s*=\s*[\d\w\{\}\(\)\-\+\*/]+)*)\s*\\?$",  # Sub-circuit, Parameter substitution not supported
    'Z': r"^(?P<designator>Z§?\w+)(?P<nodes>(\s+\S+){3})\s+(?P<value>\w+).*$",  # MESFET and IBGT. TODO: Parameters substitution not supported
    '@': r"^(?P<designator>@§?\d+)(?P<nodes>(\s+\S+){2})\s?(?P<params>(.*)*)$",  # Frequency Noise Analysis (FRA) wiggler
    # pattern = r'^@(\d+)\s+(\w+)\s+(\w+)(?:\s+delay=(\d+\w+))?(?:\s+fstart=(\d+\w+))?(?:\s+fend=(\d+\w+))?(?:\s+oct=(\d+))?(?:\s+fcoarse=(\d+\w+))?(?:\s+nmax=(\d+\w+))?\s+(\d+)\s+(\d+\w+)\s+(\d+)(?:\s+pp0=(\d+\.\d+))?(?:\s+pp1=(\d+\.\d+))?(?:\s+f0=(\d+\w+))?(?:\s+f1=(\d+\w+))?(?:\s+tavgmin=(\d+\w+))?(?:\s+tsettle=(\d+\w+))?(?:\s+acmag=(\d+))?$'
}


PARAM_REGEX = r"(?<= )(?P<replace>%s(\s*=\s*)(?P<value>[\w\*\/\.\+\-\/\*\{\}\(\)\t ]*))(?<!\s)($|\s+)(?!\s*=)"
SUBCKT_CLAUSE_FIND = r"^.SUBCKT\s+"

# Code Optimization objects, avoiding repeated compilation of regular expressions
component_replace_regexs = {prefix: re.compile(pattern, re.IGNORECASE) for prefix, pattern in REPLACE_REGXES.items()}
subcircuit_regex = re.compile(r"^.SUBCKT\s+(?P<name>\w+)", re.IGNORECASE)
lib_inc_regex = re.compile(r"^\.(LIB|INC)\s+(.*)$", re.IGNORECASE)

LibSearchPaths = []


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
    value = value.strip()
    x = len (value)
    while x > 0:
        if value[x-1] in "0123456789":
            break
        x -= 1
    suffix = value[x:]  # this is the non numeric part at the end
    f = float(value[:x])  # this is the numeric part. Can raise ValueError.
    if suffix:
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
            return f * 1E+6
    return f


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
    def __init__(self, parameter):
        super().__init__(f'Parameter "{parameter}" not found')


class UnrecognizedSyntaxError(Exception):
    """Line doesn't match expected Spice syntax"""
    def __init__(self, line, regex):
        super().__init__(f'Line: "{line}" doesn\'t match regular expression "{regex}"')


class MissingExpectedClauseError(Exception):
    """Missing expected clause in Spice netlist"""



class SpiceCircuit(object):
    """
    The Spice Circuit represents subcircuits within a SPICE circuit and since subcircuits can have subcircuits inside
    them, it serves as base for the top level netlist. See class SpiceEditor
    This hierarchical approach helps to encapsulate and protect parameters and components from edits made at a higher
    level.

    The netlist information is stored in a list, each element of the list corresponds to a SPICE instruction.
    If an instruction spawns more than a line with the '+' operator, it is contained in the same element.

    This class serves as subclass to the SpiceEditor class.
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
            if isinstance(line, SpiceCircuit):  # If it is a subcircuit it will simply ignore it.
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

    def _get_line_matching(self, command, search_expression):
        """
        Internal function. Do not use. Returns a line starting with command and matching the search with the regular
        expression
        """
        in_param_line = False  # This is needed to process multi-line commands
        line_no = 0
        while line_no < len(self.netlist):
            line = self.netlist[line_no]
            if isinstance(line, SpiceCircuit):  # If it is a subcircuit it will simply ignore it.
                line_no += 1
                continue
            cmd = get_line_command(line)
            if cmd == command:
                match = search_expression.search(line)
                if match:
                    return line_no, match
            line_no += 1
        return -1, None  # If it fails, it returns an invalid line number and No match

    def _get_subcircuit(self, instance_name: str) -> 'SpiceCircuit':
        """Internal function. Do not use."""
        global LibSearchPaths
        if SUBCIRCUIT_DIVIDER in instance_name:
            subcircuit_ref, sub_subcircuits = instance_name.split(SUBCIRCUIT_DIVIDER, 1)
        else:
            subcircuit_ref = instance_name

        line_no = self._getline_startingwith(subcircuit_ref)
        sub_circuit_instance = self.netlist[line_no]
        regex = component_replace_regexs['X'] # The subcircuit instance regex
        m = regex.search(sub_circuit_instance)
        if m:
            subcircuit_name = m.group('value')  # last_token of the line before Params:
        else:
            raise UnrecognizedSyntaxError(sub_circuit_instance, REPLACE_REGXES['X'])

        line_no = 0
        reg_subckt = re.compile(SUBCKT_CLAUSE_FIND + subcircuit_name, re.IGNORECASE)

        libs_list = []
        sub_circuit = None
        while line_no < len(self.netlist):
            line = self.netlist[line_no]
            if isinstance(line, SpiceCircuit) and line.name() == subcircuit_name:
                sub_circuit = line # The circuit was already found
                break
            else:
                m = lib_inc_regex.match(line)
                if m:     # For compatibility issues not using the walruss operator here
                    libs_list.append( m.group(2) )
            line_no += 1
        if sub_circuit is None:
            # If we reached here is because the subciruit was not found. Search for it in declared libraries
            libs_list_full_path = []
            for lib in libs_list:
                if os.path.exists(lib):
                    libs_list_full_path.append(lib)
                    continue
                lib_filename = os.path.join(os.path.expanduser('~'),"Documents\\LTspiceXVII\\lib\\sub", lib)
                if os.path.exists(lib_filename):
                    libs_list_full_path.append(lib)
                    continue
                for path in LibSearchPaths:
                    lib_filename= os.path.join(path, lib)
                    if os.path.exists(lib_filename):
                        libs_list_full_path.append(lib_filename)
                        continue


            # If it reached here, we have a valid lib_filename
            for lib_path in libs_list_full_path:
                sub_circuit = SpiceEditor.find_subckt_in_lib(lib_path, subcircuit_name)
                if sub_circuit:
                    break
        if sub_circuit:
            if SUBCIRCUIT_DIVIDER in instance_name:
                return sub_circuit._get_subcircuit(sub_subcircuits)
            else:
                return sub_circuit
        else:
            # The search was not successful
            raise ComponentNotFoundError(f'Subcircuit "{subcircuit_name}" not found')

    def _set_model_and_value(self, component, value):
        """Internal function. Do not use."""
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regex = component_replace_regexs.get(prefix, None)  # Obtain RegX to make the update

        if regex is None:
            print("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            print("Got '{}'".format(component))
            return

        if isinstance(value, (int, float)):
            value = format_eng(value)

        line_no = self._getline_startingwith(component)

        line = self.netlist[line_no]
        m = regex.match(line)
        if m is None:
            raise UnrecognizedSyntaxError(line, REPLACE_REGXES[prefix])
            # print("Unsupported line ""{}""".format(line))
        else:
            start = m.start('value')
            end = m.end('value')
            self.netlist[line_no] = line[:start] + value + line[end:]

    def clone(self, **kwargs) -> 'SpiceCircuit':
        """
        Creates a new copy of the SpiceCircuit. Change done at the new copy are not affecting the original
        
        :key new_name: The new name to be given to the circuit
        :type new_name: str
        :return: The new replica of the SpiceCircuit object
        :rtype: SpiceCircuit
        """
        clone = SpiceCircuit()
        clone.netlist = self.netlist.copy()
        clone.netlist.insert(0, "***** SpiceEditor Manipulated this subcircuit ****" + END_LINE_TERM)
        clone.netlist.append("***** ENDS SpiceEditor ****" + END_LINE_TERM)
        new_name = kwargs.get('new_name', None)
        if new_name:  # If it is different from None
            clone.setname(new_name)
        return clone

    def name(self) -> str:
        """
        Returns the name of the Sub-Circuit -> str.

        :rtype: str
        """
        if len(self.netlist):
            for line in self.netlist:
                m = subcircuit_regex.search(line)
                if m:
                    return m.group('name')
            else:
                raise RuntimeError("Unable to find .SUBCKT clause in subcircuit")
        else:
            raise RuntimeError("Empty Subcircuit")
    
    def setname(self, new_name: str):
        """
        Renames the subcircuit to a new name. No check is done to the new game give. It is up to the user to make sure 
        that the new name is valid.
        
        :param new_name: The new Name.
        :type new_name: str 
        :return: Nothing
        :rtype: None
        """
        if len(self.netlist):
            lines = len(self.netlist)
            line_no = 0
            while line_no < lines:
                line = self.netlist[line_no]
                m = subcircuit_regex.search(line)
                if m:
                    # Replacing the name in the SUBCKT Clause
                    start = m.start('name')
                    end = m.end('name')
                    self.netlist[line_no] = line[:start] + new_name + line[end:]
                    break
                line_no += 1
            else:
                raise MissingExpectedClauseError("Unable to find .SUBCKT clause in subcircuit")

            # This second loop finds the .ENDS clause
            while line_no < lines:
                line = self.netlist[line_no]
                if get_line_command(line) == '.ENDS':
                    self.netlist[line_no] = '.ENDS ' + new_name + END_LINE_TERM
                    break
                line_no += 1
            else:
                raise MissingExpectedClauseError("Unable to find .SUBCKT clause in subcircuit")
        else:
            # Avoiding exception by creating an empty subcircuit
            self.netlist.app("* SpiceEditor Created this subcircuit")
            self.netlist.append('.SUBCKT %s%s' % (new_name, END_LINE_TERM))
            self.netlist.append('.ENDS %s%s' % (new_name, END_LINE_TERM))
        
    def get_component_info(self, component) -> dict:
        """
        Retrieves the component information as defined in the corresponding REGEX. The line number is also added.

        :param component: Reference of the component
        :type component: str
        :return: Dictionary with the component information
        :rtype: dict
        :raises: UnrecognizedSyntaxError when the line doesn't match the expected REGEX. NotImplementedError of there
                 isn't an associated regular expression for the component prefix.
        """
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regex = component_replace_regexs.get(prefix, None)  # Obtain RegX to make the update

        if regex is None:
            self.logger.warning("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            self.logger.warning("Got '{}'".format(component))
            raise NotImplementedError("Unsuported prefix {}".format(prefix))

        line_no = self._getline_startingwith(component)
        line = self.netlist[line_no]
        m = regex.match(line)
        if m is None:
            error_msg = 'Unsupported line "{}"\nExpected format is "{}"'.format(line, REPLACE_REGXES[prefix])
            self.logger.error(error_msg)
            raise UnrecognizedSyntaxError(line, REPLACE_REGXES[prefix])

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
        regx = re.compile(PARAM_REGEX % param, re.IGNORECASE)
        line_no, match = self._get_line_matching('.PARAM', regx)
        if match:
            return match.group('value')
        else:
            raise ParameterNotFoundError(param)

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
        regx = re.compile(PARAM_REGEX % param, re.IGNORECASE)
        param_line, match = self._get_line_matching('.PARAM', regx)
        if match:
            start, stop = match.span(regx.groupindex['replace'])
            line = self.netlist[param_line]
            self.netlist[param_line] = line[:start] + "{}={}".format(param, value) + line[stop:]
        else:
            # Was not found
            # the last two lines are typically (.backano and .end)
            insert_line = len(self.netlist) - 2
            self.netlist.insert(insert_line, '.PARAM {}={}  ; Batch instruction'.format(param, value) + END_LINE_TERM)

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
            LTC.set_component_value('X1:C1', '10u')

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

    def get_component_nodes(self, element: str) -> List[str]:
        """
        Returns the nodes to which the component is attached to.

        :param element: Reference of the circuit element to get the nodes.
        :type element: str
        :return: List of nodes
        :rtype: list
        """
        nodes = self.get_component_info(element)['nodes']
        nodes = nodes.split( )  # Remove any spaces if they exist. This considers \r \n \t characters as well
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
            tokens = line.split()
            try:
                if tokens[0][0] in prefixes:
                    answer.append(tokens[0])  # Appends only the designators
            except IndexError or TypeError:
                pass
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

    @staticmethod
    def add_library_search_paths(paths):
        """
        Adding search paths for libraries. By default the local directory and the
        ~username/"Documents/LTspiceXVII/lib/sub will be searched forehand. Only when a library is not found in these
        paths then the paths added by this method will be searched.
        Alternatively PyLTSpice.SpiceEditor.LibSearchPaths.append(paths) can be used."

        :param paths: Path to add to the Search path
        :type paths: str
        :return: Nothing
        :rtype: None
        """
        global LibSearchPaths
        if isinstance(paths, str):
            LibSearchPaths.append(paths)
        elif isinstance(paths, list):
            LibSearchPaths += paths

    def get_all_nodes(self) -> List[str]:
        """
        A function that retrieves all nodes existing on a Netlist

        :returns: Circuit Nodes
        :rtype: list[str]
        """
        circuit_nodes = []
        for line in self.netlist:
            prefix = get_line_command(line)
            if prefix in component_replace_regexs:
                match = component_replace_regexs[prefix].match(line)
                if match:
                    nodes = match.group('nodes').split()  # This separates by all space characters including \t
                    for node in nodes:
                        if node not in circuit_nodes:
                            circuit_nodes.append(node)
        return circuit_nodes


class SpiceEditor(SpiceCircuit):
    """
    This class implements interfaces to manipulate SPICE netlist files. The class doesn't update the netlist file
    itself. After implementing the modifications the user should call the "write_netlist" method to write a new
    netlist file.

    :param netlist_file: Name of the .NET file to parse
    :type netlist_file: str or Path
    :param encoding: Forcing the encoding to be used on the circuit netlile read. Defaults to 'autodetect' which will
        call a function that tries to detect the encoding automatically. This however is not 100% fool proof.
    :type encoding: str, optional
    """
    def __init__(self, netlist_file: Union[str, Path], encoding='autodetect'):
        super().__init__()
        self.netlist_file = Path(netlist_file)
        if self.netlist_file.suffix == '.asc':
            from .ltspice_simulator import LTspice

            self.netlist_file = LTspice.create_netlist(self.netlist_file)
        self.modified_subcircuits = {}
        if encoding == 'autodetect':
            self.encoding = detect_encoding(self.netlist_file, '*')  # Normally the file will start with a '*'
        else:
            self.encoding = encoding
        self.reset_netlist()

    def _set_model_and_value(self, component, value):
        prefix = component[0]  # Using the first letter of the component to identify what is it
        if prefix == 'X' and SUBCIRCUIT_DIVIDER in component:  # Relaces a component inside of a subciruit
            # In this case the subcircuit needs to be copied so that is copy is modified. A copy is created for each
            # instance of a subcircuit.
            component_split = component.split(SUBCIRCUIT_DIVIDER)
            modified_path = SUBCIRCUIT_DIVIDER.join(component_split[:-1])  # excludes last component
            component = component_split[-1] # This is the last component to modify

            if modified_path in self.modified_subcircuits:  # See if this was already a modified subcircuit instance
                sub_circuit = self.modified_subcircuits[modified_path]
            else:
                sub_circuit_original = self._get_subcircuit(modified_path)  # If not will look of it.
                if sub_circuit_original:
                    new_name = sub_circuit_original.name() + '_' + '_'.join(component_split[:-1])  # Creates a new name with the path appended
                    sub_circuit = sub_circuit_original.clone(new_name=new_name)
                    # Memorize that the copy is relative to that particular instance
                    self.modified_subcircuits[modified_path] = sub_circuit
                    # Change the call to the subcircuit
                    self._set_model_and_value(modified_path, new_name)
                else:
                    raise ComponentNotFoundError(component)
            #  Change the copy of the subcircuit related to that particular instance.
            sub_circuit._set_model_and_value(component, value)
            return
        # else: This is the generic case where the subcircuit is changed
        super()._set_model_and_value(component, value)

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
                line = self.netlist.index('.backanno\n')  # TODO: Improve this. END of line termination could be differnt and case as well
            except ValueError:
                line = len(self.netlist) - 2  # This is where typically the .backanno instruction is
            self.netlist.insert(line, instruction)

    def add_instructions(self, *instructions) -> None:
        """Adds a list of instructions to the SPICE NETLIST.
        Example:
        ::

            LTC.add_instructions(
                ".STEP run -1 1023 1",
                ".dc V1 -5 5"
            )

        :param instructions: Argument list of instructions to add
        :type instructions: argument list
        :returns: Nothing
        """
        for instruction in instructions:
            self.add_instruction(instruction)

    def remove_instruction(self, instruction)->None:
        """Usage a previously added instructions.
        Example: ::

            LTC.remove_instruction(".STEP run -1 1023 1")

        This only works if the instruction exactly matches the line on the netlist. This means that space characters,
        and upper case and lower case differences will not match the line.

        :param instruction: The list of instructions to remove. Each instruction is of the type 'str'
        :type instruction: str
        :returns: Nothing
        """
        # TODO: Make it more inteligent so it recognizes .models, .param
        #  and .subckt
        # Because the netlist is stored containing the end of line terminations and because they are added when they
        # they are added to the netlist.
        if not instruction.endswith(END_LINE_TERM):
            instruction += END_LINE_TERM

        self.netlist.remove(instruction)

    def write_netlist(self, run_netlist_file: 'Path') -> None:
        """
        Writes the netlist will all the requested updates into a file named <run_netlist_file>.

        :param run_netlist_file: File name of the netlist file.
        :type run_netlist_file: Path
        :returns: Nothing
        """
        with run_netlist_file.open('w', encoding=self.encoding) as f:
            lines = iter(self.netlist)
            for line in lines:
                if isinstance(line, SpiceCircuit):
                    line._write_lines(f)
                else:
                    # Writes the modified subcircuits at the end just before the .END clause
                    if line.upper().startswith(".END"):
                        # write here the modified subcircuits
                        for sub in self.modified_subcircuits.values():
                            sub._write_lines(f)
                    f.write(line)

    def reset_netlist(self) -> None:
        """
        Removes all previous edits done to the netlist, i.e. resets it to the original state.

        :returns: Nothing
        """
        self.netlist.clear()
        self.modified_subcircuits.clear()
        if self.netlist_file.exists():
            with self.netlist_file.open('r', encoding=self.encoding, errors='replace') as f:
                lines = iter(f)  # Creates an iterator object to consume the file
                finished = self._add_lines(lines)
                if not finished:
                    raise SyntaxError("Netlist with missing .END or .ENDS statements")
                # else:
                #     for _ in lines:  # Consuming the rest of the file.
                #         pass  # print("Ignoring %s" % _)
        else:
            self.logger.error("Netlist file not found")

    @staticmethod
    def find_subckt_in_lib(library, subckt_name) -> Union['SpiceCircuit', None]:
        """
        Finds returns a Subckt from a library file.

        :param library: path to the library to search
        :type library: str
        :param subckt_name: Subcircuit to search for
        :type subckt_name: str
        :return: Returns a SpiceCircuit instance with the subcircuit found or None if not found
        :rtype: SpiceCircuit
        """
        # 0. Setup things
        reg_subckt = re.compile(SUBCKT_CLAUSE_FIND + subckt_name, re.IGNORECASE)
        # 1. Find Encoding
        encoding = detect_encoding(library)
        #  2. scan the file
        with open(library, encoding=encoding) as lib:
            for line in lib:
                search = reg_subckt.match(line)
                if search:
                    sub_circuit = SpiceCircuit()
                    sub_circuit.netlist.append(line)
                    # Advance to the next non nested .ENDS
                    finished = sub_circuit._add_lines(lib)
                    if finished:
                        return sub_circuit
        #  3. Return an instance of SpiceCircuit
        return None

    def run(self, wait_resource: bool = True,
            callback: Callable[[str, str], Any] = None, timeout: float = 600, run_filename: str = None, simulator=None):
        """
        *(Deprecated)*

        Convenience function for maintaining legacy with legacy code.
        """
        from .sim_runner import SimRunner
        Sim = SimRunner()
        return Sim.run(self, wait_resource=wait_resource, callback=callback, timeout=timeout, run_filename=run_filename)


if __name__ == '__main__':
    E = SpiceEditor(os.path.abspath('..\\tests\\PI_Filter_resampled.net'))
    E.add_instruction(".nodeset V(N001)=0")
    E.write_netlist('..\\tests\\PI_Filter_resampled_mod.net')
    E = SpiceEditor('..\\tests\\Editor_Test.net')
    print("Circuit Nodes", E.get_all_nodes())
    E.add_library_search_paths([r"C:\SVN\Electronic_Libraries\LTSpice\lib"])
    E.set_element_model("XU2", 324)
    E.set_component_value("XU1:XDUT:R77", 200)
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
