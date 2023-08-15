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
# Name:        sim_analysis.py
# Purpose:     Classes to automate Monte-Carlo, FMEA or Worst Case Analysis
#              be updated by user instructions
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     06-07-2021
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

from collections import OrderedDict
from functools import wraps
from typing import Union, Optional

from ...sim.sim_runner import AnyRunner
from ...editor.base_editor import BaseEditor
from ...sim.simulator import Simulator
from ...log.ltsteps import LTSpiceLogReader


class LogFileAnalysis(LTSpiceLogReader):
    """
    This is a subclass of LTSpiceLogReader that is used to analyse the log file of a simulation.
    The super class constructor is bypassed and only their attributes are initialized
    """
    def __init__(self, stepset, dataset, encoding):
        self.stepset = stepset
        self.dataset = dataset
        self.logname = None
        self.encoding = encoding
        self.step_count = len(stepset)
        self.measure_count = len(dataset)

    def plot_histogram(self, param, bins=50, normalized=True, sigma=3.0, title=None, image_file=None, **kwargs):
        """
        Plots a histogram of the parameter
        """
        import numpy as np
        from scipy.stats import norm
        import matplotlib.pyplot as plt

        x = np.array(self.dataset[param], dtype=float)
        mu = x.mean()
        mn = x.min()
        mx = x.max()
        sd = np.std(x)
        sigmin = mu - sigma*sd
        sigmax = mu + sigma*sd

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
            plt.axvspan(mu - sigma*sd, mu + sigma*sd, alpha=0.2, color="cyan")
            plt.ylabel('Distribution [Normalised]')
        else:
            plt.ylabel('Distribution')
        plt.xlabel(param)

        if title is None:
            fmt = '%g'
            title = (r'$\mathrm{Histogram\ of\ %s:}\ \mu='+fmt+r',\ stdev='+fmt+r',\ \sigma=%d$') % (param, mu, sd, sigma)

        plt.title(title)

        plt.axis([axisXmin, axisXmax, 0, axisYmax ])
        plt.grid(True)
        if image_file is not None:
            plt.savefig(image_file)
        else:
            plt.show()


class SimAnalysis(object):
    """
    Base class for making Monte-Carlo, Extreme Value Analysis (EVA) or Failure Mode and Effects Analysis.
    As a base class, a certain number of assertions must be made on the simulation results that will make the pass/fail.

    Note: For the time being only measurements done with .MEAS are possible. At a later stage the parsing of RAW files
    will be possible, although, it seems that the later solution is less computing intense.
    """

    def __init__(self, circuit_file: Union[str, BaseEditor], runner: Optional[AnyRunner] = None):
        if isinstance(circuit_file, str):
            from ...editor.spice_editor import SpiceEditor
            self.editor = SpiceEditor(circuit_file)
        else:
            self.editor = circuit_file
        self._runner = runner
        self.simulations = []
        self.num_runs = 0

    @property
    def runner(self):
        if self._runner is None:
            from ...sim.sim_runner import SimRunner
            self._runner = SimRunner()
        return self._runner

    @runner.setter
    def runner(self, new_runner: AnyRunner):
        self._runner = new_runner

    def run(self, **kwargs):
        """
        Runs the simulations. See runner.run() method for details on keyword arguments.
        """
        sim = self.runner.run(self.editor, **kwargs)
        self.simulations.append(sim)
        self.runner.wait_completion()
        if 'callback' in kwargs:
            return (sim.callback_return if sim is not None else None for sim in self.simulations)

    @wraps(BaseEditor.reset_netlist)
    def reset_netlist(self):
        self.editor.reset_netlist()

    def cleanup_files(self):
        """Clears all simulation files. Typically used after a simulation run and analysis."""
        self.runner.file_cleanup()

    def simulation(self, index: int) -> Simulator:
        """Returns a simulation object"""
        return self.simulations[index]

    def __getitem__(self, item):
        return self.simulations[item]

    def read_logfiles(self) -> LogFileAnalysis:
        """Reads the log files and returns a dictionary with the results"""
        all_stepset = {}
        all_dataset = OrderedDict()
        for sim in self.simulations:
            if sim is None:
                continue
            log_results = LTSpiceLogReader(sim.log_file)
            for param in log_results.stepset:
                if param not in all_stepset:
                    all_stepset[param] = log_results.stepset[param]
                else:
                    all_stepset[param].extend(log_results.stepset[param])
            for param in log_results.dataset:
                if param not in all_dataset:
                    all_dataset[param] = log_results.dataset[param]
                else:
                    all_dataset[param].extend(log_results.dataset[param])
        # Now reusing the last log_results object to store the results
        return LogFileAnalysis(all_stepset, all_dataset, log_results.encoding)

