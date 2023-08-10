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
import argparse
from PyLTSpice.client_server.sim_server import SimServer
import time
import keyboard


def main():
    parser = argparse.ArgumentParser(
        description="Run the LTSpice Server. This is a command line interface to the SimServer class."
                    "The SimServer class is used to run simulations in parallel using a server-client architecture."
                    "The server is a machine that runs the SimServer class and the client is a machine that runs the "
                    "SimClient class."
                    "The argument is the simulator to be used (LTSpice, NGSpice, XYCE, etc.)"
    )
    parser.add_argument('simulator', type=str, default="LTSpice",
                        help="Simulator to be used (LTSpice, NGSpice, XYCE, etc.)")
    parser.add_argument("-p", "--port", type=int, default=9000,
                        help="Port to run the server. Default is 9000")
    parser.add_argument("-o", "--output", type=str, default=".",
                        help="Output folder for the results. Default is the current folder")
    parser.add_argument("-l", "--parallel", type=int, default=4,
                        help="Maximum number of parallel simulations. Default is 4")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    if args.parallel < 1:
        args.parallel = 1

    if args.simulator == "LTSpice":
        from PyLTSpice.sim.ltspice_simulator import LTspice
        simulator = LTspice
    elif args.simulator == "NGSpice":
        from PyLTSpice.sim.ngspice_simulator import NGSpice
        simulator = NGSpice
    elif args.simulator == "XYCE":
        from PyLTSpice.sim.xyce_simulator import Xyce
        simulator = Xyce
    else:
        raise ValueError(f"Simulator {args.simulator} is not supported")
        exit(-1)

    print("Starting Server")
    server = SimServer(simulator, parallel_sims=args.parallel, output_folder=args.output, port=args.port)
    print("Server Started. Press and hold 'q' to stop")
    while server.running():
        time.sleep(0.2)
        # Check whether a key was pressed
        if keyboard.is_pressed('q'):
            server.stop_server()
            break


if __name__ == "__main__":
    import logging
    log1 = logging.getLogger("PyLTSpice.ServerSimRunner")
    log2 = logging.getLogger("PyLTSpice.SimServer")
    log3 = logging.getLogger("PyLTSpice.SimRunner")
    log4 = logging.getLogger("PyLTSpice.RunTask")
    log1.setLevel(logging.INFO)
    log2.setLevel(logging.INFO)
    log3.setLevel(logging.INFO)
    log4.setLevel(logging.INFO)
    main()
