#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
# Name:        LTSpice_RawRead.py
# Purpose:     Process LTSpice output files and align data for usage in a spread-
#              sheet tool such as Excel, or Calc.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-12-2016
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

"""
This module reads data from an LTSpice RAW file.
The main class object is the LTSpiceRawRead which is initialized with the filename of the RAW file to be processed.
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

   + Plotname:       => Name of the simulation Ex: "Transient Analysis" or "AC Analysis"

   + Output:         => *significance not understood*

   + Flags:          => Flags that are used in this plot. The simulation can have any combination of these flags.
                      * "real" -> The traces in the raw file contain real values. As for exmple on a TRAN simulation.
                      * "complex" -> Traces in the raw file contain complex values. As for exmple on an AC simulation.
                      * "forward" -> TBC
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
The variable list contains the list of measurements saved in the raw file. The order of the variables defines how they are
stored in the binary section. The format is one variable per line, using the following format:

<tab><ordinal number><tab><measurement><tab><type of measurement>

Here is an example:

.. code-block:: text

	0	time	time
	1	V(n001)	voltage
	2	V(n004)	voltage
	3	V(n003)	voltage
	4	V(n006)	voltage
	5	V(display_current_adc)	voltage
	6	V(n002)	voltage
	7	V(3v3_m)	voltage
	8	V(n005)	voltage
	9	V(n007)	voltage
	10	V(24v_dsp)	voltage
	11	I(C3)	device_current
	12	I(C2)	device_current
	13	I(C1)	device_current
	14	I(I1)	device_current
	15	I(R4)	device_current
	16	I(R3)	device_current
	17	I(V2)	device_current
	18	I(V1)	device_current
	19	Ix(u1:+)	subckt_current
	20	Ix(u1:-)	subckt_current

Binary Section
--------------
The binary section of .RAW file is where the data is usually written, unless the user had explicitly specified an ASCII
representation. In this case this section is replaced with a "Values" section.
LTSpice stores data directly onto the disk during simulation, writing per each time or frequency step the list of
values, as exemplified below for a .TRAN simulation.

     <timestamp 0><trace 1><trace 2><trace 3><trace 4>.....<trace N><timestamp 1><trace 1><trace2 >...

Depending on the type of simulation the type of data changes.
On TRAN simulations the timestamp is always stored as 8 bytes float (double) and trace values as a 4 bytes (single).
On AC simulations the data is stored in complex format, which includes a real part and an imaginary part, each with 8
bytes.
The way we determine the size of the data is dividing the total block size by the number of points, then taking only
the integer part.

Fast Access
-----------

Once a simulation is done, the user can ask LTSpice to optimize the data structure in such that he variables are stored
contiguously as illustrated below.

     <timestamp 0><trace 1><trace 2><trace 3><trace 4>.....<trace N><timestamp 1><trace 1><trace2 >...

This can speed up the data reading. Note that this transformation is not done automatically. Transforming data to Fast
Access must be requested by the user. If the transformation is done, it is registered in the Flags: line in the
header. RawReader supports both Normal and Fast Access formats

Classes Defined
===============

The .RAW file is read during the construction (constructor method) of an `LTSpiceRawRead` object. All traces on the RAW
file are uploaded into memory.

The LTSpiceRawRead class then has all the methods that allow the user to access the Axis and Trace Values. If there is
any stepped data (.STEP primitives), the LTSpiceRawRead class will try to load the log information from the same
directory as the raw file in order to obtain the STEP information.

Follows an example of the LTSpiceRawRead class usage. Information on the LTSpiceRawRead methods can be found here.

Examples
========

The example below demonstrates the usage of the LTSpiceRawRead class. It reads a .RAW file and uses the matplotlib library
to plot the results of three traces in two subplots. ::

    import matplotlib.pyplot as plt  # Imports the matplotlib library for plotting the results

    LTR = RawRead("some_random_file.raw")  # Reads the RAW file contents from file

    print(LTR.get_trace_names())  # Prints the contents of the RAW file. The result is a list, and print formats it.
    print(LTR.get_raw_property())  # Prints all the properties found in the Header section.

    plt.figure()  # Creates the canvas for plotting

    vin = LTR.get_trace('V(in)')  # Get's the trace data. If Numpy is installed, then it comes in numpy array format.
    vout = LTR.get_trace('V(out)') # Get's the second trace.

    steps = LTR.get_steps()  # Get's the step information. Returns a list of step numbers, ex: [0,1,2...]. If no steps
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
__copyright__ = "Copyright 2017, Fribourg Switzerland"

import os
from binascii import b2a_hex
from collections import OrderedDict
from struct import unpack
from typing import Union, List, Tuple
from PyLTSpice.detect_encoding import detect_encoding

try:
    from numpy import zeros, array, complex128, abs as np_abs, single, double, frombuffer, angle
except ImportError:
    USE_NNUMPY = False
else:
    USE_NNUMPY = True
    print("Found Numpy. Will be used for storing data")


def read_float64(f):
    """
    Reads a 64 bit float value, normally associated with the plot X axis.
    The codification is done as follows:

    =====  === === === ===   === === === ===
    bit#   7   6   5   4     3   2   1   0
    =====  === === === ===   === === === ===
    Byte7  SGM SGE E9  E8    E7  E6  E5  E4
    Byte6  E3  E2  E1  E0    M51 M50 M49 M48
    Byte5  M47 M46 M45 M44   M43 M42 M41 M40
    Byte4  M39 M38 M37 M36   M35 M34 M33 M32
    Byte3  M31 M30 M29 M28   M27 M26 M25 M24
    Byte2  M23 M22 M21 M20   M19 M18 M17 M16
    Byte1  M15 M14 M13 M12   M11 M10 M9  M8
    Byte0  M7  M6  M5  M4    M3  M2  M1  M0
    =====  === === === ===   === === === ===

    Legend:

    SGM - Signal of Mantissa: 0 - Positive 1 - Negative

    SGE - Signal of Exponent: 0 - Positive 1 - Negative

    E[9:0] - Exponent

    M[51:0] - Mantissa.

    :param f: data stream to convert to float value
    :type f: file
    :returns: double precision float
    :rtype: float
    """
    s = f.read(8)
    return unpack("d", s)[0]


def read_complex(f):
    """
    Used to convert a 16 byte stream into a complex data point. Usually used for the .AC simulations.
    The encoding is the same as for the set_pointB8() but two values are encoded. First one is the real part and
    the second is the complex part.

    :param f: data stream
    :type f: file
    :return: complex value
    :rtype: complex
    """
    s = f.read(16)
    (re, im) = unpack('dd', s)
    return complex(re, im)


def read_float32(f):
    """
    Reads a 32bit float (single precision) from a stream. This is how most real values are stored in the RAW file.
    This codification uses 4 bytes as follows:

    =====  === === === ===   === === === ===
    bit#   7   6   5   4     3   2   1   0
    =====  === === === ===   === === === ===
    Byte3  SGM SGE E6  E5    E4  E3  E2  E1
    Byte2  E0  M22 M21 M20   M19 M18 M17 M16
    Byte1  M15 M14 M13 M12   M11 M10 M9  M8
    Byte0  M7  M6  M5  M4    M3  M2  M1  M0
    =====  === === === ===   === === === ===

    Legend:

    SGM - Signal of Mantissa: 0 - Positive 1 - Negative

    SGE - Signal of Exponent: 0 - Positive 1 - Negative

    E[6:0] - Exponent

    M[22:0] - Mantissa.

    :param f: data stream to read from
    :type f: file
    :returns: float value
    :rtype: float
    """
    s = f.read(4)
    return unpack("f", s)[0]


def consume4bytes(f):
    """Used to advance the file pointer 4 bytes"""
    f.read(4)


def consume8bytes(f):
    """Used to advance the file pointer 8 bytes"""
    f.read(8)


def consume16bytes(f):
    """Used to advance the file pointer 16 bytes"""
    f.read(16)


class DataSet(object):
    """
    This is the base class for storing all traces inside of a RAW file. Returned by the get_trace() or by the get_axis()
    methods.
    Normally the user doesn't have to be aware of this class. It is only used internally to encapsulate the different
    implementations of the wave population.
    Data can be retrieved directly by using the [] operator.
    If numpy is available, the numpy vector can be retrieved by using the get_wave() method.
    """

    def __init__(self, name, whattype, datalen, numerical_type='real'):
        """Base Class for both Axis and Trace Classes.
        Defines the common operations between both."""
        self.name = name
        self.whattype = whattype
        self.numerical_type = numerical_type
        if USE_NNUMPY:
            if whattype == 'time':
                self.data = zeros(datalen, dtype=double)
            elif numerical_type == 'real':
                self.data = zeros(datalen, dtype=single)
            elif numerical_type == 'complex':
                self.data = zeros(datalen, dtype=complex128)
            else:
                raise NotImplementedError
        else:
            self.data = [None for _ in range(datalen)]

    def __str__(self):
        if isinstance(self.data[0], float):
            # data = ["%e" % value for value in self.data]
            return "name:'%s'\ntype:'%s'\nlen:%d\n%s" % (self.name, self.whattype, len(self.data), str(self.data))
        elif isinstance(self.data[0], complex):
            return "name: {}\ntype: {}\nlen: {:d}\n{}".format(self.name, self.whattype, len(self.data), str(self.data))
        else:
            data = [b2a_hex(value) for value in self.data]
            return "name:'%s'\ntype:'%s'\nlen:%d\n%s" % (self.name, self.whattype, len(self.data), str(data))

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __len__(self):
        return len(self.data)

    def get_point(self, n):
        """
        Get a point from the dataset
        :param n: position on the vector
        :type n:int
        :returns: Value of the data point
        :rtype: float or complex
        """
        return self.data[n]

    def get_wave(self):
        """
        :return: Internal data array
        :rtype: list or numpy.array
        """
        return self.data

    def get_len(self) -> int:
        """
        :return: The number of data points
        :rtype: int
        """
        return len(self.data)


class Axis(DataSet):
    """This class is used to represent the horizontal axis like on a Transient or DC Sweep Simulation. It derives from
    the DataSet and defines additional methods that are specific for X axis.
    This class is constructed by the get_time_axis() method or by a get_trace(0) command. In RAW files the trace 0 is
    always the X Axis. Ex: time for .TRAN simulations and frequency for the .AC simulations.

    To access data inside this class, the get_wave() should be used, which implements the support for the STEPed data.
    IF Numpy is available, get_wave() will return a numpy array.
    """

    def __init__(self, name: str, whattype: str, datalen: int, numerical_type: str ='real'):
        super().__init__(name, whattype, datalen, numerical_type)
        self.step_info = None

    def _set_steps(self, step_info: List[dict]):
        self.step_info = step_info

        self.step_offsets = [None for _ in range(len(step_info))]

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

    def step_offset(self, step: int):
        """
        In Stepped RAW files, several simulations runs are stored in the same RAW file. This function returns the
        offset within the binary stream where each step starts.

        :param step: Number of the step within the RAW file
        :type step: int
        :return: The offset within the RAW file
        :rtype: int
        """
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

    def get_wave(self, step: int =0):
        """
        Returns an the vector containing the wave values. If numpy is installed, data is returned as a numpy array.
        If not, the wave is returned as a list of floats.

        If stepped data is present in the array, the user should specify which step is to be returned. Failing to do so,
        will return all available steps concatenated together.

        :param step: Optional step in stepped data raw files.
        :type step: int
        :return: The trace values
        :rtype: list[float] or numpy.array
        """
        # print(self.data)
        # print('step offset %d' % self.step_offset(step))
        # print(self.data[self.step_offset(step):self.step_offset(step + 1)])
        if step == 0:
            return self.data[:self.step_offset(1)]
        else:
            return self.data[self.step_offset(step):self.step_offset(step + 1)]

    def get_time_axis(self, step: int = 0):
        """
        Returns the time axis raw data. Please note that the time axis may not have a constant time step. LTSpice will
        increase the time-step in simulation phases where there aren't value changes, and decrease time step in
        the parts where more time accuracy is needed.

        :param step: Optional step number if reading a raw file with stepped data.
        :type step: int
        :return: time axis
        :rtype: list[float] or numpy.array
        """
        if USE_NNUMPY:
            return np_abs(self.get_wave(step))
        else:
            shallow_copy = self.get_wave(step).copy()
            for i in range(len(shallow_copy)):
                if shallow_copy[i] < 0:
                    shallow_copy[i] = -shallow_copy[i]
            return shallow_copy


class Trace(DataSet):
    """This class is used to represent a trace. It derives from DataSet and implements the additional methods to
    support STEPed simulations.
    This class is constructed by the get_trace() command.
    Data can be accessed through the [] and len() operators, or by the get_wave() method.
    If numpy is available the get_wave() method will return a numpy array.
    """

    def __init__(self, name, whattype, datalen, axis, numerical_type='real'):
        super().__init__(name, whattype, datalen, numerical_type)
        self.axis = axis

    def get_point(self, n: int, step: int = 0):
        """
        Implementation of the [] operator. Do not use this method directly.

        :param n: item in the array
        :type n: int
        :param step: Optional step number
        :type step: int
        :return: float value of the item
        :rtype: float
        """
        if self.axis is None:
            return super().get_point(n)
        else:
            return self.data[self.axis.step_offset(step) + n]

    def get_wave(self, step=0):
        """
        Returns the data contained in this object. For stepped simulations an argument must be passed specifying the
        the step number. If no steps exist, the argument must be left blank.
        To know whether stepped data exist, the user can use the get_raw_property('Flags') method.

        If numpy is available the get_wave() method will return a numpy array.

        :param step: To be used when stepped data exist on the RAW file.
        :type step: int
        :return: a List or numpy array (if installed) containing the data contained in this object.
        :rtype: list or numpy.array
        """
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

    def __init__(self, name, whattype):
        """Base Class for both Axis and Trace Classes.
        Defines the common operations between both."""
        self.name = name
        self.whattype = whattype
        self.data = None


class LTSPiceReadException(Exception):
    """Custom class for exception handling"""


class LTSpiceRawRead(object):
    """Class for reading LTSpice wave Files. It can read all types of Files. If stepped data is detected,
    it will also try to read the corresponding LOG file so to retrieve the stepped data.

    :param raw_filename: The file containing the RAW data to be read
    :type raw_filename: str
    :param traces_to_read:
        A string or a list containing the list of traces to be read. If None is provided, only the header is read and
        all trace data is discarded. If a '*' wildcard is given or no parameter at all then all traces are read.
    :type traces_to_read: str, list or tuple
    :key headeronly:
        Used to only load the header information and skip the trace data entirely. Use `headeronly=True`.
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

    def __init__(self, raw_filename: str, traces_to_read: Union[str, List[str], Tuple[str], None] = '*', **kwargs):
        self.verbose = kwargs.get('verbose', True)
        assert isinstance(raw_filename, str), "RAW filename is expected to be a string"
        if traces_to_read is not None:
            assert isinstance(traces_to_read, (str, list, tuple)), "traces_to_read must be a string, a list or None"

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
        if self.verbose:
            print("Reading file with encoding ", self.encoding)
        # Storing the filename as part of the dictionary
        self.raw_params = OrderedDict(Filename=raw_filename)  # Initializing the dictionary that contains all raw file info
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
        self.flags = self.raw_params['Flags'].split()
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

            scan_functions = []
            for trace in self._traces:
                if self.data_size == 8:
                    if trace.data is None:
                        fun = consume8bytes
                    else:
                        fun = read_float64
                elif self.data_size == 16:
                    if trace.data is None:
                        fun = consume16bytes
                    else:
                        fun = read_complex
                else:  # data size is only 4 bytes
                    if len(scan_functions) == 0:  # This is the axis
                        fun = read_float64
                    else:
                        if trace.data is None:
                            fun = consume4bytes
                        else:
                            fun = read_float32
                scan_functions.append(fun)

            if "fastaccess" in self.raw_params["Flags"]:
                if self.verbose:
                    print("Fast access")
                # A fast access means that the traces are grouped together.
                for i, var in enumerate(self._traces):
                    if isinstance(var, DummyTrace):
                        # TODO: replace this by a seek
                        raw_file.read(self.nPoints * self.data_size)
                    else:
                        if USE_NNUMPY:
                            if self.data_size == 8:
                                s = raw_file.read(self.nPoints * 8)
                                var.data = frombuffer(s, dtype=double)
                            elif self.data_size == 16:
                                s = raw_file.read(self.nPoints * 16)
                                var.data = frombuffer(s, dtype=complex)
                            else:
                                if i == 0:
                                    s = raw_file.read(self.nPoints * 8)
                                    var.data = frombuffer(s, dtype=double)
                                else:
                                    s = raw_file.read(self.nPoints * 4)
                                    var.data = frombuffer(s, dtype=single)
                        else:
                            for point in range(self.nPoints):
                                var.data[point] = scan_functions[i](raw_file)

            else:
                if self.verbose:
                    print("Normal access")
                # This is the default save after a simulation where the traces are scattered
                for point in range(self.nPoints):
                    for i, var in enumerate(self._traces):
                        value = scan_functions[i](raw_file)
                        if value is not None:
                            var.data[point] = value

        elif self.raw_type == "Values:":
            # Will start the reading of ASCII Values
            for point in range(self.nPoints):
                first_var = True
                for var in self._traces:
                    line = raw_file.readline().decode(encoding=self.encoding, errors='ignore')
                    if first_var:
                        first_var = False
                        spoint = line.split("\t", 1)[0]

                        if point != int(spoint):
                            print("Error Reading File")
                            break
                        value = line[len(spoint):-1]
                    else:
                        value = line[:-1]
                    var.data[point] = float(value)
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
            try:
                self._load_step_information(raw_filename)
            except Exception:
                print("LOG file not found or problems happened while reading it. Auto-detecting steps")
                number_of_steps = 0
                for v in self.axis:
                    if v == self.axis[0]:
                        number_of_steps += 1
                self.steps = [{'run': i+1} for i in range(number_of_steps)]

            if not (self.steps is None):
                # Individual access to the Trace Classes, this information is stored in the Axis
                # which is always in position 0
                self._traces[0]._set_steps(self.steps)

    def get_raw_property(self, property_name=None):
        """
        Get a property. By default it returns all properties defined in the RAW file.

        :param property_name: name of the property to retrieve.
        :type property_name: str
        :returns: Property object
        :rtype: str
        :raises: ValueError if the property doesn't exist
        """
        if property_name is None:
            return self.raw_params
        elif property_name in self.raw_params.keys():
            return self.raw_params[property_name]
        else:
            raise ValueError("Invalid property. Use %s" % str(self.raw_params.keys()))

    def get_trace_names(self):
        """
        Returns a list of exiting trace names inside of the RAW file.

        :return: trace names
        :rtype: list[str]
        """
        return [trace.name for trace in self._traces]

    def get_trace(self, trace_ref: Union[str, int]):
        """
        Retrieves the trace with the requested name (trace_ref).

        :param trace_ref: Name of the trace or the index of the trace
        :type trace_ref: str or int
        :return: An object containing the requested trace
        :rtype: DataSet subclass
        :raises IndexError: When a trace is not found
        """
        if isinstance(trace_ref, str):
            for trace in self._traces:
                if trace_ref.upper() == trace.name.upper():  # The trace names are case insensitive
                    # assert isinstance(trace, DataSet)
                    return trace
            raise IndexError(f"{self} doesn't contain trace \"{trace_ref}\"\n"
                             f"Valid traces are {[trc.name for trc in self._traces]}")
        else:
            return self._traces[trace_ref]

    def get_time_axis(self, step=0):
        """
        *(Deprecated)* Use get_axis method instead

        This function is equivalent to get_trace('time').get_time_axis(step) instruction.
        It's workaround on a LTSpice issue when using 2nd Order compression, where some values on
        the time trace have a negative value."""
        return self.get_trace('time').get_time_axis(step)

    def get_axis(self, step: int = 0):
        """
        This function is equivalent to get_trace(0).get_wave(step) instruction.
        It also implements a workaround on a LTSpice issue when using 2nd Order compression, where some values on
        the time trace have a negative value.
        :param step: Step number
        :type step: int
        :returns: Array with the X axis
        :rtype: list[float] or numpy.array
        """
        axis = self.get_trace(0)
        if axis.whattype == 'time':
            return axis.get_time_axis(step)
        else:
            return axis.get_wave(step)

    def _load_step_information(self, filename):
        # Find the extension of the file
        if not filename.endswith(".raw"):
            raise LTSPiceReadException("Invalid Filename. The file should end with '.raw'")
        logfile = filename[:-3] + 'log'
        try:
            encoding = detect_encoding(logfile, "Circuit:")
            log = open(logfile, 'r', errors='replace', encoding=encoding)
        except OSError:
            raise LTSPiceReadException("Step information needs the '.log' file generated by LTSpice")
        except UnicodeError:
            raise LTSPiceReadException("Unable to parse log file and obtain .STEP information. Check Unicode")

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

    def __getitem__(self, item):
        """Helper function to access traces by using the [ ] operator."""
        return self.get_trace(item)

    def get_steps(self, **kwargs):
        """
        Returns the steps that correspond to the query set in the **kwargs parameters.
        Example:

        ::

            raw_read.get_steps(V5=1.2, TEMP=25)

        This will return all steps in which the voltage source V5 was set to 1.2V and the TEMP parameter is 24 degrees.
        This feature is only possible if a .log file with the same name as the .raw file exists in the same directory.
        Note: the correspondence between step numbers and .STEP information is stored on the .log file.

        :key kwargs:

            key-value arguments in which the key correspond to a stepped parameter or source name, and the value is the
            stepped value.

        :return: The steps that match the query
        :rtype: list[int]
        """
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

