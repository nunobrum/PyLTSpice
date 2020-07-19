from warnings import warn
import subprocess
import threading
import logging
import os
import time
from time import sleep
import sys
import re
import traceback
from typing import Optional, Callable, Union, Any

__all__ = ('sweep', 'sweep_log', 'LTCommander', 'SimCommander', 'cmdline_switches')


logging.basicConfig(filename='LTSpiceBatch.log', level=logging.INFO)

END_LINE_TERM = '\n'

# A Spice netlist can only have one of the instructions below, otherwise an error will be raised
UNIQUE_SIMULATION_DOT_instructionS = ('.AC', '.DC', '.TRAN', 'NOISE', '.DC', '.TF')

REPLACE_REGXES = {
    'B': r"^B[VI]\w+(\s+[\w\+\-]+){2}\s+(?P<value>.*)$",  # Behavioral source
    'C': r"^C\w+(\s+[\w\+\-]+){2}\s+(?P<value>({)?(?(3).*}|([0-9\.E+-]+(Meg|[kmup])?R?))).*$",  # Capacitor
    'D': r"^D\w+(\s+[\w\+\-]+){2}\s+(?P<value>\w+).*$",  # Diode
    'I': r"^I\w+(\s+[\w\+\-]+){2}\s+(?P<value>.*)$",  # Current Source
    'J': r"^J\w+(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # JFET
    'K': r"^K\w+(\s+[\w\+\-]+){2:4}\s+(?P<value>[\+\-]?[0-9\.E+-]+[kmup]?).*$",  # Mutual Inductance
    'L': r"^L\w+(\s+[\w\+\-]+){2}\s+(?P<value>({)?(?(3).*}|([0-9\.E+-]+(Meg|[kmup])?R?))).*$",  # Inductance
    'M': r"^M\w+(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # MOSFET
    'Q': r"^Q\w+(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # Bipolar
    'R': r"^R\w+(\s+[\w\+\-]+){2}\s+(?P<value>({)?(?(3).*}|([0-9\.E+-]+(Meg|[kmup])?R?))).*$",  # Resistors
    'V': r"^V\w+(\s+[\w\+\-]+){2}\s+(?P<value>.*)$",  # Voltage Source
    'X': r"^X\w+(\s+[\w\+\-]+){1,99}\s+(?P<value>\w+)(\s+\w+\s*=\s*\S+)*$",  # Sub-circuit
}

