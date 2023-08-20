#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
# Name:        logfile_data.py
# Purpose:     Store data related to log files. This is a superclass of LTSpiceLogReader
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

import re
from typing import Union, Iterable, List
from collections import OrderedDict
import math
import logging

_logger = logging.getLogger("PyLTSpice.LTSteps")


class LTComplex(object):
    """
    Class to represent complex numbers as exported by LTSpice
    """
    complex_match = re.compile(r"\((?P<mag>[^dB]*)(dB)?,(?P<ph>.*)°\)")

    def __init__(self, strvalue):
        a = self.complex_match.match(strvalue)
        if a:
            self.mag = float(a.group('mag'))
            self.ph = float(a.group('ph'))
            self.unit = 'dB' if len(a.groups()) == 3 else ''
        else:
            raise ValueError("Invalid complex value format")

    def to_complex(self):
        ph = self.ph / 180 * math.pi
        if self.unit == '':
            mag = self.mag
        else:
            mag = 10 ** (self.mag / 20)  # Typically, we are working in voltages

        return complex(mag * math.cos(ph), mag * math.sin(ph))

    def __str__(self):
        return f"{self.mag}{self.unit},{self.ph}°"


def try_convert_value(value: Union[str, int, float]) -> Union[int, float, str]:
    """
    Tries to convert the string into an integer and if it fails, tries to convert to a float, if it fails, then returns the
    value as string.

    :param value: value to convert
    :type value: str, int or float
    :return: converted value, if applicable
    :rtype: int, float, str
    """
    if isinstance(value, (int, float)):
        return value
    try:
        ans = int(value)
    except ValueError:
        try:
            ans = float(value)
        except ValueError:
            try:
                ans = LTComplex(value)
            except ValueError:
                ans = value
    return ans


def try_convert_values(values: Iterable[str]) -> List[Union[int, float, str]]:
    """
    Same as try_convert_values but applicable to an iterable

    :param values: Iterable that returns strings
    :type values:
    :return: list with the values converted to either integer (int) or floating point (float)
    :rtype: List[str]
    """
    answer = []
    for value in values:
        answer.append(try_convert_value(value))
    return answer


