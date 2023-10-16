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
# Name:        raw_convert.py
# Purpose:     command line read of the raw file and output to CSV
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     17-01-2017
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
"""
Helper script to read the raw file and output to a CSV, Excel or Clipboard

Usage:
    raw_convert.py [options] <rawfile> <trace_list>

Options:
    -h --help               Show this screen
    -v --version            Show version
    -o --output=<file>      Output file name. Valid extensions are .csv, .xlsx
    -c --clipboard          Output to clipboard
    -s --separator=<sep>    Separator for CSV output [default: \t]

The script will read the raw file and output the specified traces to the chosen format.
In case of .TRAN simulations, the time column is always output. In case of .AC simulations
the frequency column is always output. The traces are specified in the <trace_list> as a
space separated list of trace names.
The V() qualifier is optional. If the trace name is not found, the script will try to
find the trace name with the V() qualifier. If the trace name is not found, the script
will try to find the trace name with the I() qualifier.

"""

from optparse import OptionParser
import clipboard
from spicelib.raw.raw_read import RawRead as LTSpiceRawRead


def main():
    usage = "usage: %prog [options] <rawfile> <trace_list>"
    parser = OptionParser(usage=usage, version="%prog 0.1")
    parser.add_option("-o", "--output", dest="output", default=None,
                      help="Output file name.\n"
                           "Use .csv for CSV output, .xlsx for Excel output",
                      metavar="FILE")
    parser.add_option("-c", "--clipboard", dest="clipboard", action="store_true",
                      help="Output to clipboard", default=False)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                      help="Verbose output", default=False)
    parser.add_option('-s', '--sep', dest='separator', default='\t',
                      help='Value separator for CSV output. Default: "\\t" <TAB>\n'
                           'Example: -d ";"'
                      )

    (options, args) = parser.parse_args()

    if len(args) < 1:
        print("Error: Missing arguments")
        parser.print_help()
        traces = '*'  # This is here just to avoid a warning on the IDE
        exit(1)
    elif len(args) < 2:
        traces = '*'
    else:
        traces = args[1:]

    rawfile = args[0]

    # Read the raw file
    if traces != '*':
        raw_data = LTSpiceRawRead(rawfile, '*', header_only=True, verbose=False)
        raw_traces = raw_data.get_trace_names()
        found_traces = []
        for trace in traces:
            if trace in raw_traces:
                found_traces.append(trace)
            else:
                if options.verbose:
                    print("Trace " + trace + " not found. Searching for V(" + trace + ")")
                if 'V(' + trace + ')' in raw_traces:
                    found_traces.append('V(' + trace + ')')
                else:
                    if options.verbose:
                        print("Trace V(" + trace + ") not found. Searching for I(" + trace + ")")
                    if 'I(' + trace + ')' in raw_traces:
                        found_traces.append('I(' + trace + ')')
                    else:
                        print("Warning: Trace " + trace + " not found")

        if len(found_traces) == 0:
            print("Error: No traces found")
            print("Available Traces:\n ")
            for trace in raw_traces:
                print("\t<" + trace + ">")
            exit(1)
        print("Reading traces: ", found_traces)
        raw_data = LTSpiceRawRead(rawfile, found_traces, verbose=options.verbose)
    else:
        raw_data = LTSpiceRawRead(rawfile, traces, verbose=options.verbose)

    # Output the file
    if options.output is None:
        data = raw_data.export()

        text = options.separator.join(data.keys()) + '\n'
        data_size = len(data[data.__iter__().__next__()])
        for i in range(data_size):
            text += options.separator.join([str(data[col][i]) for col in data.keys()]) + '\n'
        if options.clipboard:
            print(f"Copying to clipboard text with {len(text)} bytes")
            clipboard.copy(text)

        else:
            print(text)
    else:
        if options.output.endswith(".csv"):
            print("Writing CSV file...", end="")
            raw_data.to_csv(options.output, separator=options.separator, index=False)
            print("Done")
        elif options.output.endswith(".xlsx"):
            print("Writing Excel file...", end="")
            raw_data.to_excel(options.output, index=False)
            print("Done")
        else:
            print("Error: Unknown output format. Valid formats are '.csv' and '.xlsx'")
            parser.print_help()
            exit(1)
    exit(0)


if __name__ == "__main__":
    main()
