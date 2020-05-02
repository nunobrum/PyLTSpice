#!/usr/bin/env python

# -------------------------------------------------------------------------------
# Name:        LTSpice_RawRead.py
# Purpose:     Process LTSpice output files and align data for usage in a spread-
#              sheet tool such as Excel, or Calc.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-12-2016
# Licence:     General Public GNU License
# -------------------------------------------------------------------------------

""" A pure python implementation of an LTSpice RAW file reader.
The reader returns a class containing all the traces read from the RAW File.
In case there there stepped data detected, it will try to open the simulation LOG file and
read the stepping information.
Traces are accessible by the method <LTSpiceReader instance>.get_trace(trace_ref) where trace_ref is either
the name of the net on the LTSPice Simulation. Normally trace references are stored with the format V(<node_name>)
for voltages or I(device_reference). For example V(n001) or I(R1) or Ib(Q1).
For checking step, the method <LTSpiceReader instance>.get_steps() is used. In case there are no steps in the simulation,
the class will return a single element list.
NOTE: This module tries to import the numpy if exists on the system.
If it finds numpy all data is later provided as an array. If not it will use a standard list of floats.
"""

__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"

import os
from binascii import b2a_hex
from struct import unpack

try:
    from numpy import zeros, array, complex128, abs as numpy_abs
except ImportError:
    USE_NNUMPY = False
else:
    USE_NNUMPY = True
    print("Found Numpy. WIll be used for storing data")


class DataSet(object):
    """Class for storing Traces."""

    def __init__(self, name, datatype, datalen, numerical_type='real'):
        """Base Class for both Axis and Trace Classes.
        Defines the common operations between both."""
        self.name = name
        self.type = datatype
        self.numerical_type = numerical_type
        if USE_NNUMPY:
            if numerical_type == 'real':
                self.data = zeros(datalen)
            elif numerical_type == 'complex':
                self.data = zeros(datalen, complex128)
        else:
            self.data = [None for x in range(datalen)]

    def set_pointA(self, n, value):
        """function to be used on ASCII RAW Files.
        :param n:     the point to set
        :param value: the Value of the point being set."""
        assert isinstance(value, float)
        self.data[n] = value

    def set_pointB8(self, n, value):
        """Function that converts the variable 0, normally associated with the plot X axis.
        The codification is done as follows:
               7   6   5   4     3   2   1   0
        Byte7  SGM SGE E9  E8    E7  E6  E5  E4         SGM - Signal of Mantissa: 0 - Positive 1 - Negative
        Byte6  E3  E2  E1  E0    M51 M50 M49 M48        SGE - Signal of Exponent: 0 - Positive 1 - Negative
        Byte5  M47 M46 M45 M44   M43 M42 M41 M40        E[9:0] - Exponent
        Byte4  M39 M38 M37 M36   M35 M34 M33 M32        M[51:0] - Mantissa.
        Byte3  M31 M30 M29 M28   M27 M26 M25 M24
        Byte2  M23 M22 M21 M20   M19 M18 M17 M16
        Byte1  M15 M14 M13 M12   M11 M10 M9  M8
        Byte0  M7  M6  M5  M4    M3  M2  M1  M0
        """
        self.data[n] = unpack("d", value)[0]

    def set_pointB16(self, n, value):
        (re, im) = unpack('dd', value)
        self.data[n] = complex(re, im)

    def set_pointB4(self, n, value):
        """Function that converts a normal trace into float on a Binary storage. This codification uses 4 bytes.
        The codification is done as follows:
               7   6   5   4     3   2   1   0
        Byte3  SGM SGE E6  E5    E4  E3  E2  E1         SGM - Signal of Mantissa: 0 - Positive 1 - Negative
        Byte2  E0  M22 M21 M20   M19 M18 M17 M16        SGE - Signal of Exponent: 0 - Positive 1 - Negative
        Byte1  M15 M14 M13 M12   M11 M10 M9  M8         E[6:0] - Exponent
        Byte0  M7  M6  M5  M4    M3  M2  M1  M0         M[22:0] - Mantissa.
        """
        self.data[n] = unpack("f", value)[0]

    def __str__(self):
        if isinstance(self.data[0], float):
            # data = ["%e" % value for value in self.data]
            return "name:'%s'\ntype:'%s'\nlen:%d\n%s" % (self.name, self.type, len(self.data), str(self.data))
        elif isinstance(self.data[0], complex):
            return "name: {}\ntype: {}\nlen: {:d}\n{}".format(self.name, self.type, len(self.data), str(self.data))
        else:
            data = [b2a_hex(value) for value in self.data]
            return "name:'%s'\ntype:'%s'\nlen:%d\n%s" % (self.name, self.type, len(self.data), str(data))

    def get_point(self, n):
        return self.data[n]

    def get_wave(self):
        return self.data

    def get_len(self):
        return len(self.data)


