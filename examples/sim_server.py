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
# Name:        run_server.py
# Purpose:     A Command Line Interface to run the LTSpice Server
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     10-08-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import sys

from PyLTSpice.client_server.sim_server import SimServer
import time
import keyboard

from PyLTSpice.sim.ltspice_simulator import LTspice
simulator = LTspice

print("Starting Server")
server = SimServer(simulator, parallel_sims=4, output_folder='./temp', port=9000)
print("Server Started. Press and hold 'q' to stop")
while server.running():
    time.sleep(0.2)
    # Check whether a key was pressed
    if keyboard.is_pressed('q'):
        server.stop_server()
        break