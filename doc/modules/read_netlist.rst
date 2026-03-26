Reading and Manipulating Netlists
=================================

spicelib has the ability to read and manipulate netlist files using the :doc:`../classes/spice_editor` class.

The SpiceEditor class inherits almost all functions from :doc:`/classes/spice_circuit` class. The SpiceCircuit
class allows manipulation of circuit elements such as resistors, capacitors, transistors and so on, as well as
subcircuit parameters.

The SpiceEditor extends these funcionalities and adds all the functions needed to read and write netlists to the disk,
as well as defining top level simulation directives, such as .TRAN and .AC for example.

The rationale for this division is to allow to manipulate not only elements that exist at the top level, but also to
manipulate elements that exit inside of sub-circuits. In Example 2 there is small example where the value of a component
inside a subcircuit is changed.

When all the changes are made, the save_netlist(<filename>) needs to be called in order for the updates to be registered.

Do not update the original file. It is always safer to keep the original file unchanged. This helps when debuging problems,
and also allows the script to revert to the initial condition by using the reset_netlist() method.


Example 1: Setting parameters inside a flat netlist.

.. code-block::
    
    #read netlist
    import spicelib
    net = spicelib.SpiceEditor("Batch_Test.net")  # Loading the Netlist

    net.set_parameters(res=0, cap=100e-6)  # Updating parameters res and cap
    net.set_component_value('R2', '2k')    # Updating the value of R2 to 2k
    net.set_component_value('R1', 4000)    # Updating the value of R1 to 4k
    net.set_element_model('V3', "SINE(0 1 3k 0 0 0)")  # changing the behaviour of V3

    # add instructions
    net.add_instructions(
        "; Simulation settings",
        ".param run = 0"
    )

    net.save_netlist("Batch_Test_Modified.net")  # writes the modified netlist to the indicated file

After version 1.2.0 it is possible to use a more object oriented approach to updating the netlist. The following code
makes the same changes as the previous example:

Example 2: Setting parameters inside a flat netlist.

.. code-block::

    #read netlist
    import spicelib
    net = spicelib.SpiceEditor("Batch_Test.net")  # Loading the Netlist

    net.set_parameters(res=0, cap=100e-6)  # Updating parameters res and cap
    net['R2'].value = '2k'    # Updating the value of R2 to 2k
    net['R1'].value = 4000    # Updating the value of R1 to 4k
    net['V3'].model = "SINE(0 1 3k 0 0 0)"  # changing the behaviour of V3

    # add instructions
    net.add_instructions(
        "; Simulation settings",
        "; .step param run 0 10 1"
    )
    net.set_parameter('run', 0)
    net.save_netlist("Batch_Test_Modified.net")  # writes the modified netlist to the indicated file

It is possible to update component values inside subcircuits. This is shown in Example 3.
However, only the approach used on Example 1 is possible at the moment. This will be corrected in future versions.

Example 3: Updating components inside a subcircuit

.. code-block::
    
    #read netlist
    import spicelib
    net = spicelib.SpiceEditor("Example2.net")

    net.set_component_value('R1', 1000)      # Sets the value of R1 to 1k
    net.set_component_value('XU1:Ra', '1k')  # Sets the value of Ra inside of XU1 to 1k
    net.save_netlist("Batch_Test_Modified.net")


*IMPORTANT NOTE:* When updating a subcircuit component, only the instance that is being updated is changed. If there are
multiple instances of the same subcircuit, the changes will not be reflected in the other instances. The script before
making the change, makes a copy of the subcircuit and changes the value of the component in the copy.
Every instance that is manipulated by the script is stored in the netlist as a new subcircuit.

If this is not the desired behaviour, the user should make the changes directly on the subcircuit definition.
This is shown in Example 4.

Example 4: Updating components inside a subcircuit

.. code-block::

    #read netlist
    import spicelib
    net = spicelib.SpiceEditor("Example2.net")

    print(net.get_subcircuit_names())  # get the names of the subcircuits
    subcircuit = net.get_subcircuit_named('')  # get the subcircuit definition
    subcircuit['R1'] = '1k'  # change the value of R1 inside the subcircuit.
                             # Will update all instances of the subcircuit.

    net.save_netlist("Batch_Test_Modified.net")

See the class documentation for more details :

- :py:class:`spicelib.SpiceEditor`
- :py:class:`spicelib.SpiceCircuit`
- :py:class:`spicelib.SpiceComponent`
