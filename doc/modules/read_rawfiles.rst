Reading Raw Files
=================

The RawRead class is used to (surprise...) read .RAW-files.
The file to read is given as parameter when creating the RawRead object.  The object wil read the file and construct
a structure of objects which can be used to access the data inside the .RAW-file.
All traces on the .RAW-file are uploaded into memory.

See :doc:`../varia/raw_file` for details of the contents of a .RAW-file.

The .RAW-file contains different traces for voltages and currents in the simulation.

Typically (for a transient
analysis), a trace contain a value (voltage/current) for each different time point in the simulation.
There is a list of time values, and a separate list of trace values for each trace.  So each trace uses the same
time values.
If there were different steps (e.g. for a DC sweep), then there is a set of lists with time/value data for each step.

Note that for an AC analysis, the traces are *frequency-versus-value* instead of *time-versus-value*.
We will use 'time' as an example further in this text.

The RawRead class  has all the methods that allow the user to access the X-axis and trace values. If there is
any stepped data (.STEP primitives), the RawRead class will try to load the log information from the same
directory as the raw file in order to obtain the STEP information.

You can get a list of all trace names using the ``get_trace_names()`` method.

Use method ``get_trace()`` to get the trace data, which consists of values for 1 or more simulation steps.
It will return a :py:class:`PyLTSpice.raw_classes.Trace` object.  Use this object's ``get_wave()`` method to get
the actual data points for a step.

Use the method ``get_axis()`` to get the 'time' data.  If there were multiple steps in the simulation, specify
the number for which step you want to retrieve the time data.

Now that you have lists with the times and corresponding values, you can plot this information in an X/Y plot. 

Note that all the data will be returned as numpy arrays.

See the class documentation for more details :

- :py:class:`PyLTSpice.raw_read.RawRead`
- :py:class:`PyLTSpice.raw_classes.Trace`

Example
-------

The example below demonstrates the usage of the RawRead class. It reads a .RAW file and uses the matplotlib
library to plot the results of two traces in a separate subplots.

.. code-block::

    from PyLTSpice import RawRead
    import matplotlib.pyplot as plt         # use matplotlib for plotting the results

    raw = RawRead("some_random_file.raw")   # Read the RAW file contents from disk

    print(raw.get_trace_names())            # Get and print a list of all the traces
    print(raw.get_raw_property())           # Print all the properties found in the Header section

    vin = raw.get_trace('V(in)')            # Get the trace data
    vout = raw.get_trace('V(out)')          # Get the second trace

    steps = raw.get_steps()                 # Get list of step numbers ([0,1,2]) for sweeped simulations
                                            # Returns [0] if there is just 1 step 

    plt.figure()                            # Create the canvas for plotting

    _, (ax1, ax2) = plt.subplots(2, 1, sharex=True)  # Create two subplots

    for ax in (ax1, ax2):                   # Use grid on both subplots
        ax.grid(True)

    plt.xlim([0.9e-3, 1.2e-3])              # Limit the X axis to just a subrange

    ydata = vin.get_wave()                  # Get all the values (= data points) for the 'vin' trace
    xdata = raw.get_axis()                  # Get the X-axis data (time) for these data points
    ax1.plot(xdata, ydata)                  # Do an X/Y plot on first subplot

    for step in steps:                      # On the second plot, print all the STEPS of Vout
        ydata = vout.get_wave(step)         # Retrieve the values for this step
        xdata = raw.get_axis(step)          # Retrieve the time vector
        ax2.plot(xdata, ydata)              # Do X/Y plot on second subplot

    plt.show()                              # Show matplotlib's interactive window with the plots
