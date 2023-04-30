Reading and Manipulating Netlists
=================================

PyLTSpice has the ability to read and manipulate netlist files using the :doc:`../classes/spice_editor` class.  

The SpiceEditor class inherits almost all functions from :doc:`/classes/spice_circuit` class. The SpiceCircuit
class allows manipulation of circuit elements such as resistors, capacitors, transistors and so on, as well as
subcircuit parameters.

The SpiceEditor extends these funcionalities and adds all the functions needed to read and write netlists to the disk,
as well as defining top level simulation directives, such as .TRAN and .AC for example.

The rationale for this division is to allow to manipulate not only elements that exist at the top level, but also to
manipulate elements that exit inside of sub-circuits. In Example 2 there is small example where the value of a component
inside a subcircuit is changed.

When all the changes are made, the write_netlist(<filename>) needs to be called in order for the updates to be registered.

Do not update the original file. It is always safer to keep the original file unchanged. This helps when debuging problems,
and also allows the script to revert to the initial condition by using the reset_netlist() method.


Example 1: Setting parameters inside a flat netlist.

.. code-block::
    
    #read netlist
    import PyLTSpice
    net = PyLTSpice.SpiceEditor("Batch_Test.net")  # Loading the Netlist

    net.set_parameters(res=0, cap=100e-6)  # Updating parameters res and cap
    net.set_component_value('R2', '2k')    # Updating the value of R2 to 2k
    net.set_component_value('R1', 4000)    # Updating the value of R1 to 4k
    net.set_element_model('V3', "SINE(0 1 3k 0 0 0)")  # changing the behaviour of V3

    # add instructions
    net.add_instructions(
        "; Simulation settings",
        ".param run = 0"
    )

    net.write_netlist("Batch_Test_Modified.net")  # writes the modified netlist to the indicated file
    

Example 2: Updating components inside a subcircuit

.. code-block::
    
    #read netlist
    import PyLTSpice
    net = PyLTSpice.SpiceEditor("Example2.net")

    net.set_component_value('R1', 1000)      # Sets the value of R1 to 1k
    net.set_component_value('XU1:Ra', '1k')  # Sets the value of Ra inside of XU1 to 1k
    net.write_netlist("Batch_Test_Modified.net")

See the class documentation for more details :

* :py:class:`PyLTSpice.SpiceEditor`
* :py:class:`PyLTSpice.SpiceCircuit`
