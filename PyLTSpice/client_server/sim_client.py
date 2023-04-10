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
# Name:        sim_client.py
# Purpose:     Tool used to launch LTSpice simulation in batch mode.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-02-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import os.path
import zipfile
import xmlrpc.client
import io
import pathlib
import time


class SimClientInvalidRunId(LookupError):
    """Raised when asking for a run_no that doesn't exist"""
    ...


# class RunIterator(object):
#
#     def __init__(self, client, timeout):
#         self.client = client
#         self.timeout = timeout
#
#     def __iter__(self):
#         return self
#
#     def __next__(self):
#         return self.client.__next__()


class SimClient(object):
    """
    Class used for launching simulations in a Spice Simulation Server.
    A Spice Simulation Server is a machine running a script with an active SimServer object.

    This class only implement basic level handshaking with a single simulation Server.
    Upon instance, it will establish a connection with Simulation Server. This connection is kept
    alive during the whole live of this object.

    The run() method will transfer the netlist for the server, execute a simulation and transfer the simulation results
    back to the client.
    Two lists are kept by this class:

        * A list of started jobs (started_jobs) and,

        * a list with finished jobs on the server, but, which haven't been yet transferred to the client (stored_jobs).

    This distinction is important because the data is erased on the server side when the data is transferred.

    Usage:

    .. code-block:: python

        import zipfile
        from PySpice.sim.sim_client import SimClient

        server = SimClient('http://localhost', 9000)  # Use another computer address.
        print(server.session_id)
        runid = server.run("../../tests/testfile.net")
        print("Got Job id", runid)

        for runid in server:   # may not arrive in the same order as runids were launched
            zip_filename = server.get_runno_data(runid)
            print(f"Received {zip_filename} from runid {runid}")

            with zipfile.ZipFile(zip_filename, 'r') as zipf:  # Extract the contents of the zip file
                print(zipf.namelist())  # Debug printing the contents of the zip file
                zipf.extract(zipf.namelist()[0])  # Normally the raw file comes first

    NOTE: More elaborate algorithms such as managing multiple servers will be done on another class.
    """

    def __init__(self, host_address, port):
        self.server = xmlrpc.client.ServerProxy(f'{host_address}:{port}')
        # print(self.server.system.listMethods())
        self.session_id = self.server.start_session()
        print("started ", self.session_id)
        self.started_jobs = []  # This list keeps track of started jobs on the server
        self.stored_jobs = []  # This list keeps track of finished simulations that haven't yet been transferred.
        self.completed_jobs = 0

    def __del__(self):
        print("closing session ", self.session_id)
        self.server.close_session(self.session_id)

    def run(self, circuit):
        """
        Sends the netlist identified with the argument "circuit" to the server, and it receives a run identifier
        (runno). Since the server can receive requests from different machines, this identifier is not guaranteed to be
        sequential.

        :param circuit: path to the netlist file containing the simulation directives.
        :type circuit: pathlib.Path or str
        :returns: identifier on the server of the simulation.
        :rtype int:
        """
        circuit_name = pathlib.Path(circuit).name
        if os.path.exists(circuit):
            # Create a buffer to store the zip file in memory
            zip_buffer = io.BytesIO()

            # Create the zip file in memory
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(circuit, circuit_name)  # Makes sure it writes it to the root of the zipfile

            # Reset the buffer position to the start
            zip_buffer.seek(0)

            # Read the zip file from the buffer and send it to the server
            zip_data = zip_buffer.read()

            run_id = self.server.run(self.session_id, circuit_name, zip_data)
            self.started_jobs.append(run_id)
            return run_id
        else:
            print(f"Circuit {circuit} doesn't exit")
            return -1
        
    def get_runno_data(self, runno) -> str:
        """Returns the simulation output data inside a zip file name."""
        if runno not in self.stored_jobs:
            raise SimClientInvalidRunId(f"Invalid Job id {runno}")

        zip_filename, zipdata = self.server.get_files(self.session_id, runno)
        self.stored_jobs.remove(runno)
        self.completed_jobs += 1
        if zip_filename != '':
            with open(zip_filename, 'wb') as f:
                f.write(zipdata.data)
        return zip_filename

    def __iter__(self):
        return self
    
    def __next__(self):
        while len(self.started_jobs) > 0:
            status = self.server.status(self.session_id)
            if len(status) > 0:
                runno = status.pop(0)
                self.started_jobs.remove(runno)  # Job is taken out of the started jobs list
                self.stored_jobs.append(runno)  # and is appended to the stored jobs
                return runno
            else:
                time.sleep(0.2)  # Go asleep for a sec

        # when there are no pending jobs left, exit the iterator    
        raise StopIteration
        

if __name__ == "__main__":

    server = SimClient('http://localhost', 9000)
    print(server.session_id)
    runid = server.run("../../tests/testfile.net")
    print("Got Job id", runid)
    for runid in server:  # Ma
        zip_filename = server.get_runno_data(runid)
        print(f"Received {zip_filename} from runid {runid}")
        with zipfile.ZipFile(zip_filename, 'r') as zipf:  # Extract the contents of the zip file
            print(zipf.namelist())  # Debug printing the contents of the zip file
            zipf.extract(zipf.namelist()[0])  # Normally the raw file comes first

    print("Finished")
    server.server.stop_server()  # This will terminate the server