LTspiceIV_exe = [r"C:\Program Files (x86)\LTC\LTspiceIV\scad3.exe"]
LTspiceXVII_exe = [r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe"]
LTspice_arg = {'netlist': ['-netlist'], 'run': ['-b', '-Run']}

cmdline_switches = []

# Sel existing LTC Kernel
if os.path.isfile(LTspiceXVII_exe[0]):
    LTspice_exe = LTspiceXVII_exe
    logging.info("Found LTSpice XVII. Will use this engine.")
elif os.path.isfile(LTspiceIV_exe[0]):
    LTspice_exe = LTspiceIV_exe
    logging.info("Found LTSpice IV. Will use this engine.")
else:
    error_message = "Error: No LTSpice installation found"
    logging.error(error_message)
    raise FileNotFoundError(error_message)


def _get_group_regxstr(regstr, param):
    """(Private function. Not to be used directly)
    Helper function to parse regular expressions."""
    a = regstr.find("(?P<%s>" % param)
    if a != -1:
        b = a + 1
        parenthesis_count = 0
        while b < len(regstr):
            if regstr[b] == ')':
                if parenthesis_count == 0:
                    return regstr[a:b + 1]
                else:
                    parenthesis_count -= 1
            elif regstr[b] == '(':
                parenthesis_count += 1
            b += 1
    return None


def _is_unique_instruction(instruction):
    """(Private function. Not to be used directly)
    Returns true if the instruction is one of the unique instructions"""
    cmd = instruction.upper()
    for directive in UNIQUE_SIMULATION_DOT_instructionS:
        if cmd.startswith(directive):
            return True
    return False


def sweep(start: Union[int, float], stop: Union[int, float], step: Union[int, float] = 1):
    """Helper function.
    Generator function to be used in sweeps.
    Advantages towards the range python built-in functions
    - Supports floating point arguments
    - Supports both up and down sweeps-
    Usage:
        >>> list(sweep(0.3, 1.1, 0.2))
        [0.3, 0.5, 0.7, 0.9000000000000001, 1.1]
        >>> list(sweep(15, -15, 2.5))
        [15, 12.5, 10.0, 7.5, 5.0, 2.5, 0.0, -2.5, -5.0, -7.5, -10.0, -12.5, -15.0]
        """
    if step < 0:
        step = -step
    assert step != 0, "Step cannot be 0"
    val = start
    inc = 0
    if start < stop:
        while val <= stop:
            yield val
            inc += 1
            val = start + inc * step
    elif start > stop:
        while val >= stop:
            yield val
            inc += 1
            val = start - inc * step


def sweep_log(start: Union[int, float], stop: Union[int, float], step: Union[int, float] = 10):
    """Helper function.
    Generator function to be used in logarithmic sweeps.
Advantages towards the range python built-in functions_
    - Supports floating point arguments
    - Supports both up and down sweeps.
    Usage:
        >>> list(sweep_log(0.1, 11e3, 10))
        [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0]
        >>> list(sweep_log(1000, 1, 2))
        [1000, 500.0, 250.0, 125.0, 62.5, 31.25, 15.625, 7.8125, 3.90625, 1.953125]
        """
    stp = abs(step)
    assert stp > 1.0, "The Step should be higher than 1"
    if start < stop:
        while start <= stop:
            yield start
            start *= stp
    elif start > stop:
        while start >= stop:
            yield start
            start /= stp


if sys.version_info.major >= 3 and sys.version_info.minor >= 6:
    clock_function = time.process_time

    def run_function(command):
        result = subprocess.run(command)
        return result.returncode
else:
    clock_function = time.clock

    def run_function(command):
        return subprocess.call(command)


class ComponentNotFoundError(Exception):
    """Component Not Found Error"""


class RunTask(threading.Thread):
    """This is an internal Class and should not be used directly by the User."""

    def __init__(self, run_no, netlis_file: str, callback: Callable[[str, str], Any]):
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
        cmd_run = LTspice_exe + LTspice_arg.get('run') + [self.netlist_file] + cmdline_switches

        # run the simulation
        start_time = clock_function()
        print(time.asctime(), ": Starting simulation %d" % self.run_no)

        # start execution
        self.retcode = run_function(cmd_run)

        # print simulation time
        sim_time = time.strftime("%H:%M:%S", time.gmtime(clock_function() - start_time))

        # Cleanup everything
        if self.retcode == 0:
            # simulation succesfull
            print(time.asctime() + ": Simulation Successful. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))
            if self.callback:
                netlist_radic = self.netlist_file.rstrip('.net')
                raw_file = netlist_radic + '.raw'
                log_file = netlist_radic + '.log'
                if os.path.exists(raw_file) and os.path.exists(log_file):
                    print("Calling the callback function")
                    try:
                        self.callback(raw_file, log_file)
                    except Exception as err:
                        error = traceback.format_tb(err)
                        logger.error(error)
                else:
                    logger.error("Simulation Raw file or Log file were not found")
            else:
                print('No Callback')
        else:
            # simulation failed
            logger.warning(time.asctime() + ": Simulation Failed. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))


class SimCommander(object):
    """Class for launch  LTSpice simulations from a Python Script, thus allowing to
    overcome the 3 dimensions STEP limitation on LTSpice, update resistor values, or component models.

    Usage
    -----

        ```
        LTC = SimCommander("my_circuit.asc")
        for dmodel in ("BAT54", "BAT46WJ")
            LTC.set_element_model("D1", model)  # Sets the Diode D1 model
            LTC.set_parameters(temp=80)  # Sets the simulation temperature to be 80 degrees
            LTC.set_component_value('R1', 3300)  #  Updates the resistor R1 value to be 3.3k
            LTC.set_component_value('R2', '3.3k')  #  Updates the resistor R2 value to be 3.3k
            LTC.run()

        LTC.wait_completion()  # Waits for the LTSpice simulations to complete

        print("Total Simulations: {}".format(LTC.runno))
        print("Successful Simulations: {}".format(LTC.okSim))
        print("Failed Simulations: {}".format(LTC.failSim))

        ```

    The code above will simulate a circuit with two different diode models, setting the simulation temperature to
    80 degrees and updates the values of R1 and R2 to 3.3k.

    For making better use of today's computer capabilities, the SimCommander spawns several LTSpice instances
    each executing in parallel a simulation.
    By default the number of parallel simulations is 4, however the user can override this in two ways. Either
    using the class constructor argument ´parallel_sims´ or by forcing the allocation of more processes in the
    run() call by setting wait_resource=False.
            LTC.run(wait_resource=False)

    The recommended way is to set the parameter ´parallel_sims´ in the class constructor.
            LTC=SimCommander("my_circuit.asc", parallel_sims=8)

    The wait_completion() function is needed only if the code below needs that all the simulations to be completed.
    Since SimCommander spawns different threads to supervise the different simulations, the class itself may be
    consumed by the Garbage Collector once all simulations are requested, but not finished.
    The wait_completion() function thus assures that all simulations are finished.

    Callbacks
    ---------
    As seen above, the `wait_completion()` can be used to wait for all the simulations to be finished. However, this is
    not efficient on a multiprocessor point of view. Ideally, the post-processing should be also handled while other
    simulations are still running. For this purpose, the user can use a function call backs.

    A function callback must receive two arguments. The RAW and the LOG filenames. Below is an example of a callback
    function
            ```
            def processing_data(raw_filename, log_filename):
                '''This is a call back function that just prints the filenames'''
                print("Simulation Raw file is %s. The log is %s" % (raw_filename, log_filename)
                # Other code below either using LTSteps.py or LTSpice_RawRead.py
                log_info = LTSpiceLogReader(log_filename)
                log_info.read_measures()
                rise, measures = log_info.dataset["rise_time")
            ```

    """

    def __init__(self, circuit_file: str, parallel_sims: int = 4):
        """LTspice instructioner Class. It serves to start batches of simulations"""
        circuit_path, filename = os.path.split(circuit_file)

        self.circuit_path = circuit_path
        # self.circuit_file = filename
        fname, ext = os.path.splitext(filename)
        self.circuit_radic = circuit_path + os.path.sep + fname

        self.cmdline_switches = []
        self.parallel_sims = parallel_sims
        self.threads = []

        # master_log_filename = self.circuit_radic + '.masterlog' TODO: create the JSON or YAML file
        self.logger = logging.getLogger("LTCommander")
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
            cmd_netlist = LTspice_exe + LTspice_arg.get('netlist') + [circuit_file]

            print("Creating Netlist")
            retcode = run_function(cmd_netlist)
            if retcode == 0:
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

    def _getline_startingwith(self, substr):
        """Internal function. Do not use."""
        substr_upper = substr.upper()
        for line_no, line in enumerate(self.netlist):
            line_upcase = line.upper()
            if line_upcase.startswith(substr_upper):
                return line_no
        return -1

    def _get_param_line(self, param):
        """Internal function. Do not use."""
        line_no = 0
        prm = param.upper()
        for line in self.netlist:
            line_upcase = line.upper()
            if line_upcase.startswith('.PARAM ') and (prm in line_upcase):
                return line_no
            # TODO process when the line is ending with +
            line_no += 1
        else:
            return -1

    def _set_model_and_value(self, component, value):
        """Internal function. Do not use."""
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regxstr = REPLACE_REGXES.get(prefix, None)  # Obtain RegX to make the update

        if regxstr is None:
            print("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            print("Got '{}'".format(component))
            return

        if isinstance(value, str):
            regxvaluestr = _get_group_regxstr(regxstr, 'value')
            regexvalue = re.compile(regxvaluestr, re.IGNORECASE)
            m = regexvalue.match(value)
            if m is None:
                raise ValueError("Value is not in the good format. Expecting ""{}"". Got ""{}""".format(regxvaluestr,
                                                                                                        value))
        else:
            value = str(value)

        line_no = self._getline_startingwith(component)
        if line_no != -1:  # The component was found
            regex = re.compile(regxstr, re.IGNORECASE)
            line = self.netlist[line_no]
            m = regex.match(line)
            if m is None:
                raise NotImplementedError('Unsupported line "{}"\nExpected format is "{}"'.format(line, regxstr))
                # print("Unsupported line ""{}""".format(line))
            else:
                start = m.start('value')
                end = m.end('value')
                line = line[:start] + value + line[end:]
                self.netlist[line_no] = line
        else:
            error_msg = "Component '%s' not found in netlist" % component
            self.logger.error(error_msg)
            raise ComponentNotFoundError(error_msg)

    def _get_model_and_value(self, component) -> Optional[str]:
        """Internal function. Do not use."""
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regxstr = REPLACE_REGXES.get(prefix, None)  # Obtain RegX to make the update

        if regxstr is None:
            self.logger.warning("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            self.logger.warning("Got '{}'".format(component))
            return None

        line_no = self._getline_startingwith(component)
        if line_no != -1:  # The component was found
            regex = re.compile(regxstr, re.IGNORECASE)
            line = self.netlist[line_no]
            m = regex.match(line)
            if m is None:
                error_msg = 'Unsupported line "{}"\nExpected format is "{}"'.format(line, regxstr)
                self.logger.error(error_msg)
                raise NotImplementedError(error_msg)
                # print("Unsupported line ""{}""".format(line))
            else:
                start = m.start('value')
                end = m.end('value')
                return line[start:end]
        else:
            error_msg = "Component '%s' not found in netlist" % component
            self.logger.error(error_msg)
            raise ComponentNotFoundError(error_msg)

    def setLTspiceVersion(self, exe: int) -> None:
        """For the ones that still can have access to the old IV version, you can select which version to use.
        Parameters
        ---------
        exe : int
            Use 4 for LTSpice IV and 17 for LTSpice XVII.

        :returns"""
        global LTspice_exe
        if exe == 4:
            LTspice_exe = LTspiceIV_exe
        elif exe == 17:
            LTspice_exe = LTspiceXVII_exe
        else:
            raise ValueError("Invalid LTspice Version. Allowed versions are 4 and 17.")

    def add_LTspiceRunCmdLineSwitches(self, *args) -> None:
        """Used to add an extra command line argument such as -I<path> to add symbol search path or -FastAccess
        to convert the raw file into Fast Access.
        The arguments is a list of strings as is defined in the LTSpice command line documentation.

        Parameters
        ----------
        *args : list of strings
            A list of command line switches such as "-ascii" for generating a raw file in text format or "-alt" for
            setting the solver to alternate. See Command Line Switches information on LTSpice help file.

        Returns
        -------
        Nothing
        """
        global cmdline_switches
        cmdline_switches = args

    def add_instruction(self, instruction: str) -> None:
        """Serves to add SPICE instructions to the simulation netlist. For example:
                  .tran 10m ; makes a transient simulation
                  .meas TRAN Icurr AVG I(Rs1) TRIG time=1.5ms TARG time=2.5ms" ; Establishes a measuring
                  .step run 1 100, 1 ; makes the simulation run 100 times

        Parameters
        ----------
        instruction : str
            Spice instruction to add to the netlist. This instruction will be added at the end of the netlist,
            typically just before the .BACKANNO statement

        Returns
        -------
        Nothing
        """
        if _is_unique_instruction(instruction):
            # Before adding new instruction, delete previously set unique instructions
            i = 0
            while i < len(self.netlist):
                line = self.netlist[i]
                if _is_unique_instruction(line):
                    self.netlist[i] = instruction
                    break
                else:
                    i += 1
        else:
            # check whether the instruction is already there (dummy proofing)
            if instruction not in self.netlist:
                # Insert before backanno instruction
                try:
                    line = self.netlist.index('.backanno')
                except ValueError:
                    line = len(self.netlist) - 2  # This is where typically the .backanno instruction is
                self.netlist.insert(line, instruction)

    def add_instructions(self, *instructions):
        """Adds a list of instructions to the SPICE NETLIST.
        Example:
            LTC.add_instructions(
                ".STEP run -1 1023 1", 
                ".dc V1 -5 5"
            )"""
        for instruction in instructions:
            self.add_instruction(instruction)

    def remove_instruction(self, *instruction):
        """Usage a previously added instructions.
        Example:
            LTC.remove_instruction(".STEP run -1 1023 1")
        """
        self.netlist.remove(instruction)

    def set_parameter(self, param: str, value: Union[str, int, float]) -> None:
        """Adds a parameter to the SPICE netlist.
        Usage:
            LTC.set_parameter("TEMP", 80)

        This adds onto the netlist the following line:
            .PARAM TEMP=80
        This is an alternative to the set_parameters which is more pythonic in it's usage, 
        and allows setting more than one parameter at once.

        Parameters
        ----------
        param : str
            Spice Parameter name to be added or updated.
        value : str, int or float
            Parameter Value to be set.


        Returns
        ------
        Nothing
        """
        param_line = self._get_param_line(param)
        if param_line == -1:  # Was not found
            # the last two lines are typically (.backano and .end)
            insert_line = len(self.netlist) - 2
            self.netlist.insert(insert_line, '.PARAM {}={}  ; Batch instruction'.format(param, value))
        else:
            regx = re.compile(r"%s\s*=\s*(\w*)" % param, re.IGNORECASE)
            line = self.netlist[param_line]
            m = regx.search(line)
            start, stop = m.span()
            self.netlist[param_line] = line[:start] + "{}={}".format(param, value) + line[stop:]

    def set_parameters(self, **kwargs):
        """Adds one or more parameters to the netlist.
        Usage:
            for temp in (-40, 25, 125):
                for freq in sweep_log(1, 100E3,)
            LTC.set_parameters(TEMP=80, freq=freq)
        """
        for param in kwargs:
            self.set_parameter(param, kwargs[param])

    def set_component_value(self, device: str, value: Union[str, int, float]) -> None:
        """Changes the value of a component, such as a Resistor, Capacitor or Inductor.
        Usage:
            LTC.set_component_value('R1', '3.3k')

        Parameters
        ----------
        device : str
            Reference of the circuit element to be updated.
        value : str, int or float
            value to be be set on the given circuit element

        Raises
        ------
        ComponentNotFoundError - In case the component is not found
        ValueError - In case the value doesn't correspond to the expected format
        NotImplementedError - In case the circuit element is defined in a format which is not supported by this version.
                            If this is the case, use GitHub to start a ticket.
                            https://github.com/nunobrum/PyLTSpice
        """
        self._set_model_and_value(device, value)

    def set_element_model(self, element: str, model: str) -> None:
        """Changes the value of a circuit element, such as a diode model or a voltage supply.
        Usage:
            LTC.set_element_model('D1', '1N4148')
            LTC.set_element_model('V1' "SINE(0 1 3k 0 0 0)")

        Parameters
        ----------
        element : str
            Reference of the circuit element to be updated.
        model : str
            model name of the device to be updated

        Raises
        ------
        ComponentNotFoundError - In case the component is not found
        ValueError - In case the model format contains irregular characters
        NotImplementedError - In case the circuit element is defined in a format which is not supported by this version.
                            If this is the case, use GitHub to start a ticket.
                            https://github.com/nunobrum/PyLTSpice
        """
        self._set_model_and_value(element, model)

    def get_component_value(self, element: str):
        """Returns the value of a component from the netlist."""
        return self._get_model_and_value(element)

    def write_netlist(self, run_netlist_file: str):
        """Writes the netlist will all the requested updates into a file named <run_netlist_file>.

        Parameters
        ----------
        run_netlist_file :str
            File name of the netlist file.

        Returns
        -------
        Nothing
        """
        for i, line in enumerate(self.netlist):
            if not line.endswith(END_LINE_TERM):
                self.netlist[i] = line + END_LINE_TERM
        f = open(run_netlist_file, 'w')
        f.writelines(self.netlist)
        f.close()

    def reset_netlist(self):
        """Removes all previous edits done to the netlist, i.e. resets it to the original state.

        Parameters
        ----------
        None

        Returns
        -------
        Nothing
        """
        if os.path.exists(self.netlist_file):
            try:
                f = open(self.netlist_file, 'r')
                self.netlist = f.readlines()
                f.close()
                for i, line in enumerate(self.netlist):
                    self.netlist[i] = line.rstrip(END_LINE_TERM)
            except IOError as err:
                self.netlist = None
                error_msg = traceback.format_tb(err)
                self.logger.error(error_msg)
            except Exception as err:
                error_msg = traceback.format_tb(err)
                self.logger.error(error_msg)
                self.netlist = None

    def run(self, run_filename: str = None, wait_resource: bool = True,
            callback: Callable[[str, str], Any] = None) -> int:
        """
        Executes a simulation run with the conditions set by the user.
        Conditions are set by the set_parameter, set_component_value or add_instruction functions.

        Parameters
        ----------
        run_filename : str
            The name of the netlist can be optionally overridden if the user wants to have a better control of how the
            simulations files are generated.
        wait_resource : bool
            Setting this parameter to False, will force the simulation to start immediately, irrespective of the number
            of simulations already active.
            By default the SimCommander class uses only four processors. This number can then be overridden by setting
            the parameter ´parallel_sims´ to a different number.
            If there are more than ´parallel_sims´ simulations being done, the new one will be placed on hold till one
            of the other simulations are finished.
        callback : function(raw_file, log_file)
            The user can optionally give a callback function for when the simulation finishes, so that a processing can
            be immediately done.


        Returns
        -------
        Nothing
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
                    t = RunTask(self.runno, run_netlist_file, callback)
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
        """This function """
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
        self.updated_stats()
        while len(self.threads) > 0:
            sleep(1)
            self.updated_stats()


class LTCommander(SimCommander):

    def __init__(self, circuit_file: str):
        """(Deprecated) Class for launching LTSpice simuations in a Batch."""
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
        The run_id parameter can be used to override the naming protocol of the log files.
        :return (raw filename, log filename) if simulation is successful else (None, log file name)
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
            dest_log = "%s_%i.log" % (self.circuit_radic, self.runno)
            # print simulation time
            sim_time = time.strftime("%H:%M:%S", time.gmtime(clock_function() - start_time))
            # handle simstate
            if retcode == 0:
                # simulation succesfull
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
                dest_log += 'fail'

            try:
                os.replace(self.circuit_radic + '_run.log', dest_log)
            except FileNotFoundError:
                pass

            if retcode == 0:  # If simulation is successful
                return self.circuit_radic + '_run.raw', dest_log  # Return rawfile and logfile if simulation was OK
            else:
                return None, dest_log
        else:
            # no simulation required
            raise UserWarning('skipping simulation ' + str(self.runno))


if __name__ == "__main__":
    # get script absolute path
    meAbsPath = os.path.dirname(os.path.realpath(__file__))
    # select spice model
    LTC = LTCommander(meAbsPath + "\\testfile.asc")
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
        LTC.run()
    # Sim Statistics
    print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))
