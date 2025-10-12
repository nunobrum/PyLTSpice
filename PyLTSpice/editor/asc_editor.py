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
import logging
from pathlib import Path
from typing import Union

_logger = logging.getLogger("spicelib.AscEditor")
_logger.info("This is maintained for backward compatibility. Use spicelib.editor.asc_editor instead")

from spicelib.editor.asc_editor import AscEditor as AscEditorBase

class AscEditor(AscEditorBase):

    def save_netlist(self, run_netlist_file: Union[str, Path]) -> None:
        """
        Saves the current netlist to a file.

        :param run_netlist_file: The path to the file where the netlist will be saved.
        :type run_netlist_file: str or Path
        """
        run_netlist_file = Path(run_netlist_file)
        if run_netlist_file.suffix in ('.net', '.cir'):
            # Forces use of LTSpice format when saving
            from spicelib.simulators.ltspice_simulator import LTspice
            LTspice.create_netlist(self.circuit_file)
            # Rename the generated .net file to the desired name if needed
            if run_netlist_file != self.circuit_file.with_suffix('.net'):
                self.circuit_file.with_suffix('.net').rename(run_netlist_file)
        else:
            super().save_netlist(run_netlist_file)