class Axis(DataSet):
    """This class is used to represent the horizontal axis like on a Transient or DC Sweep Simulation."""

    def __init__(self, name, datatype, datalen, numerical_type='real'):
        super().__init__(name, datatype, datalen, numerical_type)
        self.step_info = None

    def _set_steps(self, step_info):
        self.step_info = step_info

        self.step_offsets = [None for x in range(len(step_info))]

        # Now going to calculate the point offset for each step
        self.step_offsets[0] = 0
        i = 0
        k = 0
        while i < len(self.data):
            if self.data[i] == self.data[0]:
                # print(k, i, self.data[i], self.data[i+1])
                if self.data[i] == self.data[i + 1]:
                    i += 1  # Needs to add one here because the data will be repeated
                self.step_offsets[k] = i
                k += 1
            i += 1

        if k != len(self.step_info):
            raise LTSPiceReadException("The file a different number of steps than expected.\n" +
                                       "Expecting %d got %d" % (len(self.step_offsets), k))

    def step_offset(self, step):
        if self.step_info is None:
            if step > 0:
                return len(self.data)
            else:
                return 0
        else:
            if step >= len(self.step_offsets):
                return len(self.data)
            else:
                return self.step_offsets[step]

    def get_wave(self, step=0):
        # print(self.data)
        # print('step offset %d' % self.step_offset(step))
        # print(self.data[self.step_offset(step):self.step_offset(step + 1)])
        if step == 0:
            return self.data[:self.step_offset(1)]
        else:
            return self.data[self.step_offset(step):self.step_offset(step + 1)]

    def get_time_axis(self, step=0):
        if USE_NNUMPY:
            return numpy_abs(self.get_wave(step))
        else:
            shallow_copy = self.get_wave(step).copy()
            for i in range(len(shallow_copy)):
                if shallow_copy[i] < 0:
                    shallow_copy[i] = -shallow_copy[i]
            return shallow_copy


class Trace(DataSet):
    """Class used for storing generic traces that report to a given Axis."""

    def __init__(self, name, datatype, datalen, axis, numerical_type='real'):
        super().__init__(name, datatype, datalen, numerical_type)
        self.axis = axis

    def get_point(self, n=0, step=0):
        if self.axis is None:
            return super().get_point(n)
        else:
            return self.data[self.axis.step_offset(step) + n]

    def get_wave(self, step=0):
        # print('step size %d' % step)
        # print(self.data[self.axis.step_offset(step):self.axis.step_offset(step + 1)])
        if self.axis is None:
            return super().get_wave()
        else:
            if step == 0:
                return self.data[:self.axis.step_offset(1)]
            else:
                return self.data[self.axis.step_offset(step):self.axis.step_offset(step + 1)]


class Op(Trace):
    """Class used for storing operation points."""
    pass


class DummyTrace(object):
    """Dummy Trace for bypassing traces while reading"""

    def __init__(self, name, datatype):
        """Base Class for both Axis and Trace Classes.
        Defines the common operations between both."""
        self.name = name
        self.type = datatype

    def set_pointA(self, n, value):
        pass

    def set_pointB8(self, n, value):
        pass

    def set_pointB4(self, n, value):
        pass

    def set_pointB16(self, n, value):
        pass


class LTSPiceReadException(Exception):
    """Custom class for exception handling"""


