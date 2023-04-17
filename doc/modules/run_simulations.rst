Running Simulations
===================

The class :py:class:`PyLTSpice.SimRunner` allows launching LTSpice simulations from a Python script, thus allowing to
overcome the 3 dimensions STEP limitation on LTSpice, update resistor values, or component models.
It also allows to simulate several simulations in parallel, thus speeding up the time
a set of simulations would take.

The class :py:class:`PyLTSpice.SpiceEditor` described in :doc:`read_netlist` allows to modify the netlist.

The code snipped below will simulate a circuit with two different diode models, set the simulation
temperature to 80 degrees, and update the values of R1 and R2 to 3.3k.

.. code-block:: python

    from PyLTSpice import SimRunner, SpiceEditor, LTspice

    runner = SimRunner(output_folder='./temp_batch3', simulator=LTspice)  # Configures the simulator to use and output 
    # folder 

    netlist = SpiceEditor("Batch_Test.asc")  # Open the Spice Model, and creates the .net
    # set default arguments
    netlist.set_parameters(res=0, cap=100e-6)
    netlist.set_component_value('R2', '2k')  # Modifying the value of a resistor
    netlist.set_component_value('R1', '4k')
    netlist.set_element_model('V3', "SINE(0 1 3k 0 0 0)")  # Modifying the
    netlist.set_component_value('XU1:C2', 20e-12)  # modifying a
    # define simulation
    netlist.add_instructions(
            "; Simulation settings",
            ".param run = 0"
    )

    for opamp in ('AD712', 'AD820'):
        netlist.set_element_model('XU1', opamp)
        for supply_voltage in (5, 10, 15):
            netlist.set_component_value('V1', supply_voltage)
            netlist.set_component_value('V2', -supply_voltage)
            # overriding he automatic netlist naming
            run_netlist_file = "{}_{}_{}.net".format(netlist.netlist_file.name, opamp, supply_voltage)
            raw, log = runner.run_now(netlist, run_filename=run_netlist_file)
            # Process here the simulation results

In this example we are are using the SpiceEditor instantiation 'netlist' by passing an .asc file. 
When receiving an .asc file, it will use LTSpice to create the corresponding .net file and read it into memory.

Follows a series of function calls to 'netlist' that update the netlist in memory.
The method ``set_parameters(<param_name>, <param_value>)`` updates the values of
``.PARAM definitions``, the method ``set_component_value(<element_id>, <element_value>)`` will update
values of R, L and C elements, in this example we are updating only resistors. The method ``set_element_model()``
sets the values of a voltage source 'V3' and so on.

Then we pass the object to the ``runner.run_now()`` method. By doing so, it will first write the netlist to the path
indicated by the output folder indicated as parameter in the SimRunner instantiation, then will launch LTSpice to
execute the simulation.

Although this works well, it is not very efficient on the processor usage. A simulation is ended before another one is started.
An alternative method to this is presented in the next section.

---------------
Multiprocessing
---------------

For making better use of today's computer capabilities, the SimRunner can spawn several LTSpice instances
each executing in parallel a simulation. This is exemplified in the modified example below.

.. code-block:: python

    from PyLTSpice import SimRunner, SpiceEditor, LTspice

    def processing_data(raw_file, log_file):
        """This is the function that will process the data from simulations"""
        print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))

    # Configures the simulator to use and output folder. Also defines the number of parallel simulations
    runner = SimRunner(output_folder='./temp_batch3', simulator=LTspice, parallel_sims=4)  

    netlist = SpiceEditor("Batch_Test.asc")  # Open the Spice Model, and creates the .net
    # set default arguments
    netlist.set_parameters(res=0, cap=100e-6)
    netlist.set_component_value('R2', '2k')  # Modifying the value of a resistor
    netlist.set_component_value('R1', '4k')
    netlist.set_element_model('V3', "SINE(0 1 3k 0 0 0)")  # Modifying the
    netlist.set_component_value('XU1:C2', 20e-12)  # modifying a
    # define simulation
    netlist.add_instructions(
            "; Simulation settings",
            ".param run = 0"
    )

    for opamp in ('AD712', 'AD820'):
        netlist.set_element_model('XU1', opamp)
        for supply_voltage in (5, 10, 15):
            netlist.set_component_value('V1', supply_voltage)
            netlist.set_component_value('V2', -supply_voltage)
            # overriding he automatic netlist naming
            run_netlist_file = "{}_{}_{}.net".format(netlist.netlist_file.name, opamp, supply_voltage)
            # This will launch up to 'parallel_sims' simulations in background before waiting for resources
            runner.run(netlist, run_filename=run_netlist_file, callback=processing_data)

    # This will wait for the all the simulations launched before to complete.
    runner.wait_completion()
    # The timeout counter is reset everytime a simulation is finished.
    
    # Sim Statistics
    print('Successful/Total Simulations: ' + str(runner.okSim) + '/' + str(runner.runno))

If the ``parallel_sims`` parallel simulations is not given, it defaults to 4. This means that a fifth simulation
will only start when one of the other 4 is finished. If ``parallel_sims`` needs to be adjusted according to the
computer capabilities. If resources are abundant, this number can be set to a higher number. If set for example
to 16, it means that the 17th simulation will wait for another one to finish before starting. 
Another way of bypassing this behaviour is just by setting the parameter ``wait_resource=False`` to False

    ``runner.run(netlist, wait_resource=False)``


Finally we see in the example the ``runner.wait_completion()`` method. The usage of wait_completion() is optional. 
Just note that the script will only end when all the scheduled tasks are executed.


---------
Callbacks
---------

As seen above, the ``wait_completion()`` can be used to wait for all the simulations to be finished. However, this is
not efficient from a multiprocessor point of view. Ideally, the post-processing should be also handled while other
simulations are still running. For this purpose, the user can use a call back function.

The callback function is called when the simulation has finished directly by the thread/process that has handling the
simulation. A function callback receives two arguments.
The RAW file and the LOG file names. Below is an example of a callback function

.. code-block:: python

    def processing_data(raw_filename, log_filename):
        '''This is a call back function that just prints the filenames'''
        print("Simulation Raw file is %s. The log is %s" % (raw_filename, log_filename)
        # Other code below either using LTSteps.py or raw_read.py
        log_info = LTSpiceLogReader(log_filename)
        log_info.read_measures()
        rise, measures = log_info.dataset["rise_time"]

The callback function is optional. If  no callback function is given, the thread is terminated just after the
simulation is finished.

================================
Processing of simulation outputs
================================

The previous sections described the way to launch simulations. The way to parse the
simulation results contained in the RAW files are described in :doc:`read_rawfiles`.
For parsing information contained in the LOG files, which contain information about
measurements done with .MEAS primitives, is implemented by the class :py:class:`PyLTSpice.SpiceEditor`
