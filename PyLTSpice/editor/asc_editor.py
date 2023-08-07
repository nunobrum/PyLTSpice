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
# Name:        asc_editor.py
# Purpose:     Class made to update directly the ltspice ASC files
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
from pathlib import Path
from typing import Union, Tuple, List
import re
import logging
from .base_editor import BaseEditor, format_eng, ComponentNotFoundError, ParameterNotFoundError, PARAM_REGEX, \
    UNIQUE_SIMULATION_DOT_INSTRUCTIONS

_logger = logging.getLogger("PyLTSpice.AscEditor")

TEXT_REGEX = re.compile(r"TEXT (\d+)\s+(\d+)\s+(Left|Right|Top|Bottom)\s\d+\s*(?P<type>[!;])(?P<text>.*)",
                        re.IGNORECASE)
TEXT_REGEX_X = 1
TEXT_REGEX_Y = 2
TEXT_REGEX_ALIGN = 3
TEXT_REGEX_TYPE = 4
TEXT_REGEX_TEXT = 5

END_LINE_TERM = "\n"


class AscEditor(BaseEditor):
    """Class made to update directly the ltspice ASC files"""

    def __init__(self, asc_file: str):
        self._asc_file_path = Path(asc_file)
        self._asc_file_lines: List[str] = []
        self._symbols = {}
        self._texts = []  # This is only here to avoid cycling over the netlist everytime we need to retrieve the texts
        if not self._asc_file_path.exists():
            raise FileNotFoundError(f"File {asc_file} not found")
        # read the file into memory
        self.reset_netlist()

    def write_netlist(self, run_netlist_file: Union[str, Path]) -> None:
        with open(run_netlist_file, 'w') as asc_file:
            asc_file.writelines(self._asc_file_lines)

    def reset_netlist(self):
        with open(self._asc_file_path, 'r') as asc_file:
            self._asc_file_lines = asc_file.readlines()
        self._parse_asc_file()

    def _parse_asc_file(self):
        symbol_attributes = {}
        self._symbols = {}
        self._texts = []
        for line_no, line in enumerate(self._asc_file_lines):
            if line.startswith("SYMBOL"):
                tokens = line.split()
                if symbol_attributes:
                    self._symbols[symbol_attributes["InstName"]] = symbol_attributes
                symbol_attributes = {'Name': tokens[1], 'line': line_no}
            elif line.startswith("SYMATTR"):
                tokens = line.split()
                if symbol_attributes:
                    symbol_attributes[tokens[1]] = tokens[2]
            elif line.startswith("TEXT"):
                match = TEXT_REGEX.match(line)
                if match and match.group(TEXT_REGEX_TYPE) == "!":
                    text = match.group(TEXT_REGEX_TEXT)
                    self._texts.append((line_no, text.strip()))

        if symbol_attributes:
            self._symbols[symbol_attributes["InstName"]] = symbol_attributes

    def get_component_info(self, component) -> dict:
        """Returns the component information as a dictionary"""
        return self._symbols[component]

    def _get_line_matching(self, command, search_expression: re.Pattern) -> Tuple[int, Union[re.Match, None]]:
        command_upped = command.upper()
        for line_no, line in self._texts:
            if line.upper().startswith(command_upped):
                match = search_expression.search(line)
                if match:
                    return line_no, match
        else:
            return -1, None

    def get_parameter(self, param: str) -> str:
        param_regex = re.compile(PARAM_REGEX % param, re.IGNORECASE)
        line_no, match = self._get_line_matching(".PARAM", param_regex)
        if match:
            return match.group('value')
        else:
            raise ParameterNotFoundError(f"Parameter {param} not found in ASC file")

    def set_parameter(self, param: str, value: Union[str, int, float]) -> None:
        param_regex = re.compile(PARAM_REGEX % param, re.IGNORECASE)
        line_no, match = self._get_line_matching(".PARAM", param_regex)
        if match:
            value_str = format_eng(value)
            line: str = self._asc_file_lines[line_no]
            match = param_regex.search(line)  # repeating the search so we update the correct start/stop parameter
            start, stop = match.span(param_regex.groupindex['replace'])
            self._asc_file_lines[line_no] = line[:start] + "{}={}".format(param, value) + line[stop:]
        else:
            # Was not found so we need to add it,
            self.add_instruction('TEXT 296 488 Left 2 !.param temp = 0'.format(param, value) + END_LINE_TERM)
        self._parse_asc_file()

    def set_component_value(self, device: str, value: Union[str, int, float]) -> None:
        start = self._symbols[device]['line']
        for offset, line in enumerate(self._asc_file_lines[start:]):
            if line.startswith("SYMATTR Value"):
                if isinstance(value, str):
                    value_str = value
                else:
                    value_str = format_eng(value)
                self._asc_file_lines[start + offset] = "SYMATTR Value {}".format(value_str) + END_LINE_TERM
                self._parse_asc_file()
                break
        else:
            raise ComponentNotFoundError(f"Component {device} not found in ASC file")

    def set_element_model(self, element: str, model: str) -> None:
        self.set_component_value(element, model)

    def get_component_value(self, element: str) -> str:
        if element not in self._symbols:
            raise ComponentNotFoundError(f"Component {element} not found in ASC file")
        return self.get_component_info(element)["Value"]

    def get_components(self, prefixes='*') -> list:
        """Returns a list of components with the given prefix"""
        if prefixes == '*':
            return list(self._symbols.keys())
        return [k for k in self._symbols.keys() if k.startswith(prefixes)]

    def remove_component(self, designator: str):
        if designator not in self._symbols:
            raise ComponentNotFoundError(f"Component {designator} not found in ASC file")
        line_start = self._symbols[designator]['line']
        for line_no in self._asc_file_lines[line_start:]:
            if line_no.startswith("SYMBOL") or line_no.startswith("WINDOW") or line_no.startswith("SYMATTR"):
                self._asc_file_lines[line_no] = ""  # removes the line without touching the line number
            else:
                break  # If another line is found, then it is the start of another component
        self._parse_asc_file()

    def _get_text_space(self):
        """
        Returns the coordinate on the Schematic File canvas where a text can be appended.
        """
        min_x = 0
        max_x = 0
        min_y = 0
        max_y = 0
        for line in self._asc_file_lines:
            if line.startswith("SHEET"):
                x, y = line.split()[2:4]
                min_x = max_x = int(x)
                min_y = max_y = int(y)
            elif line.startswith("WIRE"):
                x1, y1, x2, y2 = [int(x) for x in line.split()[1:5]]
                min_x = min(min_x, x1, x2)
                max_x = max(max_x, x1, x2)
                min_y = min(min_y, y1, y2)
                max_y = max(max_y, y1, y2)
            elif line.startswith("FLAG") or line.startswith("TEXT"):
                x1, y1 = [int(x) for x in line.split()[1:3]]
                min_x = min(min_x, x1)
                min_y = min(min_y, y1)
            elif line.startswith("SYMBOL"):
                x1, y1 = [int(x) for x in line.split()[2:4]]
                min_x = min(min_x, x1)
                min_y = min(min_y, y1)

        return min_x, max_y + 100

    def add_instruction(self, instruction: str) -> None:
        instruction = instruction.strip()  # Clean any end of line terminators
        command = instruction.split()[0].upper()

        if command in UNIQUE_SIMULATION_DOT_INSTRUCTIONS:
            # Before adding new instruction, if it is a unique instruction, we just replace it
            i = 0
            while i < len(self._texts):
                line_no, line = self._texts[i]
                command = line.split()[0].upper()
                if command in UNIQUE_SIMULATION_DOT_INSTRUCTIONS:
                    line = self._asc_file_lines[line_no]
                    self._asc_file_lines[line_no] = line[:line.find("!")] + instruction + END_LINE_TERM
                    self._parse_asc_file()
                    return  # Job done, can exit this method
                i += 1
        elif command.startswith('.PARAM'):
            raise RuntimeError('The .PARAM instruction should be added using the "set_parameter" method')
        # If we get here, then the instruction was not found, so we need to add it
        x, y = self._get_text_space()
        self._asc_file_lines.append("TEXT {} {} Left 2 !{}".format(x, y, instruction) + END_LINE_TERM)
        self._parse_asc_file()


