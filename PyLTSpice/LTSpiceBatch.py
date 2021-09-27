#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
# Name:        LTSpiceBatch.py
# Purpose:     Tool used to launch LTSpice simulation in batch mode. Netlsts can
#              be updated by user instructions
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-12-2016
# Licence:     lGPL v3
# -------------------------------------------------------------------------------
"""
Allows to launch LTSpice simulations from a Python Script, thus allowing to overcome the 3 dimensions STEP limitation on
LTSpice, update resistor values, or component models.

In the code snipped below will simulate a circuit with two different diode models, setting the simulation
temperature to 80 degrees and updates the values of R1 and R2 to 3.3k. ::

    LTC = SimCommander("my_circuit.asc")
    LTC.set_parameters(temp=80)  # Sets the simulation temperature to be 80 degrees
    LTC.set_component_value('R2', '3.3k')  #  Updates the resistor R2 value to be 3.3k
    for dmodel in ("BAT54", "BAT46WJ"):
        LTC.set_element_model("D1", model)  # Sets the Diode D1 model
        for res_value in sweep(2.2, 2,4, 0.2):  # Steps from 2.2 to 2.4 with 0.2 increments
            LTC.set_component_value('R1', res_value)  #  Updates the resistor R1 value to be 3.3k
            LTC.run()

    LTC.wait_completion()  # Waits for the LTSpice simulations to complete

    print("Total Simulations: {}".format(LTC.runno))
    print("Successful Simulations: {}".format(LTC.okSim))
    print("Failed Simulations: {}".format(LTC.failSim))

The first line will create an python class instance that represents the LTSpice file or netlist that is to be
simulated. This object implements methods that are used to manipulate the spice netlist. For example, the method
set_parameters() will set or update existing parameters defined in the netlist. The method set_component_value() is
used to update existing component values or models.

---------------
Multiprocessing
---------------

For making better use of today's computer capabilities, the SimCommander spawns several LTSpice instances
each executing in parallel a simulation.
By default the number of parallel simulations is 4, however the user can override this in two ways. Either
using the class constructor argument ``parallel_sims`` or by forcing the allocation of more processes in the
run() call by setting ``wait_resource=False``. ::

    LTC.run(wait_resource=False)

The recommended way is to set the parameter ``parallel_sims`` in the class constructor. ::

    LTC=SimCommander("my_circuit.asc", parallel_sims=8)

The user then can launch a simulation with the updates done to the netlist by calling the run() method. Since the
processes are not executed right aways, but rather just scheduled for simulation, the wait_completion() function is
needed if the user wants to execute code only after the completion of all scheduled simulations.

The usage of wait_completion() is optional. Just note that the script will only end when all the scheduled tasks are
executed.

---------
Callbacks
---------

As seen above, the `wait_completion()` can be used to wait for all the simulations to be finished. However, this is
not efficient on a multiprocessor point of view. Ideally, the post-processing should be also handled while other
simulations are still running. For this purpose, the user can use a function call backs.

The callback function is called when the simulation has finished direclty by the thread that has handling the
simulation. A function callback receives two arguments.
The RAW file and the LOG file names. Below is an example of a callback function::

    def processing_data(raw_filename, log_filename):
        '''This is a call back function that just prints the filenames'''
        print("Simulation Raw file is %s. The log is %s" % (raw_filename, log_filename)
        # Other code below either using LTSteps.py or LTSpice_RawRead.py
        log_info = LTSpiceLogReader(log_filename)
        log_info.read_measures()
        rise, measures = log_info.dataset["rise_time"]

The callback function is optional. if there no callback function is given then thread is terminated just after the
simulation is finished.
"""
__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2020, Fribourg Switzerland"

from warnings import warn
import subprocess
import threading
import logging
import os
import time
from time import sleep
import sys
import traceback
from typing import Optional, Callable, Union, Any
from PyLTSpice.SpiceEditor import SpiceEditor

__all__ = ('SimCommander', 'cmdline_switches', 'LTspice_exe')

END_LINE_TERM = '\n'

logging.basicConfig(filename='LTSpiceBatch.log', level=logging.INFO)

if sys.platform == "linux":
    LTspice_exe = 'wine C:\\\\Program\\ Files\\\\LTC\\\\LTspiceXVII\\\\XVIIx64.exe'
    LTspice_arg = {'run': ['-b', '-Run']}
