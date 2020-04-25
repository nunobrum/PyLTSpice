import subprocess
import os
import time
import sys
import re
import traceback

__all__ = ('sweep', 'sweep_log', 'LTCommander')

END_LINE_TERM = '\n'

# A Spice netlist can only have one of the commands below, otherwise an error will be raised
UNIQUE_SIMULATION_DOT_COMMANDS = ('.AC', '.DC', '.TRAN', 'NOISE', '.DC', '.TF')

REPLACE_REGXES = {
    'C': "^C\w+(\s+[\w\+\-]+){2}\s+(?P<value>\+?[0-9\.E+-]+[MmHUuPp]?F?).*$",  # Capacitor
    'D': "^D\w+(\s+[\w\+\-]+){2}\s+(?P<value>\w+).*$",  # Diode
    'I': "^I\w+(\s+[\w\+\-]+){2}\s+(?P<value>[\+\-]?[0-9\.E+-]+(Meg|[KkMmUuPp])?).*$",  # Current Source
    'J': "^J\w+(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # JFET
    'K': "^K\w+(\s+[\w\+\-]+){2:4}\s+(?P<value>[\+\-]?[0-9\.E+-]+[KkMmUuPp]?).*$",  # Mutual Inductance
    'L': "^L\w+(\s+[\w\+\-]+){2}\s+(?P<value>\+?[0-9\.E+-]+(Meg|[KkMmUuPp])?H?).*$",  # Inductance
    'M': "^M\w+(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # MOSFET
    'Q': "^Q\w+(\s+[\w\+\-]+){3}\s+(?P<value>\w+).*$",  # Bipolar
    'R': "^R\w+(\s+[\w\+\-]+){2}\s+(?P<value>\+*[0-9\.E+-]+(Meg|[KkMmUuPp])?R?).*$",  # Resistors
    'V': "^V\w+(\s+[\w\+\-]+){2}\s+(?P<value>[\+\-]?[0-9\.E+-]+(Meg|[KkMmUuPp])?).*$",  # Voltage Source
    'X': "^X\w+(\s+[\w\+\-]+){1,99}\s+(?P<value>\w+)(\s+\w+\s*=\s*\S+)*$",  # Sub-circuit
}


def _get_group_regxstr(regstr, param):
    a = regstr.find("(?P<%s>" % param)
    if a != -1:
        b = a + 1
        parenthesis_count = 0
        while b < len(regstr):
            if regstr[b] == ')':
                if parenthesis_count == 0:
                    return regstr[a:b+1]
                else:
                    parenthesis_count -= 1
            elif regstr[b] == '(':
                parenthesis_count += 1
            b += 1
    return None


def _is_unique_command(command):
    """Returns true if the command is one of the unique commands"""
    cmd = command.upper()
    for directive in UNIQUE_SIMULATION_DOT_COMMANDS:
        if cmd.startswith(directive):
            return True
    return False


def sweep(start, stop, step=1):
    """Generator function to be used in sweeps.
Advantages towards the range python built-in functions_
    - Supports floating point arguments
    - Supports both up and down sweeps
    - Less memory footprint for large sweeps"""
    inc = 0
    val = start
    if start < stop:
        while val <= stop:
            yield val
            inc += 1
            val = start + inc * step

    elif start > stop:
        while start >= stop:
            yield val
            inc += 1
            val = start + inc * step


def sweep_log(start, stop, step=10):
    """Generator function to be used in sweeps.
Advantages towards the range python built-in functions_
    - Supports floating point arguments
    - Supports both up and down sweeps
    - Less memory footprint for large sweeps"""
    stp = abs(step)
    if start < stop:
        while start <= stop:
            yield start
            start *= stp
    elif start > stop:
        while start >= stop:
            yield start
            start /= stp

if sys.version_info.major >= 3 and sys.version_info.minor >= 6:
    clock_function = time.clock
else:
    clock_function = time.process_time


