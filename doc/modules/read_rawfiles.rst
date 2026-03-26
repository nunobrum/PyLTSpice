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
It will return a :py:class:`spicelib.Trace` object.  Use this object's ``get_wave()`` method to get
the actual data points for a step.

Use the method ``get_axis()`` to get the 'time' data.  If there were multiple steps in the simulation, specify
the number for which step you want to retrieve the time data.

Now that you have lists with the times and corresponding values, you can plot this information in an X/Y plot. 

Note that all the data will be returned as numpy arrays.

Multiple result sets/plots in one RAW file
------------------------------------------

Most RAW files only have 1 result set (also called 'plot') in them, but some simulators (like ngspice) 
support multiple sets of results/plots in one RAW file. 
One can for example create a RAW file with both `Noise Spectral Density Curves` and `Integrated Noise` data, or 
create a series of plots via a loop through a series of values or simulation steps. 

If a RAW file contains multiple plots, they are simply individual plots concatenated in the same file.

RawRead will read all result sets/plots that are in the file, and expose them under the `plots` attribute, that is an array of `PlotData`.

Through that array you can for example access the first plot using ``raw.plots[0]``, the second plot using ``raw.plots[1]``, etc.

Since most RAW files only have 1 plot in them, and in order to facilitate access to the plot data, 
all properties and methods of the first plot are also available directly on the `RawRead` object. 
This means that you do not have to specify ``.plots[0]`` to access the first plot's properties or methods. For example,
``raw.get_axis()`` and ``raw.plots[0].get_axis()`` give the same result.

Examples:

.. code-block::

    from spicelib import RawRead
    raw = RawRead("some_random_file.raw")  # Read the RAW file contents from disk
    print(raw.get_plot_name())             # name of the first plot in the file
    print(raw.plots[0].get_plot_name())    # same as above
    print(raw.plots[1].get_plot_name())    # name of the second plot in the file
    print(raw.get_trace_names())           # names of all the traces of the first plot in the file
    print(raw.plots[1].get_trace_names())  # names of all the traces of the second plot in the file


Steps versus Multiple plots in the file versus SimStepper versus ltsteps.py
---------------------------------------------------------------------------

This can get confusing, so here is a summary of the differences:

- **steps** in ``RawRead``: This is based on the ``.step`` command, that allows multiple 
  runs with for example different component values. Not all simulators support it (ngspice does not).
  It produces a single plot with multiple steps, and the data is stored in both a RAW file and a LOG file.
  The steps all share the same trace names, but the values for each step can be different.
  ``RawRead`` will automatically read any steps, if they exist, and can present the data for example
  via the ``.get_wave('name', step)`` and ``.get_axis(step)`` methods.
- **Multiple plots in the file**: This is a feature of some simulators (like ngspice) that allows multiple
  result sets/plots in one RAW file. Each plot *can* have its own set of traces. 
  What traces and what data is written is controlled by the simulator, via ``.control`` .. ``.endc`` command (the language inside is known as the 'nutmeg' language). 
  See for example the `ngspice manual <https://ngspice.sourceforge.io/ngspice-control-language-tutorial.html#step>`_. 
  It is also possible to produce multiple extractions from one simulation, and then write them to the same raw file. 
  See ``examples/testfiles/ngsteps.net`` and ``examples/ngsteps.py`` for an example of how to do steps with ngspice and how to read the results.
  ``RawRead`` will automatically read all plots in the file, and expose them via the ``.plots`` attribute.
- **SimStepper**: This is a class that allows to multiple simulations with different parameters, and collect the results. It can be used with any simulator.
- **ltsteps.py**: This is a utility that can be used to extract data from various types of LTSpice files, be it related to ``.step``, ``.meas`` or ``.txt`` exports, and format it for import in a spreadsheet.

Class documentation
-------------------

See the class documentation for more details :

- :py:class:`spicelib.RawRead`
- :py:class:`spicelib.PlotData`
- :py:class:`spicelib.raw.raw_classes.Axis`
- :py:class:`spicelib.Trace`
- :py:class:`spicelib.raw.raw_classes.TraceRead`
- :py:class:`spicelib.sim.sim_stepping.SimStepper`


Example
-------

The example below demonstrates the usage of the RawRead class. It reads a .RAW file and uses the matplotlib
library to show the results of two traces in a separate subplots. 
It only handles the data of the first result set/plot in the file, as that is the most common use case.

.. code-block::

    from spicelib import RawRead
    import matplotlib.pyplot as plt         # use matplotlib for plotting the results

    raw = RawRead("some_random_file.raw")   # Read the RAW file contents from disk

    print(raw.get_trace_names())            # Get and print a list of all the traces
    print(raw.get_raw_properties())         # Print all the properties found in the Header section

    vin = raw.get_trace('V(in)')            # Get the trace data
    vout = raw.get_trace('V(out)')          # Get the second trace

    steps = raw.get_steps()                 # Get list of step numbers ([0,1,2]) for sweeped simulations
                                            # Returns [0] if there is just 1 step 

    plt.figure()                            # Create the canvas for plotting

    _, (ax1, ax2) = plt.subplots(2, 1, sharex=True)  # Create two subplots

    for ax in (ax1, ax2):                   # Use grid on both subplots
        ax.grid(True)

    plt.xlim([0.9e-3, 1.2e-3])              # Limit the X axis to just a subrange

    xdata = raw.get_axis()                  # Get the X-axis data (time)
	
    ydata = vin.get_wave()                  # Get all the values for the 'vin' trace
    ax1.plot(xdata, ydata)                  # Do an X/Y plot on first subplot
	
    ydata = vout.get_wave()                 # Get all the values for the 'vout' trace
    ax1.plot(xdata, ydata)                  # Do an X/Y plot on first subplot as well

    for step in steps:                      # On the second plot, print all the STEPS of Vout
        ydata = vout.get_wave(step)         # Retrieve the values for this step
        xdata = raw.get_axis(step)          # Retrieve the time vector
        ax2.plot(xdata, ydata)              # Do X/Y plot on second subplot

    plt.show()                              # Show matplotlib's interactive window with the plots

    # And now an example of reading a raw file that has multiple data sets/plots in it

    raw = RawRead("./testfiles/noise_multi.bin.raw")
    print(raw.get_plot_names())            # names of all the plots in the file
    print(raw.get_trace_names())           # names of all the traces of the first plot in the file
    print(raw.plots[0].get_trace_names())  # same as above
    print(raw.plots[1].get_trace_names())  # names of all the traces of the second plot in the file

    x = raw.get_trace('frequency')  # could have used raw.get_axis() as well here
    y = raw.get_trace('onoise_spectrum')
    plt.plot(x.get_wave(), y.get_wave(), label='noise spectrum')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Noise (V/vHz)')
    plt.yscale('log')
    plt.xscale('log')
    plt.legend()
    plt.show()

    # and get the integrated noise from the second part in the file
    total = raw.plots[1].get_trace('v(onoise_total)')
    print(f"Total Integral noise: {total.get_wave()[0]} V") 

