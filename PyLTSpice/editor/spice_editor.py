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
# Purpose:     Class made to update Generic Spice netlists
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import logging
from pathlib import Path
from typing import Union, Callable, Any

_logger = logging.getLogger("spicelib.SpiceEditor")
_logger.info("This is maintained for compatibility issues. Use spicelib.editor.spice_editor instead")
from spicelib.editor.spice_editor import SpiceEditor as SpiceEditorBase, SpiceCircuit
from spicelib.simulators.ltspice_simulator import LTspice


class SpiceEditor(SpiceEditorBase):

    def __init__(self, netlist_file: Union[str, Path], encoding='autodetect', create_blank=False):
        netlist_file = Path(netlist_file)
        if netlist_file.suffix == ".asc":
            LTspice.create_netlist(netlist_file)
            netlist_file = netlist_file.with_suffix(".net")
        super().__init__(netlist_file, encoding, create_blank)

    def run(self, wait_resource: bool = True, callback: Callable[[str, str], Any] = None, timeout: float = 600,
            run_filename: str = None, simulator=None):
        if simulator is None:
            simulator = LTspice
        return super().run(wait_resource, callback, timeout, run_filename, simulator)

