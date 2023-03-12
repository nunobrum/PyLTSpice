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


class SimClient:

    def __init__(self, host_address, port):
        self.server = xmlrpc.client.ServerProxy(f'{host_address}:{port}')
        print(self.server.system.listMethods())
        print("starting session")
        self.session_id = self.server.start_session()
        self.started_jobs = []

    def __del__(self):
        print("closing session")
        self.server.close_session(self.session_id)

    def run(self, circuit):
        circuit_name = pathlib.Path(circuit).name
        print("Circuit Name", circuit_name)
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

            runno = self.server.run(self.session_id, circuit_name, zip_data)
            self.started_jobs.append(runno)
            print(runno)
        else:
            print(f"Circuit {circuit} doesn't exit")
        return runno

    def wait(self, runno):
        if runno not in self.started_jobs:
            print(runno, "not in ", self.started_jobs)
            raise AssertionError("Invalid Job id")

        status = self.server.status(self.session_id)
        while runno not in status:
            time.sleep(0.2)
            status = self.server.status(self.session_id)
        print(f"Job {runno} Completed")
        zip_filename, zipdata = self.server.get_files(self.session_id, runno)
        print(f"Received {zip_filename}")

        if zip_filename != '':
            with open(zip_filename, 'wb') as f:
                f.write(zipdata.data)
        return zip_filename


if __name__ == "__main__":

    s = SimClient('http://localhost', 9000)
    print(s.session_id)
    runno = s.run("../../tests/testfile.net")
    print("Got Job id", runno)
    s.wait(runno)
    print("Finished")

    s.server.stop_server()  # This will terminate the server