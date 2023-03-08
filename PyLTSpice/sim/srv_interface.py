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
# Name:        srv_interface.py
# Purpose:     Tool used to launch LTSpice simulation in batch mode.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-02-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
from xmlrpc.server import SimpleXMLRPCServer
import threading
from pathlib import Path
import zipfile
import io
from .srv_sim_runner import ServerSimRunner
import uuid


class SimServer():

    def __init__(self, simulator, parallel_sims=4, output_folder='./temp1', port=9000):
        self.output_folder = output_folder
        self.server_thread = ServerSimRunner(parallel_sims=parallel_sims, timeout=5 * 60, verbose=True,
                                             output_folder=output_folder, simulator=simulator)
        self.server = SimpleXMLRPCServer(
                ('localhost', port),
                # requestHandler=RequestHandler
        )
        self.server.register_introspection_functions()
        self.server.register_instance(self)
        self.server_thread = None
        self.sessions = {}  # this will contain the session_id ids hashing their respective list of threads
        self.server_thread.start()

    def run(self, session_id, circuit_name, zip_data):
        if session_id not in self.sessions:
            return -1  # This indicates that no job is started
        # Create a buffer from the zip data
        zip_buffer = io.BytesIO(zip_data.data)
        print("Created the buffer")
        # Extract the contents of the zip file
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            print(zip_file.namelist())
            zip_file.extract(circuit_name, self.output_folder)

        print(f"Running simulation of {circuit_name}")
        task = self.runner.run(circuit_name)
        self.sessions[session_id].append(task)
        return self.runner.runno

    def start_session(self):
        session_id = uuid.uuid4()
        self.sessions[session_id] = []
        return session_id

    def status(self, session_id):
        """
        Returns a dictionary with task information. The key for the dictionary is the simulation identifier returned
        by the simulation start command. The value associated with each simulation identifier is another dictionary
        containing the following keys:

            * 'completed' - whether the simulation is already finished

            * 'start' - time when the simulation was started

            * 'stop' - server time
        """
        i = 0
        ret = {}
        while i < len(self.runner.threads):
            task = self.runner.threads[i]
            if task.runno in self.sessions[session_id]:
                simulation_completed = not task.is_alive()
                ret[task.runno] = {
                    'completed': simulation_completed,
                    'raw': task.raw_file if simulation_completed else '',
                    'log': task.log_file if simulation_completed else '',
                    'start': task.start_time,
                    'stop': task.stop_time,
                }
                if simulation_completed:
                    del self.runner.threads[i]
                else:
                    i += 1

    def close_session(self, session_id):
        """Cleans all the pending threands"""
        i = 0
        while i < len(self.runner.threads):
            task = self.runner.threads[i]
            if task.runno in self.sessions[session_id]:
                task.stop()
                del self.runner.threads[i]
            else:
                i += 1

    def run_server(self):
        # Start the server in a separate thread
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
      
    def stop_server(self):
        self.server.shutdown()