class LogfileData:
    """
    This is a subclass of LTSpiceLogReader that is used to analyse the log file of a simulation.
    The super class constructor is bypassed and only their attributes are initialized
    """

    def __init__(self, step_set: dict = None, dataset: dict = None):
        if step_set is None:
            self.stepset = {}
        else:
            self.stepset = step_set.copy()  # A copy is done since the dictionary is a mutable object.
            # Changes in step_set would be propagated to object on the call

        if dataset is None:
            self.dataset = OrderedDict()  # Dictionary in which the order of the keys is kept
        else:
            self.dataset = dataset.copy()  # A copy is done since the dictionary is a mutable object.

        self.step_count = len(self.stepset)
        self.measure_count = len(self.dataset)

    def __getitem__(self, key):
        """
        __getitem__ implements
        :key: step or measurement name
        :return: step or measurement set
        :rtype: List[float]
        """
        if isinstance(key, slice):
            raise NotImplementedError("Slicing in not allowed in this class")
        if key in self.stepset:
            return self.stepset[key]
        if key in self.dataset:
            return self.dataset[key]  # This will raise an Index Error if not found here.
        raise IndexError("'%s' is not a valid step variable or measurement name" % key)

    def steps_with_parameter_equal_to(self, param: str, value: Union[str, int, float]) -> List[int]:
        """
        Returns the steps that contain a given condition.

        :param param: parameter identifier on LTSpice simulation
        :type param: str
        :param value:
        :type value:
        :return: List of positions that respect the condition of equality with parameter value
        :rtype: List[int]
        """
        condition_set = self.stepset[param]
        # tries to convert the value to integer or float, for consistency with data loading implemetation
        v = try_convert_value(value)
        # returns the positions where there is match
        return [i for i, a in enumerate(condition_set) if a == v]

    def steps_with_conditions(self, **conditions) -> List[int]:
        """
        Returns the steps that respect one more more equality conditions

        :key conditions: parameters within the LTSpice simulation. Values are the matches to be found.
        :return: List of steps that repect all the given conditions
        :rtype: List[int]
        """
        current_set = None
        for param, value in conditions.items():
            condition_set = self.steps_with_parameter_equal_to(param, value)
            if current_set is None:
                # initialises the list
                current_set = condition_set
            else:
                # makes the intersection between the lists
                current_set = [v for v in current_set if v in condition_set]
        return current_set

    def get_step_vars(self) -> List[str]:
        """
        Returns the stepped variable names of .
        :return: List of step variables.
        :rtype: list of str
        """
        return self.stepset.keys()

    def get_measure_names(self) -> List[str]:
        """
        Returns the names of the measurements read from the log file.
        :return: List of measurement names.
        :rtype: list of str
        """
        return self.dataset.keys()

    def get_measure_value(self, measure: str, step: int = None) -> Union[float, int, str, LTComplex]:
        """
        Returns a measure value on a given step.

        :param measure: name of the measurement to get
        :type measure: str
        :param step: optional step number if the simulation has no steps.
        :type step: measured value, int, float, Complex or str
        """
        if step is None:
            if len(self.dataset[measure]) == 1:
                return self.dataset[measure][0]
            else:
                raise IndexError("In stepped data, the step number needs to be provided")
        else:
            return self.dataset[measure][step]

    def get_measure_values_at_steps(self, measure: str, steps: Union[None, int, Iterable]) \
            -> List[Union[float, int, str, LTComplex]]:
        """
        Returns the measurements taken at a list of steps provided by the steps list.

        :param measure: name of the measurement to get.
        :type measure: str
        :param steps: step number, or list of step numbers.
        :type steps: Optional: int or list
        :return: measurement or list of measurements
        :rtype: list with the values converted to either integer (int) or floating point (float)
        """
        if steps is None:
            return self.dataset[measure]  # Returns everything
        elif isinstance(steps, int):
            return self.dataset[measure][steps]
        else:  # Assuming it is an iterable
            return [self.dataset[measure][step] for step in steps]

    def max_measure_value(self, measure: str, steps: Union[None, int, Iterable] = None) \
            -> Union[float, int, str]:
        """
        Returns the maximum value of a measurement.

        :param measure: name of the measurement to get
        :type measure: str
        :param steps: step number, or list of step numbers.
        :type steps: Optional, int or list
        :return: maximum value of the measurement
        :rtype: float or int
        """
        return max(self.get_measure_values_at_steps(measure, steps))

    def min_measure_value(self, measure: str, steps: Union[None, int, Iterable] = None) \
            -> Union[float, int, str]:
        """
        Returns the minimum value of a measurement.

        :param measure: name of the measurement to get
        :type measure: str
        :param steps: step number, or list of step numbers.
        :type steps: Optional: int or list
        :return: minimum value of the measurement
        :rtype: float or int
        """
        return min(self.get_measure_values_at_steps(measure, steps))

    def avg_measure_value(self, measure: str, steps: Union[None, int, Iterable] = None) \
            -> Union[float, int, str, LTComplex]:
        """
        Returns the average value of a measurement.

        :param measure: name of the measurement to get
        :type measure: str
        :param steps: step number, or list of step numbers.
        :type steps: Optional: int or list
        :return: average value of the measurement
        :rtype: float or int
        """
        values = self.get_measure_values_at_steps(measure, steps)
        return sum(values) / len(values)

    def split_complex_values_on_datasets(self):
        """
        Internal function to split the complex values into additional two columns
        TODO: Delete the old data and insert new ones the the right position
        """
        for param in list(self.dataset.keys()):
            if len(self.dataset[param]) > 0 and isinstance(self.dataset[param][0], LTComplex):
                self.dataset[param + '_mag'] = [v.mag for v in self.dataset[param]]
                self.dataset[param + '_ph'] = [v.ph for v in self.dataset[param]]

    def export_data(self, export_file: str, encoding=None, append_with_line_prefix=None):
        """
        Exports the measurement information to a tab separated value (.tsv) format. If step data is found, it is
        included in the exported file.

        When using export data together with SpiceBatch.py classes, it may be helpful to append data to an existing
        file. For this purpose, the user can user the append_with_line_prefix argument to indicate that an append should
        be done. And in this case, the user must provide a string that will identify the LTSpice batch run.

        :param export_file: path to the file containing the information
        :type export_file: str
        :param encoding: encoding to be used in the file
        :type encoding: str
        :param append_with_line_prefix: user information to be written in the file in case an append is to be made.
        :type append_with_line_prefix: str
        :return: Nothing
        """
        # print(tokens)
        if append_with_line_prefix is None:
            mode = 'w'  # rewrites the file
        else:
            mode = 'a'  # Appends an existing file

        if len(self.dataset) == 0:
            _logger.warning("Empty data set. Exiting without writing file.")
            return

        if encoding is None:
            encoding = self.encoding if hasattr(self, 'encoding') else 'utf-8'

        fout = open(export_file, mode, encoding=encoding)

        if append_with_line_prefix is not None:  # if appending a file, it must write the column title
            fout.write('user info\t')

        fout.write("step\t%s\t%s\n" % ("\t".join(self.stepset.keys()), "\t".join(self.dataset)))
        first_parameter = next(iter(self.dataset))
        for index in range(len(self.dataset[first_parameter])):
            if self.step_count == 0:
                step_data = []  # Empty step
            else:
                step_data = [self.stepset[param][index] for param in self.stepset.keys()]
            meas_data = [self.dataset[param][index] for param in self.dataset]

            if append_with_line_prefix is not None:  # if appending a file it must write the user info
                fout.write(append_with_line_prefix + '\t')
            fout.write("%d" % (index + 1))
            for s in step_data:
                fout.write(f'\t{s}')

            for tok in meas_data:
                if isinstance(tok, list):
                    for x in tok:
                        fout.write(f'\t{x}')
                else:
                    fout.write(f'\t{tok}')
            fout.write('\n')

        fout.close()

    def plot_histogram(self, param, steps: Union[None, int, Iterable] = None, bins=50, normalized=True, sigma=3.0, title=None, image_file=None, **kwargs):
        """
        Plots a histogram of the parameter
        """
        import numpy as np
        from scipy.stats import norm
        import matplotlib.pyplot as plt
        values = self.get_measure_values_at_steps(param, steps)
        x = np.array(values, dtype=float)
        mu = x.mean()
        mn = x.min()
        mx = x.max()
        sd = np.std(x)

        # Automatic calculation of the range
        axisXmin = mu - (sigma + 1) * sd
        axisXmax = mu + (sigma + 1) * sd

        if mn < axisXmin:
            axisXmin = mn

        if mx > axisXmax:
            axisXmax = mx

        n, bins, patches = plt.hist(x, bins, density=normalized, facecolor='green', alpha=0.75,
                                    range=(axisXmin, axisXmax))
        axisYmax = n.max() * 1.1

        if normalized:
            # add a 'best fit' line
            y = norm.pdf(bins, mu, sd)
            l = plt.plot(bins, y, 'r--', linewidth=1)
            plt.axvspan(mu - sigma * sd, mu + sigma * sd, alpha=0.2, color="cyan")
            plt.ylabel('Distribution [Normalised]')
        else:
            plt.ylabel('Distribution')
        plt.xlabel(param)

        if title is None:
            fmt = '%g'
            title = (r'$\mathrm{Histogram\ of\ %s:}\ \mu=' + fmt + r',\ stdev=' + fmt + r',\ \sigma=%d$') % (
                param, mu, sd, sigma)

        plt.title(title)

        plt.axis([axisXmin, axisXmax, 0, axisYmax])
        plt.grid(True)
        if image_file is not None:
            plt.savefig(image_file)
        else:
            plt.show()