class LTCommander(object):
    LTspiceIV_exe = [r"C:\Program Files (x86)\LTC\LTspiceIV\scad3.exe"]
    LTspiceXVII_exe = [r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe"]
    LTspice_arg = {'netlist': ['-netlist'], 'run': ['-b', '-Run']}

    def __init__(self, circuit_file: str):
        """LTspice Commander Class. It serves to start batches of simulations"""
        circuit_path, filename = os.path.split(circuit_file)

        self.circuit_path = circuit_path
        # self.circuit_file = filename
        self.circuit_radic = circuit_path + os.path.sep + os.path.splitext(filename)[0]
        self.run_netlist_file = self.circuit_radic + '_run.net'
        self.logfilename = None  # Used to force the log filename to a user defined one.
        self.masterlog = self.circuit_radic + '.masterlog'

        mlog = open(self.masterlog, 'a+')

        # self.parameters = {}
        # self.commands = []
        # self.value_updates = {}  # Resistances, Capacitances, Inductaces, Voltage and Current Sources
        # self.model_updates = {} # Diodes, Transistors,
        # self.line_updates = []
        self.runno = 0  # number of total runs
        self.failSim = 0  # number of failed simulations
        self.okSim = 0  # number of succesfull completed simulations
        # self.failParam = []  # collects for later user investigation of failed parameter sets

        # Sel existing LTC Kernel
        if os.path.isfile(self.LTspiceIV_exe[0]):
            self.LTspice_exe = self.LTspiceIV_exe
        elif os.path.isfile(self.LTspiceXVII_exe[0]):
            self.LTspice_exe = self.LTspiceXVII_exe
        else:
            msg = "Error: No LTSpice installation found"
            print(msg)
            mlog.write(msg + END_LINE_TERM)
            mlog.close()
            return
        # prepare commands, two stages used to enable load of sim_settings w/o open GUI
        # see: https://www.mikrocontroller.net/topic/480647?goto=5965300#5965300
        cmd_netlist = self.LTspice_exe + self.LTspice_arg.get('netlist') + [circuit_file]

        mlog.write("Creating Netlist" + END_LINE_TERM)
        version = sys.version_info
        if version.major > 3 and version.minor >= 6:
            result = subprocess.run(cmd_netlist)
            retcode = result.returncode  # logical or to collect all eros
        else:
            retcode = subprocess.call(cmd_netlist)  # build netlist

        self.netlist = []
        if retcode == 0:
            mlog.write("The Netlist was successfully created" + END_LINE_TERM)
            netlist_file = self.circuit_radic + ".net"
            if os.path.exists(netlist_file):
                try:
                    f = open(netlist_file, 'r')
                    self.netlist = f.readlines()
                    f.close()
                except IOError as err:
                    self.netlist = []
                except Exception as err:
                    traceback.print_tb(err)
                    self.netlist = []

        if len(self.netlist) == 0:
            mlog.write("Unable to create Netlist")
        mlog.close()

    def __del__(self):
        """Class Destructor : Closes Everything"""
        # self.write_log("Simulation Ended" + end_line)
        pass

    def _getline_startingwith(self, component):
        comp = component.upper()
        for line_no, line in enumerate(self.netlist):
            lineU = line.upper()
            if line.startswith(comp):
                return line_no
        return -1

    def _get_param_line(self, param):
        line_no = 0
        prm = param.upper()
        for line in self.netlist:
            lineU = line.upper()
            if lineU.startswith('.PARAM ') and (prm in lineU):
                return line_no
            # TODO process when the line is ending with +
            line_no += 1
        else:
            return -1

    def _set_model_and_value(self, component, value):
        prefix = component[0]  # Using the first letter of the component to identify what is it
        regxstr = REPLACE_REGXES.get(prefix, None)  # Obtain RegX to make the update

        if regxstr is None:
            print("Component must start with one of these letters:\n", ','.join(REPLACE_REGXES.keys()))
            print("Got '{}'".format(component))
            return

        if isinstance(value, str):
            regxvaluestr = _get_group_regxstr(regxstr, 'value')
            regexvalue = re.compile(regxvaluestr)
            m = regexvalue.match(value)
            assert m is not None, "Value is not in the good format"
        else:
            value = str(value)

        line_no = self._getline_startingwith(component)
        if line_no != -1:  # The component was found
            regex = re.compile(regxstr)
            line = self.netlist[line_no]
            match = regex.match(line)
            if match is None:
                #raise NotImplementedError("Unsupported line ""{}""".format(line))
                print("Unsupported line ""{}""".format(line))
            else:
                start = match.start('value')
                end = match.end('value')
                line = line[:start] + value + line[end:]
                self.netlist[line_no] = line
            line_no += 1
        else:
            raise Exception("Component not found in netlist")

    def setLTspiceVersion(self, exe):
        if exe == 4:
            self.LTspice_exe = self.LTspiceIV_exe
        elif exe == 17:
            self.LTspice_exe = self.LTspiceXVII_exe
        else:
            raise ValueError("Invalid LTspice Version. Allowed versions are 4 and 17.")

    def write_log(self, text: str):
        mlog = open(self.masterlog, 'a')
        mlog.write(time.asctime() + ':' + text)
        mlog.close()

    def add_command(self, command):
        """Serves to save to the sim_settings.lob file simulation primitives other than .PARAM .
                For example:
                  [".tran 10m"],   #-> makes a transient simulation
                  [".meas TRAN Icurr AVG I(Rs1) TRIG time=1.5ms TARG time=2.5ms"], #-> Establishes a measuring
                  [.step run 1 100, 1"], #-> makes the simulation run 100 times
                :type settings: (str,list)
                """
        if _is_unique_command(command):  # Before adding new command, delete previously set unique commands
            i = 0
            while i < len(self.netlist):
                line = self.netlist[i]
                if _is_unique_command(line):
                    self.netlist[i] = command + END_LINE_TERM
                    break
                else:
                    i += 1
        else:
            # check whether the command is already there (dummy proofing)
            if command not in self.netlist:
                # Insert before backanno command
                try:
                    line = self.netlist.index('.backanno' + END_LINE_TERM)
                except ValueError:
                    line = len(self.netlist) - 2  # This is where typically the .backanno command is
                self.netlist.insert(line, command + END_LINE_TERM)

    def add_commands(self, *commands):
        for command in commands:
            self.add_command(command)

    def remove_command(self, *command):
        self.netlist.remove(command)

    def set_parameter(self, param, value):
        param_line = self._get_param_line(param)
        if param_line == -1:  # Was not found
            # the last two lines are typically (.backano and .end)
            insert_line = len(self.netlist) - 2
            self.netlist.insert(insert_line, '.param {} = {}  ; Batch command'.format(param, value) + END_LINE_TERM)
        else:
            regx = re.compile("%s\s*=\s*(\w*)" % param, re.IGNORECASE)
            line = self.netlist[param_line]
            m = regx.search(line)
            start, stop = m.span()
            self.netlist[param_line] = line[:start] + "{} = {}".format(param, value) + line[stop:]

    def set_parameters(self, **kwargs):
        for param in kwargs:
           self.set_parameter(param, kwargs[param])

    def set_component_value(self, device, value):
        self._set_model_and_value(device, value)

    def set_element_model(self, element, model):
        self._set_model_and_value(element, model)

    def write_netlist(self):
        f = open(self.run_netlist_file, 'w')
        f.writelines(self.netlist)
        f.close()

    def reset_netlist(self):
        netlist_file = self.circuit_radic + '.net'
        f = open(netlist_file, 'r')
        self.netlist = f.readlines()
        f.close()

    def set_logname(self, filename):
        """Used to override the name of the log. If used, in must be set once per each run."""
        self.logfilename = filename

    def run(self, run_id=None):
        """
        Executes a simulation run with the conditions set by the user. (See also set_param, set_value, set_command)
        The run_only parameter can be used run only a specified
        """
        # update number of simulation
        self.runno += 1  # Using internal simulation number in case a run_id is not supplied
        # decide sim required
        if self.netlist is not None:
            # Write the new settings
            self.write_netlist()
            cmd_run = self.LTspice_exe + self.LTspice_arg.get('run') + [self.run_netlist_file]

            # run the simulation
            start_time = clock_function()
            print(time.asctime(), ": Starting simulation %d%s" % (self.runno, END_LINE_TERM))
            version = sys.version_info
            retcode = 0
            # start execution
            if version.major > 3 and version.minor >= 6:
                # combine sim settings and model
                # do simulation
                result = subprocess.run(cmd_run)
                retcode |= result.returncode  # logical or to collect all eros
            else:
                retcode |= subprocess.call(cmd_run)  # calculate
            # process the logfile, user can rename it
            if self.logfilename:
                dest_log = self.circuit_path + self.logfilename
                self.logfilename = None  # Can only be used once per simulation
            elif run_id is not None:
                dest_log = self.circuit_radic + "_{}.log".format(run_id)
            else:
                dest_log = self.circuit_radic + ('%d.log' % self.runno)
            # print simulation time
            sim_time = time.strftime("%H:%M:%S", time.gmtime(clock_function() - start_time))
            # handle simstate
            if retcode == 0:
                # simulation succesfull
                print(time.asctime() + ": Simulation Successful. Time elapsed %s:%s" % (sim_time, END_LINE_TERM))
                os.replace(self.circuit_radic + '.log', dest_log)
                self.write_log("%d%s" % (self.runno, END_LINE_TERM))
                self.okSim += 1
            else:
                # simulation failed
                try:
                    os.replace(self.circuit_radic + '.log', dest_log + '.fail')
                except:
                    pass
                # update failed parameters and counter
                self.failSim += 1
                # raise exception for try/except construct
                # SRC: https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python
                raise ValueError(time.asctime() + ': Simulation number ' + str(self.runno) + ' Failed !')
        else:
            # no simulation required
            raise UserWarning('skipping simulation ' + str(self.runno))


if __name__ == "__main__":
    # get script absolute path
    meAbsPath = os.path.dirname(os.path.realpath(__file__))
    # select spice model
    LTC = LTCommander(meAbsPath + "\\test_files\\testfile.asc")
    # set default arguments
    LTC.set_parameters(res=0, cap=100e-6)
    # define simulation
    LTC.add_commands(
        "; Simulation settings",
        # [".STEP PARAM Rmotor LIST 21 28"],
        ".TRAN 3m",
        # ".step param run 1 2 1"
    )
    # do parameter sweep
    for res in range(5):
        # LTC.runs_to_do = range(2)
        LTC.set_params(ANA=res)
        try:
            LTC.run()
        except:
            continue  # skip loop iteration
    # Sim Statistics
    print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))
