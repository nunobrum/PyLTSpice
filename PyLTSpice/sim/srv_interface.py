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
from typing import Tuple
from xmlrpc.client import Binary
from xmlrpc.server import SimpleXMLRPCServer

import threading
import zipfile
import io
from .srv_sim_runner import ServerSimRunner
import uuid


class SimServer():

    def __init__(self, simulator, parallel_sims=4, output_folder='./temp1', port=9000):
        self.output_folder = output_folder
        self.simulation_manager = ServerSimRunner(parallel_sims=parallel_sims, timeout=5 * 60, verbose=True,
                                                  output_folder=output_folder, simulator=simulator)
        self.server = SimpleXMLRPCServer(
                ('localhost', port),
                # requestHandler=RequestHandler
        )
        self.server.register_introspection_functions()
        self.server.register_instance(self)
        self.sessions = {}  # this will contain the session_id ids hashing their respective list of threads
        self.simulation_manager.start()
        self.server_thread = threading.Thread(target=self.server.serve_forever, name="ServerThread")
        self.server_thread.start()

    def run(self, session_id, circuit_name, zip_data):
        print("Run ", session_id, circuit_name)
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
        runno = self.simulation_manager.add_simulation(circuit_name)
        if runno != -1:
            self.sessions[session_id].append(runno)
        return runno

    def start_session(self):
        """Returns an unique key that represents the session. It will be later used to sort the threads belonging
        to the session."""
        session_id = str(uuid.uuid4())  # Needs to be a string, otherwise the rpc client can't handle it
        print("Starting session ", session_id)
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
        print("collecting status for ", session_id)
        ret = []
        for task_info in self.simulation_manager.completed_tasks:
            print(task_info)
            runno = task_info['runno']
            if runno in self.sessions[session_id]:
                ret.append(runno)  # transfers the dictionary from the simulation_manager completed task
                # to the return dictionary 
        print("returning status", ret)
        return ret

    def get_files(self, session_id, job_id) -> Tuple[str, Binary]:
        if job_id in self.sessions[session_id]:

            for task_info in self.simulation_manager.completed_tasks:
                if job_id == task_info['runno']:
                    # Create a buffer to store the zip file in memory
                    zip_file = task_info['zipfile']
                    zip = zip_file.open('rb')
                    # Read the zip file from the buffer and send it to the server
                    zip_data = zip.read()
                    zip.close()
                    self.simulation_manager.vacuum_files_of_runno(job_id)
                    return zip_file.name, Binary(zip_data)

        return "", Binary(b'')  # Returns and empty data

    def close_session(self, session_id):
        """Cleans all the pending threads with """
        for runno in self.sessions[session_id]:
            self.simulation_manager.vacuum_files_of_runno(runno)
        return True  # Needs to return always something. None is not supported

    def stop_server(self):
        print("stopping...ServerInterface")
        self.simulation_manager.stop()
        self.server.shutdown()
        print("stopped...ServerInterface")
        return True  # Needs to return always something. None is not supported

    def running(self):
        return self.simulation_manager.running()

