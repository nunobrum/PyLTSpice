# -------------------------------------------------------------------------------
# Name:        LTSteps.py
# Purpose:     Process LTSpice output files and align data for usage in a spread-
#              sheet tool such as Excel, or Calc.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     19-05-2014
# Licence:     Free
# Version:     0.3  Transforming the procedure into a callable one in order
#              to call them from a higher level script.
# -------------------------------------------------------------------------------

__author__ = "Nuno Canto Brum <me@nunobrum.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"

import re
import os
import sys

if __name__ == "__main__":
    def message(*strs):
        for string in strs:
            print(string)
else:
    def message(*strs):
        pass


def enc_norm(line):
    if len(line) > 1 and line[0] == '\0':  # This is the stupid encoding of LTspice XVII
        return line[1::2]  # Removes zeros from the encoding
    else:
        return line  # Return as is


def reformat_LTSpice_export(export_file: str, tabular_file: str):
    """Reformat an LTSpice trace export to a tabular so that the step information is part of the columns exported
    The reformatted file is written into <tabular_file>"""
    fin = open(export_file, 'r')
    fout = open(tabular_file, 'w')

    headers = enc_norm(fin.readline())
    # writing header
    go_header = True
    run_no = 0  # Just to avoid warning, this is later overridden by the step information
    param_values = ""  # Just to avoid warning, this is later overridden by the step information
    regx = re.compile(r"Step Information: ([\w=\d\. -]+) +\(Run: (\d*)/\d*\)\n")
    for line in fin:
        line = enc_norm(line)
        if line.startswith("Step Information:"):
            match = regx.match(line)
            # message(line, end="")
            if match:
                # message(match.groups())
                step, run_no = match.groups()
                # message(step, line, end="")
                params = []
                for param in step.split():
                    params.append(param.split('=')[1])
                param_values = "\t".join(params)

                if go_header:
                    header_keys = []
                    for param in step.split():
                        header_keys.append(param.split('=')[0])
                    param_header = "\t".join(header_keys)
                    fout.write("Run\t%s\t%s" % (param_header, headers))
                    message("Run\t%s\t%s" % (param_header, headers))
                    go_header = False
                    # message("%s\t%s"% (run_no, param_values))
        else:
            fout.write("%s\t%s\t%s" % (run_no, param_values, line))

    fin.close()
    fout.close()


class LTSpiceExport(object):

    def __init__(self, filename: str):
        """Reads an LTSpice Export into a structured class containing all data. Data is accessible by
        other class functions"""
        fin = open(filename, 'r')
        file_header = enc_norm(fin.readline())

        self.headers = file_header.split('\t')
        # Set to read header
        go_header = True

        curr_dic = {}
        self.dataset = {}

        regx = re.compile(r"Step Information: ([\w=\d\. -]+) +\(Run: (\d*)/\d*\)\n")
        for line in fin:
            line = enc_norm(line)
            if line.startswith("Step Information:"):
                match = regx.match(line)
                # message(line, end="")
                if match:
                    # message(match.groups())
                    step, run_no = match.groups()
                    # message(step, line, end="")
                    curr_dic['runno'] = run_no
                    for param in step.split():
                        key, value = param.split('=')
                        curr_dic[key] = float(value)

                    if go_header:
                        go_header = False  # This is executed only once
                        for key in self.headers:
                            self.dataset[key] = []  # Initializes an empty list

                        for key in curr_dic:
                            self.dataset[key] = []  # Initializes an empty list

            else:
                values = line.split('\t')

                for key in curr_dic:
                    self.dataset[key].append(curr_dic[key])

                for i in range(len(values)):
                    self.dataset[self.headers[i]].append(float(values[i]))

        fin.close()


