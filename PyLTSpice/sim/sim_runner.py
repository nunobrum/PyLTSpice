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
# Name:        sim_batch.py
# Purpose:     Tool used to launch LTSpice simulation in batch mode. Netlsts can
#              be updated by user instructions
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-12-2016
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
"""
Allows launching LTSpice simulations from a Python Script, thus allowing to overcome the 3 dimensions STEP limitation on
LTSpice, update resistor values, or component models.

The code snipped below will simulate a circuit with two different diode models, set the simulation
temperature to 80 degrees, and update the values of R1 and R2 to 3.3k. ::

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

By default, the number of parallel simulations is 4, however the user can override this in two ways. Either
using the class constructor argument ``parallel_sims`` or by forcing the allocation of more processes in the
run() call by setting ``wait_resource=False``. ::

    LTC.run(wait_resource=False)

The recommended way is to set the parameter ``parallel_sims`` in the class constructor. ::

    LTC=SimCommander("my_circuit.asc", parallel_sims=8)

The user then can launch a simulation with the updates done to the netlist by calling the run() method. Since the
processes are not executed right away, but rather just scheduled for simulation, the wait_completion() function is
needed if the user wants to execute code only after the completion of all scheduled simulations.

The usage of wait_completion() is optional. Just note that the script will only end when all the scheduled tasks are
executed.

---------
Callbacks
---------

As seen above, the `wait_completion()` can be used to wait for all the simulations to be finished. However, this is
not efficient from a multiprocessor point of view. Ideally, the post-processing should be also handled while other
simulations are still running. For this purpose, the user can use a function call back.

The callback function is called when the simulation has finished directly by the thread that has handling the
simulation. A function callback receives two arguments.
The RAW file and the LOG file names. Below is an example of a callback function::

    def processing_data(raw_filename, log_filename):
        '''This is a call back function that just prints the filenames'''
        print("Simulation Raw file is %s. The log is %s" % (raw_filename, log_filename)
        # Other code below either using LTSteps.py or raw_read.py
        log_info = LTSpiceLogReader(log_filename)
        log_info.read_measures()
        rise, measures = log_info.dataset["rise_time"]

The callback function is optional. If  no callback function is given, the thread is terminated just after the
simulation is finished.
"""
__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2020, Fribourg Switzerland"

import logging
import os
import shutil
from pathlib import Path, PurePath
import threading
import time
import traceback
from time import sleep
from typing import Callable, Union, Any, Tuple
from warnings import warn

from ..sim.local_run_task import RunTask
from ..sim.spice_editor import SpiceEditor
from ..sim.simulator import clock_function, Simulator

END_LINE_TERM = '\n'

logging.basicConfig(filename='SpiceBatch.log', level=logging.INFO)


