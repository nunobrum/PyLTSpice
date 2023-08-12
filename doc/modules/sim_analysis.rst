Sim Analysis Toolkit
====================

The Sim Analysis toolkit is a collection of tools for setting up, running and analyzing simulations.

At present there are two main tools:
    * Montecarlo simulation setup
    * Worst Case simulation setup

Other tools will be added in the future.

## Simulation Setup ##

Let's consider the following circuit:

.. image:: sallenkey.png
    :alt: Sallen-Key Amplifier
    :align: center
    :width: 710px

When performing a Monte Carlo simulation on this circuit, we need to manually modify the value of each component,
and then add the .step command for making several runs on the same circuit.
To simplify this process, the Montecarlo class can be used as exemplified below:

.. code-block:: python

    from PyLTSpice import AscEditor  # Imports the class that manipulates the asc file
    from PyLTSpice.sim.tookit.montecarlo import Montecarlo  # Imports the Montecarlo toolkit class

    sallenkey = AscEditor("./testfiles/sallenkey.asc")  # Reads the asc file into memory

    mc = Montecarlo(sallenkey)  # Instantiates the Montecarlo class, with the asc file already in memory

    # The following lines set the default tolerances for the components
    mc.set_tolerance('R', 0.01)  # 1% tolerance, default distribution is uniform
    mc.set_tolerance('C', 0.1, distribution='uniform')  # 10% tolerance, explicit uniform distribution
    mc.set_tolerance('V', 0.1, distribution='normal')  # 10% tolerance, but using a normal distribution

    # Some components can have a different tolerance
    mc.set_tolerance('R1', 0.05)  # 5% tolerance for R1 only. This only overrides the default tolerance for R1

    # Tolerances can be set for parameters as well
    mc.set_parameter_deviation('Vos', 3e-4, 5e-3, 'uniform')  # The keyword 'distribution' is optional
    mc.prepare_testbench(1000)  # Prepares the testbench for 1000 simulations

    # Finally the netlist is saved to a file
    mc.save_netlist('./testfiles/sallenkey_mc.net')

When opening the created sallenkey_mc.net file, we can see that the following circuit.

.. image:: sallenkey_mc.png
    :alt: Sallen-Key Amplifier with Montecarlo
    :align: center
    :width: 710px

The following updates were made to the circuit:

    * The value of each component was replaced by a function that generates a random value within the specified tolerance.

    * The .step param run command was added to the netlist. Starts at -1 which it's the nominal value simulation, and
      finishes that the number of simulations specified in the prepare_testbench() method.

    * A default value for the run parameter was added. This is useful if the .step param run is commented out.

    * The R1 tolerance is different from the other resistors. This is because the tolerance was explicitly set for R1.

    * The Vos parameter was added to the .param list. This is because the parameter was explicitly set using the
      set_parameter_deviation method.

    * Functions utol, ntol and urng were added to the .func list. These functions are used to generate random values.


Uniform distributions use the LTSpice built-in mc(x, tol) and flat(x) functions, while normal distributions use the
gauss(x) function.

Similarly, the worst case analysis can also be setup by using the class WorstCaseAnalysis, as exemplified below:

.. code-block:: python

    from PyLTSpice import AscEditor  # Imports the class that manipulates the asc file
    from PyLTSpice.sim.tookit.worst_case import WorstCaseAnalysis

    sallenkey = AscEditor("./testfiles/sallenkey.asc")  # Reads the asc file into memory

    wca = WorstCaseAnalysis(sallenkey)  # Instantiates the Worst Case Analysis class

    # The following lines set the default tolerances for the components
    wca.set_tolerance('R', 0.01)  # 1% tolerance
    wca.set_tolerance('C', 0.1)  # 10% tolerance
    wca.set_tolerance('V', 0.1)  # 10% tolerance. For Worst Case analysis, the distribution is irrelevant

    # Some components can have a different tolerance
    wca.set_tolerance('R1', 0.05)  # 5% tolerance for R1 only. This only overrides the default tolerance for R1

    # Tolerances can be set for parameters as well.
    wca.set_parameter_deviation('Vos', 3e-4, 5e-3)

    # Finally the netlist is saved to a file
    wca.save_netlist('./testfiles/sallenkey_wc.asc')

When opening the created sallenkey_wc.net file, we can see that the following circuit.

.. image:: sallenkey_wc.png
    :alt: Sallen-Key Amplifier with Worst Case Analysis
    :align: center
    :width: 710px


The following updates were made to the circuit:

  * The value of each component was replaced by a function that generates a nominal, minimum and maximum value depending
    on the run parameter and is assigned a unique index number. (R1=0, Vos=1, R2=2, ... V2=7, VIN=8)
    The unique number corresponds to the bit position of the run parameter. Bit 0 corresponds to the minimum value and
    bit 1 corresponds to the maximum value. Calculating all possible permutations of maximum and minimum values for each
    component, we get 2**9 = 512 possible combinations. This maps into a 9 bit binary number, which is the run parameter.

  * The .step param run command was added to the netlist. It starts at -1 which it's the nominal value simulation, then 0
    which corresponds to the minimum value for each component, then it makes all combinations of minimum and maximum values
    until 511, which is the simulation with all maximum values.

  * A default value for the run parameter was added. This is useful if the .step param run is commented out.

  * The R1 tolerance is different from the other resistors. This is because the tolerance was explicitly set for R1.

  * The wc() function is added to the circuit. This function is used to calculate the worst case value for each component,
    given a tolerance value and its respective index.

  * The wc1() function is added to the circuit. This function is used to calculate the worst case value for each component,
    given a minimum and maximum value and its respective index.