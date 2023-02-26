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
# Name:        sim_server.py
# Purpose:     Tool used to launch LTSpice simulation in batch mode.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-02-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
from xmlrpc.server import SimpleXMLRPCServer
from pathlib import Path
import zipfile
import io
from .sim_runner import SimRunner


class SimServer():

    def __init__(self, simulator, parallel_sims=4, output_folder='./temp1'):
        self.output_folder = output_folder
        self.runner = SimRunner(parallel_sims=parallel_sims, timeout=5 * 60, verbose=True, output_folder=output_folder,
                                simulator=simulator)

    def callback(self, raw_file, log_file):
        print("Update Stats")

    def run(self, circuit_name, zip_data):
        def callback_fun(raw_file, log_file):
            self.callback(raw_file, log_file)

        print(f"Received {circuit_name}")
        # Create a buffer from the zip data
        zip_buffer = io.BytesIO(zip_data.data)
        print("Created the buffer")
        # Extract the contents of the zip file
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            print(zip_file.namelist())
            zip_file.extract(circuit_name, self.output_folder)

        print("did write the file")
        print(f"Running {circuit_name}")
        self.runner.run(circuit_name)
        return 0

    def run_server(self, port=9000):
        with SimpleXMLRPCServer(('localhost', port),
                                # requestHandler=RequestHandler
                                ) as server:
            # server.register_introspection_functions()
            # # Register len() function;
            # server.register_function(len)
            # # Register a function under a different name
            # @server.register_function(name='rmndr')
            # def remainder_function(x, y):
            #    return x // y
            # # Register a function under function.__name__.
            # @server.register_function
            # def modl(x, y):
            #    return x % y
            server.register_introspection_functions()
            server.register_instance(self)

            server.serve_forever()
        print("Server Stopped")


if False:
    from xmlrpc.server import SimpleXMLRPCServer

    # Create a SimpleXMLRPCServer object
    server = SimpleXMLRPCServer(('localhost', 8000))

    # Start the server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # Wait for the server to start up
    time.sleep(1)

    # Shut down the server
    server.shutdown()
