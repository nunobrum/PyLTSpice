#!/usr/bin/env python

"""LTSpice_RawRead.py : A pure python implementation of an LTSpice RAW file reader.
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

__author__ = "Nuno Canto Brum <me@nunobrum.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"


from binascii import b2a_hex

try:
    from numpy import zeros, array
except ImportError:
    USE_NNUMPY = False
else:
    USE_NNUMPY = True
    print("Found Numpy. WIll be used for storing data")

class DataSet(object):
    """Class for storing Traces."""

    def __init__(self, name, datatype, datalen):
        """Base Class for both Axis and Trace Classes.
        Defines the common operations between both."""
        self.name = name
        self.type = datatype
        if USE_NNUMPY:
            self.data = zeros(datalen)
        else:
            self.data = [None for x in range(datalen)]


    def set_pointA(self, n, value):
        """function to be used on ASCII RAW Files.

        :param n:     the point to set
        :param value: the Value of the point being set."""
        assert isinstance(value, float)
        self.data[n] = value

    def set_pointB(self, n, value):
        """Function that converts a normal trace into float on a Binary storage. This codification uses 4 bytes.
        The codification is done as follows:
               7   6   5   4     3   2   1   0
        Byte3  SGM SGE E6  E5    E4  E3  E2  E1         SGM - Signal of Mantissa: 0 - Positive 1 - Negative
        Byte2  E0  M22 M21 M20   M19 M18 M17 M16        SGE - Signal of Exponent: 0 - Positive 1 - Negative
        Byte1  M15 M14 M13 M12   M11 M10 M9  M8         E[6:0] - Exponent
        Byte0  M7  M6  M5  M4    M3  M2  M1  M0         M[22:0] - Mantissa.

        :param n:     the point to set
        :param value: the Value of the point being set."""

        if value[3] & 0x80 == 0:
            sign = 1
        else:
            sign = -1

        exp = (value[3] & 0x3F) * 2
        exp += (value[2] >> 7)

        if value[3] & 0x40 == 0:
            exp -= 128

        mts = ((value[2] & 0x7F) / 64.0) + (value[1] / 16384.0) + (value[0] / 4194304.0)
        if mts == 0 and exp == -128:
            self.data[n] = 0.0
        else:
            self.data[n] = sign * (2 + mts) * (2 ** exp)

            # print(b2a_hex(value), self.data[n])

    def __str__(self):
        if isinstance(self.data[0], float):
            # data = ["%e" % value for value in self.data]
            return "name:'%s'\ntype:'%s'\nlen:%d\n%s" % (self.name, self.type, len(self.data), str(self.data))
        else:
            data = [b2a_hex(value) for value in self.data]
            return "name:'%s'\ntype:'%s'\nlen:%d\n%s" % (self.name, self.type, len(self.data), str(data))

    def get_point(self, n):
        return self.data[n]

    def get_wave(self):
        return self.data


class Axis(DataSet):
    """This class is used to represent the horizontal axis like on a Transient or DC Sweep Simulation."""
    def __init__(self, name, datatype, datalen):
        super().__init__(name, datatype, datalen)
        self.step_info = None


    def set_pointB(self, n, value):
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
        if value[7] & 0x80 == 0:
            sign = 1
        else:
            sign = -1

        exp = (value[7] & 0x3F) * 16
        exp += (value[6] >> 4)

        if value[7] & 0x40 == 0:
            exp -= 1024

        mts = (((value[6] & 0x0F) / 8.0) + (value[5] / 2048.0) +
               (value[4] / 524288.0) + (value[3] / 134217728.0) +
               (value[2] / 34359738368.0) + (value[1] / 8796093022208.0) + (value[0] / 2.25179981368525E15))

        if (mts == 0) and exp == -1024:
            self.data[n] = 0.0
        else:
            self.data[n] = sign * (2 + mts) * (2 ** exp)
            # print (b2a_hex(value), self.data[n])

    def _set_steps(self, step_info):
        self.step_info = step_info

        if USE_NNUMPY:
            self.step_offsets = zeros(len(step_info))
        else:
            self.step_offsets = [None for x in range(len(step_info))]

        # Now going to calculate the point offset for each step
        self.step_offsets[0] = 0
        i = 0
        k = 0
        while i < len(self.data):
            if self.data[i] == self.data[0]:
                print(k, i, self.data[i], self.data[i+1])
                self.step_offsets[k] = i
                i += 1 # Needs to add one here because the data will be repeated
                k += 1
            i += 1

        if k != len(self.step_info):
            raise LTSPiceReadException("The file a different number of steps than expected.\n" +
                                       "Expecting %d got %d" % (len(self.step_offsets), k))

    def step_offset(self, step):
        if self.step_info == None:
            return 0
        else:
            if step >= len(self.step_offsets):
                return len(self.data)
            else:
                return self.step_offsets[step]

    def get_wave(self, step=0):
        return self.data[self.step_offset(step):self.step_offset(step + 1)]



class Trace(DataSet):
    """Class used for storing generic traces that report to a given Axis."""

    def __init__(self, name, datatype, datalen, axis):
        super().__init__(name, datatype, datalen)
        self.axis = axis

    def get_point(self, n, step=0):
        if self.axis is None:
            return super().get_point(n)
        else:
            return self.data[self.axis.step_offset(step) + n]

    def get_wave(self, step=0):
        if self.axis is None:
            return super().get_wave()
        else:
            return self.data[self.axis.step_offset(step):self.axis.step_offset(step + 1)]


class DummyTrace(object):
    """Dummy Trace for bypassing traces while reading"""
    def __init__(self, name, datatype):
        """Base Class for both Axis and Trace Classes.
        Defines the common operations between both."""
        self.name = name
        self.type = datatype

    def set_pointA(self, n, value):
        pass

    def set_pointB(self, n, value):
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
        "Flags",
        "No. Variables",
        "No. Points",
        "Offset",
        "Command",
        "Variables",
        "Backannotation"
    ]

    def __init__(self, raw_filename, traces_to_read="*", **kwargs):
        """The arguments for this class are:
    raw_filename   - The file containing the RAW data to be read
    traces_to_read - A string containing the list of traces to be read. If None is provided, only the header is read
                     and all trace data is discarded. If a '*' wildcard is given, all traces are read.
    """
        assert isinstance(raw_filename, str)
        if not traces_to_read is None:
            assert isinstance(traces_to_read, str)

        raw_file = open(raw_filename, "rb")

        # Storing the filename as part of the dictionary
        self.raw_params = {"Filename": raw_filename}

        line = raw_file.readline().decode()
        while line:
            for tag in self.header_lines:
                if line.startswith(tag):
                    self.raw_params[tag] = line[len(tag) + 1:-1]  # Adding 1 to account with the colon after the tag
                    # print(ftag)
                    break
            else:
                raw_file.close()
                raise LTSPiceReadException(("Error reading Raw File !\n " +
                                            "Unrecognized tag in line %s") % (line))

            line = raw_file.readline().decode()
            if line.startswith("Variables"):
                break
        else:
            raw_file.close()
            raise LTSPiceReadException("Error reading Raw File !\n " +
                                       "Unexpected end of file")

        if not ("real" in self.raw_params["Flags"]):
            # Not Supported, an exception will be raised
            raw_file.close()
            raise LTSPiceReadException("The LTSpiceRead class doesn't support non real data")

        self.nPoints = int(self.raw_params["No. Points"], 10)
        self.nVariables = int(self.raw_params["No. Variables"], 10)
        self._traces = []
        self.steps = None
        self.axis = None # Creating the axis
        # print("Reading Variables")

        for ivar in range(self.nVariables):
            line = raw_file.readline().decode()[:-1]
            # print(line)
            dummy, n, name, var_type = line.split("\t")
            if ivar == 0 and self.nVariables > 1:
                self.axis = Axis(name, var_type, self.nPoints)
                self._traces.append(self.axis)
            elif ((traces_to_read == "*") or
                    (name in traces_to_read) or
                    (ivar == 0)):
                # TODO: Add wildcards to the waveform matching
                self._traces.append(Trace(name, var_type, self.nPoints, self.axis))
            else:
                self._traces.append(DummyTrace(name, var_type))

        if traces_to_read is None or len(self._traces) == 0:
            # The read is stopped here if there is nothing to read.
            raw_file.close()
            return

        if kwargs.get("headeronly", False):
            return

        raw_type = raw_file.readline().decode()

        if raw_type.startswith("Binary:"):
            # Will start the reading of binary values
            if "fastaccess" in self.raw_params["Flags"]:
                # A fast access means that the traces are grouped together.
                first_var = True
                for var in self._traces:
                    if first_var:
                        first_var = False
                        for point in range(self.nPoints):
                            value = raw_file.read(8)
                            var.set_pointB(point, value)
                    else:
                        if isinstance(var, DummyTrace):
                            #TODO: replace this by a seek
                            raw_file.read(self.nPoints*4)
                        else:
                            for point in range(self.nPoints):
                                value = raw_file.read(4)
                            var.set_pointB(point, value)
            else:
                # This is the default save after a simulation where the traces are scattered
                for point in range(self.nPoints):
                    first_var = True
                    for var in self._traces:
                        if first_var:
                            first_var = False
                            value = raw_file.read(8)
                            var.set_pointB(point, value)
                        else:
                            value = raw_file.read(4)
                            var.set_pointB(point, value)

        elif raw_type.startswith("Values:"):
            # Will start the reading of ASCII Values
            for point in range(self.nPoints):
                first_var = True
                for var in self._traces:
                    line = raw_file.readline().decode()
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
            raise LTSPiceReadException("Unsupported RAW File. ""%s""" % raw_type)

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
                   #assert isinstance(trace, DataSet)
                    return trace
            return None
        else:
            return self._traces[trace_ref]

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

    def get_steps(self):
        if self.steps is None:
            return ["No Step"]
        else:
            return self.steps


if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt

    if len(sys.argv) > 1:
        raw_filename = sys.argv[1]
    else:
        raw_filename = "CSL2_kevin_Test.raw"
        # raw_filename = "teste.raw"

    LTR = LTSpiceRawRead(raw_filename,'V(out)')

    print(LTR.get_trace_names())
    # for trace in LTR.get_trace_names():
    #     print(LTR.get_trace(trace))

    print(LTR.get_raw_property())

    y = LTR.get_trace('V(out)')
    x = LTR.get_trace(0)  # Zero is always the X axis
    steps = LTR.get_steps()
    for step in range(len(steps)):
        # print(steps[step])
        plt.plot(x.get_wave(step), y.get_wave(step), label=steps[step])

    plt.legend() # order a legend.
    plt.show()



    # out = open("RAW_TEST_out_test1.txt", 'w')
    #
    # for step in LTR.get_steps():
    #     for x in range(len(LTR[0].data)):
    #         out.write("%s, %e, %e\n" % (step, LTR[0].data[x], LTR[2].data[x]))
    # out.close()
