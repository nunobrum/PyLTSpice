Reading and Manipulating Netlists
=================================

PyLTSpice has the ability to read and manipulate netlist files using the :doc:`../classes/SpiceEditor` class.  Basic functions include adding and removing instructions, and writing out the modified netlist.

Functions for getting and setting component values, and much more are derived from the :doc:`../classes/SpiceCircuit`: class.

Example :

.. code-block::
    
    #read netlist
    import PyLTSpice
    net = PyLTSpice.SpiceEditor("Batch_Test.net")

    # set default arguments
    net.set_parameters(res=0, cap=100e-6)
    net.set_component_value('R2', '2k')
    net.set_component_value('R1', '4k')
    net.set_element_model('V3', "SINE(0 1 3k 0 0 0)")

    # add instructions
    net.add_instructions(
        "; Simulation settings",
        ".param run = 0"
    )
    

See the class documentation for more details :

* :py:class:`PyLTSpice.SpiceEditor.SpiceEditor`
* :py:class:`PyLTSpice.SpiceEditor.SpiceCircuit`