class LTSpiceLogReader(object):

    def __init__(self, logname: str):
        """Reads Step data from a LTSpice log file. Data is accessible """
        self.logname = logname
        fin = open(logname, 'r')
        self.dataset = {}
        self.headers = []  # This is only need to keep the parameter order in the export
        self.step_count = 0
        self.stepset = {}
        message("Processing LOG file", logname)
        # wait for the step information
        for line in fin:
            line = enc_norm(line)
            print(line)
            if line.startswith(".step "):
                print(line)
                break
        else:
            fin.close()
            return

        while line:
            if line.startswith(".step"):
                # message(line)
                self.step_count += 1
                tokens = line.strip('\n').split(' ')
                for tok in tokens[1:]:
                    lhs, rhs = tok.split("=")
                    ll = self.stepset.get(lhs, None)
                    if ll:
                        ll.append(rhs)
                    else:
                        self.stepset[lhs] = [rhs]
            elif line.startswith("Measurement:"):
                break
            line = enc_norm(fin.readline())
        fin.close()

    def read_measures(self, filename=None):
        if filename is None:
            filename = self.logname
        fin = open(filename, 'r')
        # self.dataset = {}  # Resets all loaded previous data
        dataname = None
        measurements = []

        if self.step_count == 0:  # then there are no steps,
            # there are only measures taken in the format parameter: measurement
            # A few examples of readings
            # vout_rms: RMS(v(out))=1.41109 FROM 0 TO 0.001  => Interval
            # vin_rms: RMS(v(in))=0.70622 FROM 0 TO 0.001  => Interval
            # gain: vout_rms/vin_rms=1.99809 => Parameter
            # vout1m: v(out)=-0.0186257 at 0.001 => Point
            regx = re.compile(r"^(?P<name>\w+):\s+.*=(?P<value>[\d\.E+\-\(\)dB,°]+)(( FROM (?P<from>[\d\.E+-]*) TO (?P<to>[\d\.E+-]*))|( at (?P<at>[\d\.E+-]*)))?", re.IGNORECASE)
            for line in fin:
                match = regx.match(line)
                if match:
                    # Get the data
                    dataname = match.group('name')
                    if match.group('from'):
                        params = [dataname, dataname + "_FROM", dataname + "_TO"]
                        measurements = [match.group('value'), match.group('from'), match.group('to')]
                    elif match.group('at'):
                        params = [dataname, dataname + "_at"]
                        measurements = [match.group('value'), match.group('at')]
                    else:
                        params = [dataname]
                        measurements = [match.group('value')]

                    self.headers.append(dataname)
                    self.dataset[dataname] = (params, [measurements])
            fin.close()
            return

        for line in fin:
            line = enc_norm(line)
            print(line)
            if line.startswith("Measurement:"):
                break

        # message("Reading Measurements")
        measure_count = 0
        param = ['param']  # Initializing an empty parameters
        while line:
            line = line.strip('\n')
            if line.startswith("Measurement: "):
                if dataname:
                    # store the info
                    if len(measurements):
                        message("Storing Measurement %s (count %d)" % (dataname, len(measurements)))
                        self.headers.append(dataname)
                        self.dataset[dataname] = (param, measurements)
                        param = ['param']
                    measurements = []
                dataname = line[13:]
                message("Reading Measurement %s" % line[13:])
            else:
                tokens = line.split("\t")
                if len(tokens) >= 2:
                    try:
                        int(tokens[0])  # This instruction only serves to trigger the exception
                        meas = tokens[1:]  # [float(x) for x in tokens[1:]]
                        measurements.append(meas)
                        measure_count += 1
                    except:
                        if len(tokens) >= 3 and (tokens[2] == "FROM" or tokens[2] == 'at'):
                            tokens[2] = dataname + '_' + tokens[2]
                        if len(tokens) >= 4 and tokens[3] == "TO":
                            tokens[3] = dataname + "_TO"
                        param = [dataname] + tokens[2:]
                else:
                    message("->", line)

            line = enc_norm(fin.readline())  # advance to the next line

        # storing the last data into the dataset
        message("Storing Measurement %s" % dataname)
        if len(measurements):
            self.dataset[dataname] = (param, measurements)
        self.headers.append(dataname)

        message("%d measurements" % len(self.headers))
        message("Identified %d steps, read %d measurements" % (self.step_count, measure_count))

    def get_measure(self, measure, param=0):
        data = self.dataset[measure]
        if len(data[0]) == 1:
            return data[1]
        else:
            if isinstance(param, str):
                k = data[0].index(param)
            else:
                k = int(param)
            return [x[k] for x in data[1]]

    def export_data(self, export_file: str, append_loginfo=None):
        # message(tokens)
        if append_loginfo is None:
            mode = 'w'  # rewrites the file
        else:
            mode = 'a'  # Appends an existing file

        if len(self.dataset) == 0:
            print("Empty data set. Exiting without writing file.")
            return
        fout = open(export_file, mode)
        # fout.write("%s\t%s\n" % ("\t".join(self.stepset.keys()), "\t\t".join(self.headers)))
        meas_headers = ["\t".join(self.dataset[param][0]) for param in self.headers]
        if append_loginfo is not None:  # if an append it will write the filename first
            fout.write('long information\t')

        fout.write("step\t%s\t%s\n" % ("\t".join(self.stepset.keys()), "\t".join(meas_headers)))
        for index in range(len(self.dataset[self.headers[0]][1])):
            if self.step_count == 0:
                step_data = []  # Empty step
            else:
                step_data = [self.stepset[param][index] for param in self.stepset.keys()]
            meas_data = [self.dataset[param][1][index] for param in self.headers]

            if append_loginfo is not None:  # if an append it will write the filename first
                fout.write(append_loginfo + '\t')
            fout.write("%d\t%s" % (index + 1, '\t'.join(step_data)))
            for tok in meas_data:
                if isinstance(tok, list):
                    for x in tok:
                        fout.write('\t%s' % x)
                else:
                    fout.write('\t%s' % tok)
            fout.write('\n')

        fout.close()


if __name__ == "__main__":

    def valid_extension(filename):
        return filename.endswith('.txt') or filename.endswith('.log') or filename.endswith('.mout')


    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if not valid_extension(filename):
            print("Invalid extension in filename '%s'" % filename)
            print("This tool only supports the following extensions :'.txt','.log','.mout'")
            exit(-1)
    else:
        filename = None
        newer_date = 0
        for f in os.listdir():
            date = os.path.getmtime(f)
            if date > newer_date and valid_extension(f):
                newer_date = date
                filename = f
    if filename is None:
        print("File not found")
        print("This tool only supports the following extensions :'.txt','.log','.mout'")
        exit(-1)

    fname_out = None
    if filename.endswith('.txt'):
        fname_out = filename.rstrip('txt') + 'tsv'
    elif filename.endswith('.log'):
        fname_out = filename.rstrip('log') + 'tlog'
    elif filename.endswith('.mout'):
        fname_out = filename.rstrip('mout') + 'tmout'
    else:
        print("Error in file type")
        print("This tool only supports the following extensions :'.txt','.log','.mout'")
        exit(-1)

    if fname_out is not None:
        print("Processing File %s" % filename)
        print("Creating File %s" % fname_out)
        if filename.endswith('txt'):
            print("Processing Data File")
            reformat_LTSpice_export(filename, fname_out)
        elif filename.endswith("log"):
            data = LTSpiceLogReader(filename)
            data.read_measures(filename)
            data.export_data(fname_out)
        elif filename.endswith(".mout"):
            # It must read first the step information
            data = LTSpiceLogReader(filename.rstrip('mout') + 'log')
            # Then we can read the measurement output file.
            data.read_measures(filename)
            data.export_data(fname_out)

    # input("Press Enter to Continue")
