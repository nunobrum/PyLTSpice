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
# Name:        srv_sim_runner.py
# Purpose:     Manager of the simulation threads on the server side
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-02-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import threading
import time
from typing import Any, Callable, Union
from pathlib import Path

from .sim_runner import SimRunner
from .spice_editor import SpiceEditor


class ServerSimRunner(threading.Thread):

    def __init__(self, parallel_sims: int = 4, timeout=None, verbose=True, output_folder: str = None, simulator=None):
        super().__init__(name="SimManager")
        self.runner = SimRunner(parallel_sims, timeout, verbose, output_folder, simulator)
        self.pending_tasks = []

    def run(self) -> None:
        while True:

            self.runner.updated_stats()
            time.sleep(1)

    def add_simulation(self, netlist: Union[str, Path, SpiceEditor], *,  wait_resource: bool = True,
            callback: Callable[[Path, Path], Any] = None,
            timeout: float = 600, run_filename: str = None):
        task = self.runner.run(netlist, wait_resource=wait_resource, callback=callback,
                               timeout=timeout, run_filename=run_filename)