elif sys.platform == "darwin":
    LTspice_exe = '/Applications/LTspice.app/Contents/MacOS/LTspice'
    LTspice_arg = {'run': ['-b']}
else:  # Windows
    LTspice_exe = [r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe"]
    LTspice_arg = {'netlist': ['-netlist'], 'run': ['-b', '-Run']}

# Legacy
LTspiceIV_exe = [r"C:\Program Files (x86)\LTC\LTspiceIV\scad3.exe"]

cmdline_switches = []


if sys.version_info.major >= 3 and sys.version_info.minor >= 6:
    clock_function = time.process_time

    def run_function(command, timeout=None):
        result = subprocess.run(command, timeout=timeout)
        return result.returncode
else:
    clock_function = time.clock

    def run_function(command, timeout=None):
        return subprocess.call(command, timeout=timeout)


class RunTask(threading.Thread):
    """This is an internal Class and should not be used directly by the User."""

    def __init__(self, run_no, netlis_file: str, callback: Callable[[str, str], Any], timeout=None, verbose=True):
        self.verbose = verbose
        self.timeout = timeout  # Thanks to Daniel Phili for implemnting this
        
        threading.Thread.__init__(self)
        self.setName("sim%d" % run_no)
        self.run_no = run_no
        self.netlist_file = netlis_file
        self.callback = callback
        self.retcode = -1  # Signals an error by default

    def run(self):
        # Setting up
        logger = logging.getLogger("sim%d" % self.run_no)
        logger.setLevel(logging.INFO)

        # Running the Simulation
        cmd_run = LTspice_exe + LTspice_arg.get('run', '') + [self.netlist_file] + cmdline_switches

        # run the simulation
        self.start_time = clock_function()
        if self.verbose:
            print(time.asctime(), ": Starting simulation %d" % self.run_no)

        # start execution
        self.retcode = run_function(cmd_run, timeout=self.timeout)

        # print simulation time
        sim_time = time.strftime("%H:%M:%S", time.gmtime(clock_function() - self.start_time))

        # Cleanup everything
        if self.retcode == 0:
            # simulation succesfull
            if self.verbose:
                print(time.asctime() + ": Simulation Successful. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))
            if self.callback:
                netlist_radic = self.netlist_file.rstrip('.net')
                raw_file = netlist_radic + '.raw'
                log_file = netlist_radic + '.log'
                if os.path.exists(raw_file) and os.path.exists(log_file):
                    if self.verbose:
                        print("Calling the callback function")
                    try:
                        self.callback(raw_file, log_file)
                    except Exception as err:
                        error = traceback.format_tb(err)
                        logger.error(error)
                else:
                    logger.error("Simulation Raw file or Log file were not found")
            else:
                if self.verbose:
                    print('No Callback')
        else:
            # simulation failed
            logger.warning(time.asctime() + ": Simulation Failed. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))
            netlist_radic = self.netlist_file.rstrip('.net')
            if os.path.exists(netlist_radic + '.log'):
                os.rename(netlist_radic + '.log', netlist_radic + '.fail')


class SimCommander(SpiceEditor):
    """
    The SimCommander class implements all the methods required for launching batches of LTSpice simulations.
    """
    def __init__(self, circuit_file: str, parallel_sims: int = 4, timeout=None, verbose=True, file_id=''):
        """
        Class Constructor. It serves to start batches of simulations.
        See Class documentation for more information.
        """
        self.verbose = verbose
        self.timeout = timeout
        
        circuit_path, filename = os.path.split(circuit_file)

        self.circuit_path = circuit_path
        # self.circuit_file = filename
        fname, ext = os.path.splitext(filename)
        self.circuit_radic = circuit_path + os.path.sep + fname

        self.cmdline_switches = []
        self.parallel_sims = parallel_sims
        self.threads = []

        # master_log_filename = self.circuit_radic + '.masterlog' TODO: create the JSON or YAML file
        self.logger = logging.getLogger("SimCommander")
        self.logger.setLevel(logging.INFO)
        # TODO redirect this logger to a file.

        self.runno = 0  # number of total runs
        self.failSim = 0  # number of failed simulations
        self.okSim = 0  # number of succesfull completed simulations
        # self.failParam = []  # collects for later user investigation of failed parameter sets
        self.netlist = []  # Netlist needs to be created in the __init__ for LINT purposes

        if ext == '.asc':
            self.netlist_file = self.circuit_radic + '.net'
            # prepare instructions, two stages used to enable edits on the netlist w/o open GUI
            # see: https://www.mikrocontroller.net/topic/480647?goto=5965300#5965300
            assert 'netlist' in LTspice_arg, "In this platform LTSpice doesn't have netlist generation capabilities "
            cmd_netlist = LTspice_exe + LTspice_arg.get('netlist') + [circuit_file]

            if self.verbose:
                print("Creating Netlist")
            retcode = run_function(cmd_netlist)
            if retcode == 0:
                if self.verbose:
                    print("The Netlist was successfully created")
                self.reset_netlist()

        else:   # Supposedly it is a net or similar net file
            self.netlist_file = circuit_file
            self.reset_netlist()

        if len(self.netlist) == 0:
            self.logger.error("Unable to create Netlist")

    def __del__(self):
        """Class Destructor : Closes Everything"""
        self.logger.debug("Waiting for all spawned threads to finish.")
        self.wait_completion()  # TODO: Kill all pending simulations
        self.logger.debug("Exiting SimCommander")


    def setLTspiceRunCommand(self, run_command: str) -> None:
        """
        Manually setting the LTSpice run command

        :param path: String containing the command to be invoked to run LTSpice
        :type path: str
        :return: Nothing
        :rtype: None
        """
        global LTspice_exe
        LTspice_exe = run_command


    def add_LTspiceRunCmdLineSwitches(self, *args) -> None:
        """
        Used to add an extra command line argument such as -I<path> to add symbol search path or -FastAccess
        to convert the raw file into Fast Access.
        The arguments is a list of strings as is defined in the LTSpice command line documentation.

        :param args: list of strings
            A list of command line switches such as "-ascii" for generating a raw file in text format or "-alt" for
            setting the solver to alternate. See Command Line Switches information on LTSpice help file.
        :type args: list[str]
        :returns: Nothing
        """
        global cmdline_switches
        cmdline_switches = args

    def run(self, run_filename: str = None, wait_resource: bool = True,
            callback: Callable[[str, str], Any] = None) -> int:
        """
        Executes a simulation run with the conditions set by the user.
        Conditions are set by the set_parameter, set_component_value or add_instruction functions.

        :param run_filename:
            The name of the netlist can be optionally overridden if the user wants to have a better control of how the
            simulations files are generated.
        :type run_filename: str
        :param wait_resource:
            Setting this parameter to False, will force the simulation to start immediately, irrespective of the number
            of simulations already active.
            By default the SimCommander class uses only four processors. This number can then be overridden by setting
            the parameter ´parallel_sims´ to a different number.
            If there are more than ´parallel_sims´ simulations being done, the new one will be placed on hold till one
            of the other simulations are finished.
        :type wait_resource: bool
        :param callback:
            The user can optionally give a callback function for when the simulation finishes, so that a processing can
            be immediately done.
        :type: callback: function(raw_file, log_file)

        :returns: Nothing
        """
        # decide sim required
        if self.netlist is not None:
            # update number of simulation
            self.runno += 1  # Using internal simulation number in case a run_id is not supplied

            # Write the new settings
            if run_filename is None:
                run_netlist_file = "%s_%i.net" % (self.circuit_radic, self.runno)
            else:
                run_netlist_file = run_filename

            self.write_netlist(run_netlist_file)

            while True:
                self.updated_stats()  # purge ended tasks

                if (wait_resource is False) or (len(self.threads) < self.parallel_sims):
                    t = RunTask(self.runno, run_netlist_file, callback,
                                timeout=self.timeout, verbose=self.verbose)
                    self.threads.append(t)
                    t.start()
                    sleep(0.01)  # Give slack for the thread to start
                    break
                sleep(0.1)  # Give Time for other simulations to end

            return self.runno  # Just returns the simulation number

        else:
            # no simulation required
            raise UserWarning('skipping simulation ' + str(self.runno))

    def updated_stats(self):
        """
        This function updates the OK/Fail statistics and releases finished RunTask objects from memory.

        :returns: Nothing
        """
        i = 0
        while i < len(self.threads):
            if self.threads[i].is_alive():
                i += 1
            else:
                if self.threads[i].retcode == 0:
                    self.okSim += 1
                else:
                    # simulation failed
                    self.failSim += 1
                del self.threads[i]

    def wait_completion(self):
        """
        This function will wait for the execution of all scheduled simulations to complete.

        :returns: Nothing
        """
        self.updated_stats()
        while len(self.threads) > 0:
            sleep(1)
            self.updated_stats()


class LTCommander(SimCommander):
    """
    *(Deprecated)*

    Class for launching batch LTSpice simulations. Please use the new SimCommander class instead of LTCommander which
    supports multi-processing.
    """

    def __init__(self, circuit_file: str):
        warn("Deprecated Class. Please use the new SimCommander class instead of LTCommander\n"
             "For more information consult. https://www.nunobrum.com/pyspicer.html", DeprecationWarning)
        SimCommander.__init__(self, circuit_file, 1)


    def write_log(self, text: str):
        mlog = open(self.circuit_radic + '.masterlog', 'a')
        if text.endswith(END_LINE_TERM):
            mlog.write(time.asctime() + ':' + text)
        else:
            mlog.write(time.asctime() + ':' + text + END_LINE_TERM)
        mlog.close()

    def run(self, run_id=None):
        """
        Executes a simulation run with the conditions set by the user. (See also set_parameter, set_component_value,
        add_instruction)
        :param run_id: The run_id parameter can be used to override the naming protocol of the log files.
        :type run_id: int
        :returns: (raw filename, log filename) if simulation is successful else (None, log file name)
        """
        # update number of simulation
        self.runno += 1  # Using internal simulation number in case a run_id is not supplied

        # decide sim required
        if self.netlist is not None:
            # Write the new settings
            run_netlist_file = "%s_%i.net" % (self.circuit_radic, self.runno)
            self.write_netlist(run_netlist_file)
            cmd_run = LTspice_exe + LTspice_arg.get('run') + [run_netlist_file]

            # run the simulation
            start_time = clock_function()
            print(time.asctime(), ": Starting simulation %d" % self.runno)

            # start execution
            retcode = run_function(cmd_run)

            # process the logfile, user can rename it
            netlist_radic = run_netlist_file.rstrip('.net')
            raw_file = netlist_radic + '.raw'
            log_file = netlist_radic + '.log'
            # print simulation time
            sim_time = time.strftime("%H:%M:%S", time.gmtime(clock_function() - start_time))
            # handle simstate
            if retcode == 0:
                # simulation successful
                print(time.asctime() + ": Simulation Successful. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))
                self.write_log("%d%s" % (self.runno, END_LINE_TERM))
                self.okSim += 1
            else:
                # simulation failed
                self.failSim += 1
                # raise exception for try/except construct
                # SRC: https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python
                # raise ValueError(time.asctime() + ': Simulation number ' + str(self.runno) + ' Failed !')
                print(time.asctime() + ": Simulation Failed. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))
                # update failed parameters and counter
                log_file += 'fail'

            if retcode == 0:  # If simulation is successful
                return raw_file, log_file  # Return rawfile and logfile if simulation was OK
            else:
                return None, log_file
        else:
            # no simulation required
            raise UserWarning('skipping simulation ' + str(self.runno))


if __name__ == "__main__":
    # get script absolute path
    meAbsPath = os.path.dirname(os.path.realpath(__file__))
    meAbsPath, _ = os.path.split(meAbsPath)
    # select spice model
    LTC = LTCommander(meAbsPath + "\\test_files\\testfile.asc")
    # set default arguments
    LTC.set_parameters(res=0.001, cap=100e-6)
    # define simulation
    LTC.add_instructions(
        "; Simulation settings",
        # [".STEP PARAM Rmotor LIST 21 28"],
        ".TRAN 3m",
        # ".step param run 1 2 1"
    )
    # do parameter sweep
    for res in range(5):
        # LTC.runs_to_do = range(2)
        LTC.set_parameters(ANA=res)
        raw, log = LTC.run()
        print("Raw file '%s' | Log File '%s'" % (raw, log))
    # Sim Statistics
    print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))


    def callback_function(raw_file, log_file):
        print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))

    LTC = SimCommander(meAbsPath + "\\test_files\\testfile.asc", parallel_sims=1)
    tstart = 0
    for tstop in (2, 5, 8, 10):
        tduration = tstop - tstart
        LTC.add_instruction(".tran {}".format(tduration),)
        if tstart != 0:
            LTC.add_instruction(".loadbias {}".format(bias_file))
            # Put here your parameter modifications
            # LTC.set_parameters(param1=1, param2=2, param3=3)
        bias_file = "sim_loadbias_%d.txt" % tstop
        LTC.add_instruction(".savebias {} internal time={}".format(bias_file, tduration))
        tstart = tstop
        LTC.run(callback=callback_function)