if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt
    import os
    from os.path import split as pathsplit
    from os.path import join as pathjoin
    from numpy import abs as mag

    def what_to_units(whattype):
        "Determines the unit to display on the plot Y axis"
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
        test_directory = pathjoin(pathsplit(directory)[0], 'test_files')
        filename = 'testfile_5.raw'
        trace_names = ('V(in)', 'V(out)')
        raw_filename = pathjoin(test_directory, filename)

    LTR = RawRead(raw_filename, trace_names, verbose=True)
    for param, value in LTR.raw_params.items():
        print("{}: {}{}".format(param, " "*(20-len(param)), str(value).strip()))

    if trace_names == '*':
        print("Add the traces to plot after the raw file")
        exit(0)
    traces = [LTR.get_trace(trace) for trace in trace_names]
    steps = LTR.get_steps()
    print("Steps read are :", list(steps))
    if 'complex' in LTR.flags:
        n_axis = len(traces) * 2
    else:
        n_axis = len(traces)

    fig, axis_set = plt.subplots(n_axis, 1, sharex='all')
    write_labels = True

    for i, trace in enumerate(traces):
        if 'complex' in LTR.flags:
            axises = axis_set[2*i: 2*i + 2]  # Returns two axis
        else:
            if n_axis == 1:
                axises = [axis_set]  # Needs to return a list
            else:
                axises = axis_set[i:i+1]  # Returns just one axis but enclosed in a list
        magnitude = True
        for ax in axises:
            ax.grid(True)
            if 'log' in LTR.flags:
                ax.set_xscale('log')
            for step in steps:
                x = LTR.get_axis(step)
                y = traces[i].get_wave(step)
                if 'complex' in LTR.flags:
                    x = mag(x)
                    if magnitude:
                        ax.set_yscale('log')
                        y = mag(y)
                    else:
                        y = angle(y, deg=True)
                if write_labels:
                    ax.plot(x, y, label=str(LTR.steps[step]))
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
