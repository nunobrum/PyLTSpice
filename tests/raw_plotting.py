import sys
import matplotlib.pyplot as plt
import os
from os.path import split as pathsplit
from os.path import join as pathjoin
import numpy as np
from numpy import abs as mag, angle
from PyLTSpice import RawRead


def what_to_units(whattype):
    """Determines the unit to display on the plot Y axis"""
    if 'voltage' in whattype:
        return 'V'
    if 'current' in whattype:
        return 'A'


directory = os.getcwd()

if len(sys.argv) > 1:
    raw_filename = sys.argv[1]
    trace_names = sys.argv[2:]
    if len(trace_names) == 0:
        trace_names = '*'
else:
    test_directory = pathjoin(pathsplit(directory)[0], 'tests')
    # filename = 'DC sweep.raw'
    # filename = 'tran.raw'
    # filename = 'tran - step.raw'
    # filename = 'ac.raw'
    # filename = 'AC - STEP.raw'
    # filename = 'PI_Filter_tf.raw'
    # filename = 'DC op point - STEP_1.raw'
    # filename = 'Noise.raw'
    # filename = "test2_gs_000.raw"
    filename = 'fra_eg1.fra_1.raw'
    filename = 'LTC6241_Noise.raw'
    # trace_names = ("run", "V(out)", "V(err)")
    trace_names = 'V(onoise)', 'V(inoise)'
    raw_filename = pathjoin(test_directory, filename)

LTR = RawRead(raw_filename, trace_names, verbose=True)
for param, value in LTR.raw_params.items():
    print("{}: {}{}".format(param, " " * (20 - len(param)), str(value).strip()))

if trace_names == '*':
    print("Reading all the traces in the raw file")
    trace_names = LTR.get_trace_names()

traces = [LTR.get_trace(trace) for trace in trace_names]
if LTR.axis is not None:
    steps_data = LTR.get_steps()
else:
    steps_data = [0]
print("Steps read are :", list(steps_data))

if 'complex' in LTR.flags:
    n_axis = len(traces) * 2
else:
    n_axis = len(traces)

fig, axis_set = plt.subplots(n_axis, 1, sharex='all')
write_labels = True

for i, trace in enumerate(traces):
    if 'complex' in LTR.flags:
        axises = axis_set[2 * i: 2 * i + 2]  # Returns two axis
    else:
        if n_axis == 1:
            axises = [axis_set]  # Needs to return a list
        else:
            axises = axis_set[i:i + 1]  # Returns just one axis but enclosed in a list
    magnitude = True
    for ax in axises:
        ax.grid(True)
        if 'log' in LTR.flags:
            ax.set_xscale('log')
        for step_i in steps_data:
            if LTR.axis:
                x = LTR.get_axis(step_i)
            else:
                x = np.arange(LTR.nPoints)
            y = LTR.get_wave(trace.name, step_i)
            if 'complex' in LTR.flags:
                x = mag(x)
                if magnitude:
                    ax.set_yscale('log')
                    y = mag(y)
                else:
                    y = angle(y, deg=True)
            if write_labels:
                ax.plot(x, y, label=str(steps_data[step_i]))
            else:
                ax.plot(x, y)
        write_labels = False

        if 'complex' in LTR.flags:
            if magnitude:
                title = f"{trace.name} Mag [db{what_to_units(trace.whattype)}]"
                magnitude = False
            else:
                title = f"{trace.name} Phase [deg]"
        else:
            title = f"{trace.name} [{what_to_units(trace.whattype)}]"
        ax.set_title(title)

plt.figlegend()
plt.show()
