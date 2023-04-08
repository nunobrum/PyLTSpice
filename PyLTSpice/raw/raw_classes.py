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
# Name:        raw_classes.py
# Purpose:     Implements helper classes that contain
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     19-06-2022
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

import numpy as np
from numpy import zeros, complex128, float32, float64
from binascii import b2a_hex
from typing import Union, List


class DataSet(object):
    """
    This is the base class for storing all traces inside of a RAW file. Returned by the get_trace() or by the get_axis()
    methods.
    Normally the user doesn't have to be aware of this class. It is only used internally to encapsulate the different
    implementations of the wave population.
    Data can be retrieved directly by using the [] operator.
    If numpy is available, the numpy vector can be retrieved by using the get_wave() method.
    The parameter whattype defines what is the trace representing in the simulation, Voltage, Current a Time or
    Frequency.
    """

    def __init__(self, name, whattype, datalen, numerical_type='real'):
        """Base Class for both Axis and Trace Classes.
        Defines the common operations between both."""
        self.name = name
        self.whattype = whattype
        self.numerical_type = numerical_type
        if numerical_type == 'double':
            self.data = zeros(datalen, dtype=float64)
        elif numerical_type == 'real':
            self.data = zeros(datalen, dtype=float32)
        elif numerical_type == 'complex':
            self.data = zeros(datalen, dtype=complex128)
        else:
            raise NotImplementedError

    def __str__(self):
        if isinstance(self.data[0], float):
            # data = ["%e" % value for value in self.data]
            return "name:'%s'\ntype:'%s'\nlen:%d\n%s" % (self.name, self.whattype, len(self.data), str(self.data))
        elif isinstance(self.data[0], complex):
            return "name: {}\ntype: {}\nlen: {:d}\n{}".format(self.name, self.whattype, len(self.data), str(self.data))
        else:
            data = [b2a_hex(value) for value in self.data]
            return "name:'%s'\ntype:'%s'\nlen:%d\n%s" % (self.name, self.whattype, len(self.data), str(data))

    def __len__(self):
        return len(self.data)

    def get_wave(self):
        """
        :return: Internal data array
        :rtype: list or numpy.array
        """
        return self.data


