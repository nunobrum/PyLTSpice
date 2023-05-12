#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        Histogram.py
# Purpose:     Make an histogram plot based on the results of an LTSpice log file
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     17-01-2017
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
from numpy import angle, arange


from PyLTSpice import RawRead


def main():
    """Uses matplotlib to plot the data in the raw file"""
    import sys
    import matplotlib.pyplot as plt
    import os
    from os.path import split as path_split
    from os.path import join as path_join
    from numpy import abs as mag

    def what_to_units(whattype):
        """Determines the unit to display on the plot Y axis"""
        if 'voltage' in whattype:
            return 'V'
        if 'current' in whattype:
            return 'A'

    directory = os.getcwd()

    if len(sys.argv) > 2:
        raw_filename = sys.argv[1]
        trace_names = sys.argv[2:]
    else:
        print("Usage: rawplot.py RAW_FILE TRACE_NAME")
        print("TRACE_NAME is the traces to plot")
        sys.exit(-1)

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

    fig, axis_set = plt.subplots(nrows=n_axis, ncols=1, sharex='all')
    write_labels = True

    for i, trace in enumerate(traces):
        if 'complex' in LTR.flags:
            axis_set = axis_set[2 * i: 2 * i + 2]  # Returns two axis
        else:
            if n_axis == 1:
                axis_set = [axis_set]  # Needs to return a list
            else:
                axis_set = axis_set[i:i + 1]  # Returns just one axis but enclosed in a list
        magnitude = True
        for ax in axis_set:
            ax.grid(True)
            if 'log' in LTR.flags:
                ax.set_xscale('log')
            for step_i in steps_data:
                if LTR.axis:
                    x = LTR.get_axis(step_i)
                else:
                    x = arange(LTR.nPoints)
                y = traces[i].get_wave(step_i)
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
'''
'''
# out = open("RAW_TEST_out_test1.txt", 'w')
#
# for step in LTR.get_steps():
#     for x in range(len(LTR[0].data)):
#         out.write("%s, %e, %e\n" % (step, LTR[0].data[x], LTR[2].data[x]))
# out.close()
if __name__ == "__main__":
    main()
