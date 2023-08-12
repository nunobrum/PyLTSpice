Client Server
=============

Simulations take a huge computational power, and having the
possibility of extending your own computer's capabilities can
come as very handy. For this reason, PyLTspice has implemented
a client-server architecture, where the server is the one machine and
the client is the other. The server is the one that will run the simulation.
The client will send the commands to the server and will receive the
simulation raw and log files. At this moment there is no way to make the
server machine execute the processing of raw files.
It is therefore advised to make use of the .meas command in the netlist
and to use the .raw file only for plotting purposes.

The server machine can be any machine that has LTspice installed. To start the server
use the following command:

.. code-block:: bash

    python -m pyltspice.run_server --port 9000 --parallel 4 --output ./temp

Make sure that each machine is on the same network and that the port is open.
If port is not specified, the default port is 9000.

On the client side, you can use the following code to run the simulation:

.. code-block:: python

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

            ## Any treatment of the files can be done here

        os.remove(zip_filename)  # Remove the zip file

    server.close_session()

The server will run the simulation and will send the raw and log files to the client.
In order to minimize the data transfer between client and server, all files are zipped before being sent.
When the run() command is called, the client will automatically zip the netlist file and send it to the server.
The server will execute the simulation and will send the raw and log files back to the client also in zip format.
The client has to unzip the files and then use them as needed.

In the example above the client is unzipping the first file and then deleting the zip file.