class Axis(DataSet):
    """This class is used to represent the horizontal axis like on a Transient or DC Sweep Simulation. It derives from
    the DataSet and defines additional methods that are specific for X axis.
    This class is constructed by the get_time_axis() method or by a get_trace(0) command. In RAW files the trace 0 is
    always the X Axis. Ex: time for .TRAN simulations and frequency for the .AC simulations.

    To access data inside this class, the get_wave() should be used, which implements the support for the STEPed data.
    IF Numpy is available, get_wave() will return a numpy array.

    In Transient Analysis and in DC transfer characteristic, LTSpice uses doubles to store the axis values.
    """

    def __init__(self, name: str, whattype: str, datalen: int, numerical_type: str = 'double'):
        super().__init__(name, whattype, datalen, numerical_type)
        self.step_info = None

    def _set_steps(self, step_info: List[dict]):
        self.step_info = step_info

        self.step_offsets = [None for _ in range(len(step_info))]

        # Now going to calculate the point offset for each step
        self.step_offsets[0] = 0
        i = 1
        k = 1
        while i < len(self.data):
            if self.data[i] == self.data[0]:
                # print(k, i, self.data[i], self.data[i+1])
                self.step_offsets[k] = i
                k += 1
            i += 1

        if k != len(self.step_info):
            raise SpiceReadException("The file a different number of steps than expected.\n" +
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

    def get_wave(self, step: int = 0):
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
        assert self.name == 'time', \
            "This function is only applicable to transient analysis, where a bug exists on the time signal"
        return np.abs(self.get_wave(step))

    def get_point(self, n, step: int = 0):
        """
        Get a point from the dataset
        :param n: position on the vector
        :type n:int
        :param step: step index
        :type step: int
        :returns: Value of the data point
        :rtype: float or complex
        """
        return self.data[n + self.step_offset(step)]

    def __getitem__(self, item):
        """This is only here for compatibility with previous code. """
        assert self.step_info is None, "Indexing should not be used with stepped data. Use get_point"
        return self.data.__getitem__(item)

    def get_position(self, t, step: int = 0) -> Union[int, float]:
        """
        Returns the position of a point in the axis. If the point doesn't exist, an interpolation is done between the
        two closest points.
        For example, if the point requested is 1.0001ms and the closest points that exist in the axis are t[100]=1ms and
        t[101]=1.001ms, then the return value will be 100 + (1.0001ms-1ms)/(1.001ms-1ms) = 100.1

        :param t: point in axis to search for
        :type t: float
        :param step: step number
        :type step: int
        :returns: The position of parameter /t/ in the axis
        :rtype: int, float
        """
        if self.name == 'time':
            timex = self.get_time_axis(step)
        else:
            timex = self.get_wave(step)
        for i, x in enumerate(timex):
            if x == t:
                return i
            elif x > t:
                # Needs to interpolate the data
                if i == 0:
                    raise IndexError("Time position is lower than t0")
                frac = (t - timex[i-1])/(timex[i] - timex[i-1])
                return i - 1 + frac

    def get_len(self, step: int = 0) -> int:
        """
        Returns the length of the axis.
        :param step: Optional parameter the step index.
        :type step: int
        :return: The number of data points
        :rtype: int
        """
        return self.step_offset(step + 1) - self.step_offset(step)

    def __len__(self):
        if self.step_info is None:
            return len(self.data)
        else:
            return self.get_len()


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
        Implementation of the [] operator.

        :param n: item in the array
        :type n: int
        :param step: Optional step number
        :type step: int
        :return: float value of the item
        :rtype: float
        """
        if self.axis is None:
            if n != 0:
                return self.data[n]
            else:
                return self.data[step]  # This is for the case of stepped operation point simulation.
        else:
            return self.data[self.axis.step_offset(step) + n]

    def __getitem__(self, item):
        """This is only here for compatibility with previous code. """
        assert self.axis is None or self.axis.step_info is None, \
            "Indexing should not be used with stepped data. Use get_point() method"
        return self.data.__getitem__(item)

    def get_wave(self, step: int = 0):
        """
        Returns the data contained in this object. For stepped simulations an argument must be passed specifying the
        step number. If no steps exist, the argument must be left blank.
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

    def get_point_at(self, t, step: int = 0):
        """
        Get a point from the trace at the point specified by the /t/ argument.
        If the point doesn't exist on the axis, the data is interpolated using a linear regression between the two
        adjacent points.
        :param t: point in the axis where to find the point.
        :type t: float, float32(numpy) or float64(numpy)
        :param step: step index
        :type step: int
        """
        pos = self.axis.get_position(t, step)
        if isinstance(pos, (float, float32, float64)):
            offset = self.axis.step_offset(step)
            i = int(pos)
            last_item = self.get_len(step) - 1
            if i < last_item:
                f = pos - i
                return self.data[offset + i] + f * (self.data[offset + i + 1] - self.data[offset + i])
            elif pos == last_item:  # This covers the case where a float is given containing the last position
                return self.data[offset + i]
            else:
                raise IndexError(f"The highest index is {last_item}. Received {pos}")
        else:
            return self.get_point(pos, step)

    def get_len(self, step: int = 0) -> int:
        """
        Returns the length of the axis.
        :param step: Optional parameter the step index.
        :type step: int
        :return: The number of data points
        :rtype: int
        """
        return self.axis.step_offset(step + 1)

    def __len__(self):
        """This is only here for compatibility with previous code. """
        assert self.axis is None or self.axis.step_info is None, \
            "len() should not be used with stepped data. Use get_len() method passing the step index"
        return len(self.data)


class DummyTrace(object):
    """Dummy Trace for bypassing traces while reading"""

    def __init__(self, name, whattype):
        """Base Class for both Axis and Trace Classes.
        Defines the common operations between both."""
        self.name = name
        self.whattype = whattype


class SpiceReadException(Exception):
    """Custom class for exception handling"""
    ...