class SimRunner(object):
    """
    The SimCommander class implements all the methods required for launching batches of LTSpice simulations.
    It takes a parameter the path to the LTSpice .asc file to be simulated, or directly the .net file.
    If an .asc file is given, the class will try to generate the respective .net file by calling LTspice with
    the --netlist option
    :raises FileNotFoundError: When the file is not found  /!\ This will be changed

    :param parallel_sims: Defines the number of parallel simulations that can be executed at the same time. Ideally this
                          number should be aligned to the number of CPUs (processor cores) available on the machine.
    :type parallel_sims: int, optional
    :param timeout: Timeout parameter as specified on the os subprocess.run() function
    :type timeout: float, optional
    :param verbose: If True, it enables a richer printout of the program execution.
    :type verbose: bool, optional
    :param encoding: Forcing the encoding to be used on the circuit netlile read. Defaults to 'autodetect' which will
                     call a function that tries to detect the encoding automatically. This however is not 100% fool
                     proof.
    :type encoding: str, optional
    :param output_folder: specifying which directory shall be used for simulation files (raw and log files).
    :param output_folder: str
    :param simulator: Forcing a given simulator executable.
    :type simulator: str or Simulator, optional

    """

    def __init__(self, parallel_sims: int = 4, timeout=None, verbose=True, output_folder: str = None, simulator=None):
        """
        Class Constructor. It serves to start batches of simulations.
        See Class documentation for more information.
        """
        self.workfiles = []
        self.verbose = verbose
        self.timeout = timeout

        if output_folder:
            self.output_folder = Path(output_folder)  # If not None convert to Path() object
            if not self.output_folder.exists():
                self.output_folder.mkdir()
        else:
            self.output_folder = None

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

        # Gets a simulator.
        if simulator is None:
            self.simulator = Simulator.get_default_simulator()
        elif isinstance(simulator, Simulator):
            self.simulator = simulator
        elif isinstance(simulator, (str, Path)):
            self.simulator = Simulator.create_from(simulator)
        else:
            raise TypeError("Invalid simulator type. Either use a string with the ")

    def __del__(self):
        """Class Destructor : Closes Everything"""
        self.logger.debug("Waiting for all spawned threads to finish.")
        self.wait_completion()  # TODO: Kill all pending simulations
        self.logger.debug("Exiting SimCommander")

    def setRunCommand(self, spice_tool: Union[str, Simulator]) -> None:
        """
        Manually setting the LTSpice run command

        :param spice_tool: String containing the path to the spice tool to be used, or alternatively the Simulator
        object.
        :type spice_tool: str or Simulator
        :return: Nothing
        :rtype: None
        """
        if isinstance(spice_tool, str):
            self.simulator = Simulator.create_from(spice_tool)
        elif isinstance(spice_tool, Simulator):
            self.simulator = spice_tool
        else:
            raise TypeError("Expecting str or Simulator objects")

    def addRunCmdLineSwitches(self, *args) -> None:
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
        self.simulator.add_command_line_switch(*args)

    def _on_output_folder(self, afile):
        if self.output_folder:
            return self.output_folder / afile
        else:
            return PurePath(afile)

    def _to_output_folder(self, afile: Path, *, copy: bool, new_name: str = ''):
        if self.output_folder:
            if new_name:
                ddst = self.output_folder / new_name
            else:
                ddst = self.output_folder

            if copy:
                dest = shutil.copy(afile, ddst)
            else:
                dest = shutil.move(afile, ddst)
            return Path(dest)
        else:
            return afile

    def _run_file_name(self, netlist):
        if not isinstance(netlist, Path):
            netlist = Path(netlist)
        return "%s_%i.net" % (netlist.stem, self.runno)

    def create_netlist(self, asc_file: Union[str, Path]):
        if not isinstance(asc_file, Path):
            asc_file = Path(asc_file)
        if asc_file.suffix == '.asc':
            netlist_file = asc_file.with_suffix('.net')
            if self.verbose:
                print("Creating Netlist")
            retcode = self.simulator.create_netlist(netlist_file)
            if retcode == 0 and netlist_file.exists():
                if self.verbose:
                    print("The Netlist was successfully created")
                netlist_file = self._to_output_folder(netlist_file, copy=False)
                self.workfiles.append(netlist_file)
                return netlist_file
            else:
                self.logger.error("Unable to create Netlist")
                if self.verbose:
                    print("Unable to create the Netlist from %s" % asc_file)
        return None

    def run(self, netlist: Union[str, Path, SpiceEditor], *,  wait_resource: bool = True,
            callback: Callable[[str, str], Any] = None, timeout: float = 600, run_filename: str = None) -> RunTask:
        """
        Executes a simulation run with the conditions set by the user.
        Conditions are set by the set_parameter, set_component_value or add_instruction functions.

        :param netlist:
            The name of the netlist can be optionally overridden if the user wants to have a better control of how the
            simulations files are generated.
        :type netlist: SpiceEditor or a path to the file
        :param wait_resource:
            Setting this parameter to False will force the simulation to start immediately, irrespective of the number
            of simulations already active.
            By default the SimCommander class uses only four processors. This number can be overridden by setting
            the parameter ´parallel_sims´ to a different number.
            If there are more than ´parallel_sims´ simulations being done, the new one will be placed on hold till one
            of the other simulations are finished.
        :type wait_resource: bool, optional
        :param callback:
            The user can optionally give a callback function for when the simulation finishes so that processing can
            be done immediately.
        :type: callback: function(raw_file, log_file), optional
        :param timeout: Timeout to be used in waiting for resources. Default time is 600 seconds, i.e. 10 minutes.
        :type timeout: float, optional
        :param run_filename: Name to be used for the log and raw file.
        :type run_filename: str or Path
        :returns: The task object of type RunTask
        """
        # update number of simulation
        self.runno += 1  # Using internal simulation number in case a run_id is not supplied
        # Harmonize the netlist into a Path object pointing to a netlist file on the right output folder
        if isinstance(netlist, SpiceEditor):
            if run_filename is None:
                run_filename = self._run_file_name(netlist.netlist_file)

            # Calculates the path where to store the new netlist.
            run_netlist_file = self._on_output_folder(run_filename).with_suffix('.net')
            netlist.write_netlist(run_netlist_file)

        elif isinstance(netlist, (Path, str)):
            if run_filename is None:
                run_filename = self._run_file_name(netlist)
            run_netlist_file = self._to_output_folder(netlist, copy=True, new_name=run_filename)
        else:
            raise TypeError("'netlist' parameter shall be a SpiceEditor, pathlib.Path or a plain str")

        self.workfiles.append(run_netlist_file)

        t0 = time.perf_counter()  # Store the time for timeout calculation
        while time.perf_counter() - t0 < timeout:
            self.updated_stats()  # purge ended tasks

            if (wait_resource is False) or (len(self.threads) < self.parallel_sims):
                t = RunTask(self.simulator, self.runno, run_netlist_file, callback,
                            timeout=self.timeout, verbose=self.verbose)
                self.threads.append(t)
                t.start()
                sleep(0.01)  # Give slack for the thread to start
                return t  # Returns the task number
            sleep(0.1)  # Give Time for other simulations to end
        else:
            self.logger.error("Timeout waiting for resources for simulation %d" % self.runno)
            if self.verbose:
                print("Timeout on launching simulation %d." % self.runno)

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

    @staticmethod
    def kill_all_ltspice():
        """Function to terminate LTSpice in windows"""
        simulator = Simulator.get_default_simulator()
        simulator.kill_all()

    def wait_completion(self, timeout=None, abort_all_on_timeout=False) -> bool:
        """
        This function will wait for the execution of all scheduled simulations to complete.

        :param timeout: Cancels the wait after the number of seconds specified by the timeout.
            This timeout is reset everytime that a simulation is completed. The difference between this timeout and the
            one defined in the SimCommander instance, is that the later is implemented by the subprocess class, and the
            this timeout just cancels the wait.
        :type timeout: int
        :param abort_all_on_timeout: attempts to stop all LTSpice processes if timeout is expired.
        :type abort_all_on_timeout: bool
        :returns: True if all simulations were executed successfully
        :rtype: bool
        """
        self.updated_stats()
        timeout_counter = 0
        sim_counters = (self.okSim, self.failSim)

        while len(self.threads) > 0:
            sleep(1)
            self.updated_stats()
            if timeout is not None:
                if sim_counters == (self.okSim, self.failSim):
                    timeout_counter += 1
                    print(timeout_counter, "timeout counter")
                else:
                    timeout_counter = 0

                if timeout_counter > timeout:
                    if abort_all_on_timeout:
                        self.kill_all_ltspice()
                    return False

        return self.failSim == 0

    def file_cleanup(self):
        """
        Will delete all log and raw files that were created by the script. This should only be executed at the end
        of data processing.
        """
        while len(self.workfiles):
            workfile = self.workfiles.pop(0)
            if workfile.suffix == '.net':
                # Delete the log file if exists
                logfile = workfile.with_suffix('.log')
                if logfile.exists():
                    print("Deleting", logfile)
                    logfile.unlink()
                # Delete the raw file if exists
                rawfile = workfile.with_suffix('.raw')
                if rawfile.exists():
                    print("Deleting", rawfile)
                    rawfile.unlink()

                # Delete the op.raw file if exists
                oprawfile = workfile.with_suffix('.op.raw')
                if oprawfile.exists():
                    print("Deleting", oprawfile)
                    oprawfile.unlink()

            # Delete the file
            print("Deleting", workfile)
            workfile.unlink()


