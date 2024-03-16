# coding=utf-8

# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        raw_read.py
# Purpose:     Process LTSpice output files and align data for usage in a spreadsheet
#              tool such as Excel, or Calc.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

"""
This module reads data from an LTSpice RAW file.
The main class object is the RawRead which is initialized with the filename of the RAW file to be processed.
The object wil read the file and construct a structure of objects which can be used to access the data inside the
RAW file.
To understand why this is done so, in the next section follows a brief explanation of what is contained inside a RAW
file.
In case RAW file contains stepped data detected, i.e. when the .STEP command is used, then it will also try to open the
simulation LOG file and read the stepping information.

RAW File Structure
==================

This section is written to help understand the why the structure of classes is defined as it is. You can gladly skip
this section and get right down to business by seeing the examples section below.

The RAW file starts with a text preamble that contains information about the names of the traces the order they
appear on the binary part and some extra information.
In the preamble, the lines are always started by one of the following identifiers:

   + Title:          => Contains the path of the source .asc file used to make the simulation preceded by *

   + Date:           => Date when the simulation started

   + Plotname:       => Name of the simulation. The known Simulation Types are:
                       * Operation Point
                       * DC transfer characteristic
                       * AC Analysis
                       * Transient Analysis
                       * Noise Spectral Density - (V/Hz½ or A/Hz½)
                       * Transfer Function

   + Flags:          => Flags that are used in this plot. The simulation can have any combination of these flags.
                      * "real" -> The traces in the raw file contain real values. As for example on a TRAN simulation.
                      * "complex" -> Traces in the raw file contain complex values. As for example on an AC simulation.
                      * "forward" -> Tells whether the simulation has more than one point. DC transfer
                        characteristic, AC Analysis, Transient Analysis or Noise Spectral Density have the forward flag.
                        Operating Point and Transfer Function don't have this flag activated.
                      * "log" -> The preferred plot view of this data is logarithmic.
                      * "stepped" -> The simulation had .STEP primitives.
                      * "FastAccess" -> Order of the data is changed to speed up access. See Binary section for details.

   + No. Variables:  => number of variables contained in this dataset. See section below for details.

   + No. Points:     => number of points per each variable in

   + Offset:         => when the saving of data started

   + Command:        => Name of the simulator executable generating this file.

   + Backannotation: => Backannotation alerts that occurred during simulation

   + Variables:      => a list of variable, one per line as described below

   + Binary:         => Start of the binary section. See section below for details.

Variables List
--------------
The variable list contains the list of measurements saved in the raw file. The order of the variables defines how they
are stored in the binary section. The format is one variable per line, using the following format:

<tab><ordinal number><tab><measurement><tab><type of measurement>

Here is an example:

.. code-block:: text

    0	time	time
    1	V(n001)	   voltage
    2	V(n004)	   voltage
    3	V(n003)	   voltage
    4	V(n006)	   voltage
    5	V(adcc)    voltage
    6	V(n002)	   voltage
    7	V(3v3_m)   voltage
    8	V(n005)	   voltage
    9	V(n007)	   voltage
    10	V(24v_dsp) voltage
    11	I(C3)	   device_current
    12	I(C2)	   device_current
    13	I(C1)	   device_current
    14	I(I1)	   device_current
    15	I(R4)	   device_current
    16	I(R3)	   device_current
    17	I(V2)	   device_current
    18	I(V1)	   device_current
    19	Ix(u1:+)   subckt_current
    20	Ix(u1:-)   subckt_current

Binary Section
--------------
The binary section of .RAW file is where the data is usually written, unless the user had explicitly specified an ASCII
representation. In this case this section is replaced with a "Values" section.
LTSpice stores data directly onto the disk during simulation, writing per each time or frequency step the list of
values, as exemplified below for a .TRAN simulation.

     <timestamp 0><trace1 0><trace2 0><trace3 0>...<traceN 0>

     <timestamp 1><trace1 1><trace2 1><trace3 1>...<traceN 1>

     <timestamp 2><trace1 2><trace2 2><trace3 2>...<traceN 2>

     ...

     <timestamp T><trace1 T><trace2 T><trace3 T>...<traceN T>
     
Depending on the type of simulation the type of data changes.
On TRAN simulations the timestamp is always stored as 8 bytes float (double) and trace values as 4 bytes (single).
On AC simulations the data is stored in complex format, which includes a real part and an imaginary part, each with 8
bytes.
The way we determine the size of the data is dividing the total block size by the number of points, then taking only
the integer part.

Fast Access
-----------

Once a simulation is done, the user can ask LTSpice to optimize the data structure in such that variables are stored
contiguously as illustrated below.

     <timestamp 0><timestamp 1>...<timestamp T>

     <trace1 0><trace1 1>...<trace1 T>

     <trace2 0><trace2 1>...<trace2 T>

     <trace3 0><trace3 1>...<trace3 T>

     ...

     <traceN T><traceN T>...<tranceN T>

This can speed up the data reading. Note that this transformation is not done automatically. Transforming data to Fast
Access must be requested by the user. If the transformation is done, it is registered in the Flags: line in the
header. RawReader supports both Normal and Fast Access formats

Classes Defined
===============

The .RAW file is read during the construction (constructor method) of an `RawRead` object. All traces on the RAW
file are uploaded into memory.

The RawRead class then has all the methods that allow the user to access the Axis and Trace Values. If there is
any stepped data (.STEP primitives), the RawRead class will try to load the log information from the same
directory as the raw file in order to obtain the STEP information.

Follows an example of the RawRead class usage. Information on the RawRead methods can be found here.

Examples
========

The example below demonstrates the usage of the RawRead class. It reads a .RAW file and uses the matplotlib
library to plot the results of three traces in two subplots. ::

    import matplotlib.pyplot as plt  # Imports the matplotlib library for plotting the results

    LTR = RawRead("some_random_file.raw")  # Reads the RAW file contents from file

    print(LTR.get_trace_names())  # Prints the contents of the RAW file. The result is a list, and print formats it.
    print(LTR.get_raw_property())  # Prints all the properties found in the Header section.

    plt.figure()  # Creates the canvas for plotting

    vin = LTR.get_trace('V(in)')  # Gets the trace data. If Numpy is installed, then it comes in numpy array format.
    vout = LTR.get_trace('V(out)') # Gets the second trace.

    steps = LTR.get_steps()  # Gets the step information. Returns a list of step numbers, ex: [0,1,2...]. If no steps
                             # are present on the RAW file, returns only one step : [0] .

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)  # Creates the two subplots. One on top of the other.

    for ax in (ax1, ax2):  # Crates a grid on all the plots.
        ax.grid(True)

    plt.xlim([0.9e-3, 1.2e-3])  # Optionally, limits the X axis to just a subrange.

    x = LTR.get_axis(0)  # Retrieves the time vector that will be used as X axis. Uses STEP 0
    ax1.plot(x, vin.get_wave(0)) # On first plot plots the first STEP (=0) of Vin

    for step in steps:  # On the second plot prints all the STEPS of the Vout
        x = LTR.get_axis(step)  # Retrieves the time vector that will be used as X axis.
        ax2.plot(x, vout.get_wave(step))

    plt.show()  # Creates the matplotlib's interactive window with the plots.

"""

__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2022, Fribourg Switzerland"

import logging
_logger = logging.getLogger("spicelib.RawRead")
_logger.info("This is maintained for backward compatibility. Use spicelib.raw.raw_read instead")

from spicelib.raw.raw_read import RawRead
# Backward compatibility naming
LTSpiceRawRead = RawRead
