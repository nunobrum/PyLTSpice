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
from PyLTSpice.client_server.sim_client import SimClient
import logging

# In order for this, to work, you need to have a server running. To start a server, run the following command:
# python -m PyLTSpice.run_server --port 9000 --parallel 4 --output ./temp

_logger = logging.getLogger("PyLTSpice.SimClient")
_logger.setLevel(logging.DEBUG)

server = SimClient('http://localhost', 9000)
print(server.session_id)
runid = server.run("./testfiles/testfile.net")
print("Got Job id", runid)
for runid in server:  # Ma
    zip_filename = server.get_runno_data(runid)
    print(f"Received {zip_filename} from runid {runid}")
    with zipfile.ZipFile(zip_filename, 'r') as zipf:  # Extract the contents of the zip file
        print(zipf.namelist())  # Debug printing the contents of the zip file
        zipf.extract(zipf.namelist()[0])  # Normally the raw file comes first
    os.remove(zip_filename)  # Remove the zip file

server.close_session()
print("Finished")
# server.server.stop_server()  # This will terminate the server