class LTSpiceRawRead(object):
    """Class for reading LTSpice wave Files. It can read all types of Files. If stepped data is detected,
    it will also try to read the corresponding LOG file so to retrieve the stepped data.
    """
    header_lines = [
        "Title",
        "Date",
        "Plotname",
        "Output",
        "Flags",
        "No. Variables",
        "No. Points",
        "Offset",
        "Command",
        "Variables",
        "Backannotation"
    ]

    def __init__(self, raw_filename, traces_to_read='*', **kwargs):
        """The arguments for this class are:
    raw_filename   - The file containing the RAW data to be read
    traces_to_read - A string containing the list of traces to be read. If None is provided, only the header is read
                     and all trace data is discarded. If a '*' wildcard is given, all traces are read.
    kwargs         - Keyword parameters that define the options for the loading. Options are:
                        loadmem - If true, the file will only read waveforms to memory
    """
        assert isinstance(raw_filename, str)
        if not traces_to_read is None:
            assert isinstance(traces_to_read, str)

        raw_file_size = os.stat(raw_filename).st_size  # Get the file size in order to know the data size
        raw_file = open(raw_filename, "rb")

        ch = raw_file.read(6)
        if ch.decode(encoding='utf_8') == 'Title:':
            self.encoding = 'utf_8'
            sz_enc = 1
            line = 'Title:'
        elif ch.decode(encoding='utf_16_le') == 'Tit':
            self.encoding = 'utf_16_le'
            sz_enc = 2
            line = 'Tit'

        # Storing the filename as part of the dictionary
        self.raw_params = {"Filename": raw_filename}  # Initializing the dictionary that contains all raw file info
        self.backannotations = []  # Storing backannotations
        header = []
        while True:
            ch = raw_file.read(sz_enc).decode(encoding=self.encoding)
            if ch == '\n':
                if self.encoding == 'utf_8':  # must remove the \r
                    line = line.rstrip('\r')
                header.append(line)
                if line in ('Binary:', 'Values:'):
                    self.binary_start = raw_file.tell()
                    self.raw_type = line
                    break
                line = ""
            else:
                line += ch
        for line in header:
            k, _, v = line.partition(':')
            if k == 'Variables':
                break
            self.raw_params[k] = v
        self.nPoints = int(self.raw_params['No. Points'], 10)
        self.nVariables = int(self.raw_params['No. Variables'], 10)
        self._traces = []
        self.steps = None
        self.axis = None  # Creating the axis
        if 'complex' in self.raw_params['Flags']:
            numerical_type = 'complex'
        else:
            numerical_type = 'real'
        i = header.index('Variables:')
        ivar = 0
        for line in header[i + 1:-1]:
            _, name, var_type = line.lstrip().split('\t')
            if ivar == 0 and self.nVariables > 1 and self.nPoints != 1:
                self.axis = Axis(name, var_type, self.nPoints, numerical_type)
                self._traces.append(self.axis)
            elif self.nPoints == 1:
                self._traces.append(Op(name, var_type, self.nPoints, self.axis))
            elif ((traces_to_read == "*") or
                  (name in traces_to_read) or
                  (ivar == 0)):
                # TODO: Add wildcards to the waveform matching
                trace = Trace(name, var_type, self.nPoints, self.axis, numerical_type)
                self._traces.append(trace)
            else:
                self._traces.append(DummyTrace(name, var_type))
            ivar += 1

        if traces_to_read is None or len(self._traces) == 0:
            # The read is stopped here if there is nothing to read.
            raw_file.close()
            return

        if kwargs.get("headeronly", False):
            raw_file.close()
            return

        if self.raw_type == "Binary:":
            # Will start the reading of binary values
            # But first check whether how data is stored.
            self.block_size = (raw_file_size - self.binary_start) // self.nPoints
            self.data_size = self.block_size // self.nVariables
            if "fastaccess" in self.raw_params["Flags"]:
                print("Fast access")
                # A fast access means that the traces are grouped together.
                for var in self._traces:
                    if isinstance(var, DummyTrace):
                        # TODO: replace this by a seek
                        raw_file.read(self.nPoints * self.data_size)
                    else:
                        if self.data_size == 8 or isinstance(var, Axis):
                            for point in range(self.nPoints):
                                value = raw_file.read(8)
                                var.set_pointB8(point, value)
                        elif self.data_size == 16:
                            for point in range(self.nPoints):
                                value = raw_file.read(16)
                                var.set_pointB16(point, value)
                        else:  # Data size is 4
                            for point in range(self.nPoints):
                                value = raw_file.read(4)
                                var.set_pointB4(point, value)

            else:
                print("Normal access")
                # This is the default save after a simulation where the traces are scattered
                if self.data_size == 8:
                    for point in range(self.nPoints):
                        for var in self._traces:
                            value = raw_file.read(8)
                            var.set_pointB8(point, value)
                elif self.data_size == 16:
                    for point in range(self.nPoints):
                        for var in self._traces:
                            value = raw_file.read(16)
                            var.set_pointB16(point, value)
                else:  # data size is only 4 bytes
                    for point in range(self.nPoints):
                        value = raw_file.read(8)  # first variable (ex:time) is always 8 bytes
                        self._traces[0].set_pointB8(point, value)
                        for var in self._traces[1:]:
                            value = raw_file.read(4)
                            var.set_pointB4(point, value)

        elif self.raw_type == "Values:":
            # Will start the reading of ASCII Values
            for point in range(self.nPoints):
                first_var = True
                for var in self._traces:
                    line = raw_file.readline() \
                        .decode(encoding=self.encoding, errors='ignore')
                    # raw_file.seek(raw_file.tell() + self.offset)  # Move past 0x00 from prev. line
                    # print(line)

                    if first_var:
                        first_var = False
                        spoint = line.split("\t", 1)[0]
                        # print(spoint)
                        if point != int(spoint):
                            print("Error Reading File")
                            break
                        value = float(line[len(spoint):-1])
                    else:
                        value = float(line[:-1])
                    var.set_pointA(point, value)
        else:
            raw_file.close()
            raise LTSPiceReadException("Unsupported RAW File. ""%s""" % self.raw_type)

        raw_file.close()

        # Setting the properties in the proper format
        self.raw_params["No. Points"] = self.nPoints
        self.raw_params["No. Variables"] = self.nVariables
        self.raw_params["Variables"] = [var.name for var in self._traces]
        # Now Purging Dummy Traces
        i = 0
        while i < len(self._traces):
            if isinstance(self._traces[i], DummyTrace):
                del self._traces[i]
            else:
                i += 1

        # Finally, Check for Step Information
        if "stepped" in self.raw_params["Flags"]:
            self._load_step_information(raw_filename)

    def get_raw_property(self, property_name=None):
        """Get a property. By default it returns everything"""
        if property_name is None:
            return self.raw_params
        elif property_name in self.raw_params.keys():
            return self.raw_params[property_name]
        else:
            return "Invalid property. Use %s" % str(self.raw_params.keys())

    def get_trace_names(self):
        return [trace.name for trace in self._traces]

    def get_trace(self, trace_ref):
        """Retrieves the trace with the name given. """
        if isinstance(trace_ref, str):
            for trace in self._traces:
                if trace_ref == trace.name:
                    # assert isinstance(trace, DataSet)
                    return trace
            return None
        else:
            return self._traces[trace_ref]

    def get_time_axis(self, step=0):
        """This funcion is to workaround on a LTSpice issue when using 2nd Order compression, where some values
        have a negative value"""
        return abs(self.get_trace('time').get_wave(step))

    def _load_step_information(self, filename):
        # Find the extension of the file
        if not filename.endswith(".raw"):
            raise LTSPiceReadException("Invalid Filename. The file should end with '.raw'")
        logfile = filename[:-3] + 'log'
        try:
            log = open(logfile, 'r')
        except:
            raise LTSPiceReadException("Step information needs the '.log' file generated by LTSpice")
        for line in log:
            if line.startswith(".step"):
                step_dict = {}
                for tok in line[6:-1].split(' '):
                    key, value = tok.split('=')
                    try:
                        # Tries to convert to float for backward compatibility
                        value = float(value)
                    except:
                        pass
                        # Leave value as a string to accomodate cases as temperature steps
                        # Temperature steps have the form '.step temp=25°C'
                    step_dict[key] = value
                if self.steps is None:
                    self.steps = [step_dict]
                else:
                    self.steps.append(step_dict)
        log.close()
        if not (self.steps is None):
            # Individual access to the Trace Classes, this information is stored in the Axis
            # which is always in position 0
            self._traces[0]._set_steps(self.steps)
            pass

    def __getitem__(self, item):
        """Helper function to access traces by using the [ ] operator."""
        return self.get_trace(item)

    def get_steps(self, **kwargs):
        if self.steps is None:
            return [0]  # returns an single step
        else:
            if len(kwargs) > 0:
                ret_steps = []  # Initializing an empty array
                i = 0
                for step_dict in self.steps:
                    for key in kwargs:
                        ll = step_dict.get(key, None)
                        if ll is None:
                            break
                        elif kwargs[key] != ll:
                            break
                    else:
                        ret_steps.append(i)  # All the step parameters match
                    i += 1
                return ret_steps
            else:
                return range(len(self.steps))  # Returns all the steps