if __name__ == "__main__":
    # get script absolute path
    meAbsPath = os.path.dirname(os.path.realpath(__file__))
    meAbsPath, _ = os.path.split(meAbsPath)
    # select spice model
    netlist = SpiceEditor(meAbsPath + "\\test_files\\testfile.asc")
    # set default arguments
    netlist.set_parameters(res=0.001, cap=100e-6)
    # define simulation
    netlist.add_instructions(
            "; Simulation settings",
            # [".STEP PARAM Rmotor LIST 21 28"],
            ".TRAN 3m",
            # ".step param run 1 2 1"
    )
    # do parameter sweep
    for res in range(5):
        # LTC.runs_to_do = range(2)
        netlist.set_parameters(ANA=res)
        raw, log = netlist.run()
        print("Raw file '%s' | Log File '%s'" % (raw, log))
    # Sim Statistics
    print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))


    def callback_function(raw_file, log_file):
        print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))


    LTC = SimCommander(meAbsPath + "\\test_files\\testfile.asc", parallel_sims=1)
    tstart = 0
    for tstop in (2, 5, 8, 10):
        tduration = tstop - tstart
        LTC.add_instruction(".tran {}".format(tduration), )
        if tstart != 0:
            LTC.add_instruction(".loadbias {}".format(bias_file))
            # Put here your parameter modifications
            # LTC.set_parameters(param1=1, param2=2, param3=3)
        bias_file = "sim_loadbias_%d.txt" % tstop
        LTC.add_instruction(".savebias {} internal time={}".format(bias_file, tduration))
        tstart = tstop
        LTC.run(callback=callback_function)

    LTC.reset_netlist()
    LTC.add_instruction('.ac dec 40 1m 1G')
    LTC.set_component_value('V1', 'AC 1 0')
    LTC.run(callback=callback_function)
    LTC.wait_completion()