# Instruction for compatibility with modification made by other users
RawRead = LTSpiceRawRead

'''
This section is for testing your code
'''

if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt
    import os
    from os.path import split as pathsplit
    from os.path import join as pathjoin

    directory = os.getcwd()

    if len(sys.argv) > 1:
        raw_filename = sys.argv[1]
    else:
        test_directory = pathjoin(pathsplit(directory)[0], 'test_files')
        filename = 'testfile.raw'
        raw_filename = pathjoin(test_directory, filename)

    LTR = RawRead(raw_filename)

    print(LTR.get_trace_names())
    print(LTR.get_raw_property())

    plt.figure()

    volt_1 = LTR.get_trace('V(in)')
    volt_2 = LTR.get_trace('V(out)')
    x = LTR.get_trace('time')  # Zero is always the X axis
    # steps = LTR.get_steps(ana=4.0)
    steps = LTR.get_steps()
    print(steps)
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    for ax in (ax1, ax2):
        ax.grid(True)

    plt.xlim([0.9e-3, 1.2e-3])
    ax1.plot(x.get_time_axis(0), volt_1.get_wave(0))
    for step in steps:
        ax2.plot(x.get_time_axis(step), volt_2.get_wave(step))
        # plt.plot(y.get_wave(step))
        # plt.plot(x.get_wave(step),marker='x')
        # plt.plot(x.get_wave(step), y.get_wave(step), label=LTR.steps[step])

    plt.show()
'''
'''
# out = open("RAW_TEST_out_test1.txt", 'w')
#
# for step in LTR.get_steps():
#     for x in range(len(LTR[0].data)):
#         out.write("%s, %e, %e\n" % (step, LTR[0].data[x], LTR[2].data[x]))
# out.close()
