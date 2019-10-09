import subprocess
import os
import time
import sys


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


class LTCommander(object):
    LTspiceIV_exe = [r"C:\Program Files (x86)\LTC\LTspiceIV\scad3.exe"]
    LTspiceXVII_exe = [r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe"]
    LTspice_arg = {'netlist': ['-netlist'], 'run': ['-b', '-Run']}

    def __init__(self, circuit_file: str):
        """LTspice Commander Class. It serves to start batches of simulations"""
        circuit_path, filename = os.path.split(circuit_file)

        self.circuit_path = circuit_path
        self.circuit_file = filename
        self.circuit_radic = os.path.splitext(circuit_file)[0]
        # self.masterlogname = circuit_radical + '.masterlog'

        self.logfilename = None  # Used to force the log filename to a user defined one.
        self.masterlog = self.circuit_radic + '.masterlog'
        mlog = open(self.masterlog, 'a+')
        mlog.write(time.asctime() + ':' + "Simulation Started\n")
        mlog.close()
        self.defaults = {}
        self.parameters = {}
        self.settings = []
        self.runno = 0      # number of total runs
        self.failSim = 0    # number of failed simulations
        self.okSim = 0      # number of succesfull completed simulations
        self.failParam = [] # collects for later user investigation of failed parameter sets
        # Sel existing LTC Kernel
        if ( True == os.path.isfile(self.LTspiceIV_exe[0]) ):
            self.LTspice_exe = self.LTspiceIV_exe
        elif (True == os.path.isfile(self.LTspiceXVII_exe[0]) ):
            self.LTspice_exe = self.LTspiceXVII_exe
        else:
            print("Error: No LTSpice installation found")

    def __del__(self):
        """Class Destructor : Closes Everything"""
        # self.write_log("Simulation Ended\n")
        pass

    def setLTspiceVersion(self, exe):
        if exe == 4:
            self.LTspice_exe = self.LTspiceIV_exe
        elif exe == 17:
            self.LTspice_exe = self.LTspiceXVII_exe
        else:
            raise ValueError("Invalid LTspice Version. Allowed versions are 4 and 17.")

    def run_only(self, runs_to_do):
        self.runs_to_do = runs_to_do

    def if_run(self):
        """Checks if the run should be done"""
        if hasattr(self, "runs_to_do"):
            return self.runno in self.runs_to_do
        else:
            return True

    def write_log(self, text: str):
        mlog = open(self.masterlog, 'a')
        mlog.write(time.asctime() + ':' + text)
        mlog.close()

    def set_defaults(self, **kwargs):
        for key in kwargs:
            self.defaults[key] = kwargs[key]

    def reset_params(self):
        self.logfilename = None
        for key in self.defaults:
            self.parameters[key] = self.defaults[key]

    def set_settings(self, *settings):
        """
        Serves to save to the sim_settings.lob file simulation primitives other than .PARAM .
        For example:
          [".tran 10m"],   #-> makes a transient simulation
          [".meas TRAN Icurr AVG I(Rs1) TRIG time=1.5ms TARG time=2.5ms"], #-> Establishes a measuring
          [.step run 1 100, 1"], #-> makes the simulation run 100 times
        :type settings: (str,list)
        """
        self.settings = settings

    def set_params(self, **kwargs):
        for key in kwargs:
            self.parameters[key] = kwargs[key]

    def write_params(self):
        f = open(self.circuit_path + os.path.sep + "sim_settings.lib", 'w')

        # completes missing parameters
        for key in self.defaults:
            self.parameters.setdefault(key, self.defaults[key])

        for line in self.settings:
            f.write(line + '\n')

        f.write("; Parameter Settings\n")
        for param, value in self.parameters.items():
            f.write(".param %s = %s\n" % (param, str(value)))

        f.close()

    def set_logname(self, filename):
        self.logfilename = filename

    def run(self):
        """
        @note:  writes configuration in sim_settings.lib, starts LTSpice and 
                checks for sim errors
        """
        # update number of simulation
        self.runno += 1
        # decide sim required
        if self.if_run():
            # Write the new settings
            self.write_params()
            # run the simulation
            start_time = time.clock()
            print(time.asctime(), ": Starting simulation %d\n" % self.runno)
            version = sys.version_info
            # prepare commands, two stages used to enable load of sim_settings w/o open GUI
            # see: https://www.mikrocontroller.net/topic/480647?goto=5965300#5965300
            cmd_netlist = self.LTspice_exe + self.LTspice_arg.get('netlist') + [self.circuit_path + os.path.sep + self.circuit_file]
            cmd_run     = self.LTspice_exe + self.LTspice_arg.get('run') + [self.circuit_path + os.path.sep + self.circuit_file[0:len(self.circuit_file)-4] + ".net"]
            retcode     = 0
            # start execution
            if version.major > 3 and version.minor >= 6:
                # combine sim settings and model
                result  = subprocess.run(cmd_netlist)    
                retcode |= result.returncode            # logical or to collect all eros
                # do simulation
                result  = subprocess.run(cmd_run)
                retcode |= result.returncode            # logical or to collect all eros
            else:
                retcode |= subprocess.call(cmd_netlist) # build netlist
                retcode |= subprocess.call(cmd_run)     # calculate
            # process the logfile, user can rename it
            if self.logfilename:
                dest_log = self.circuit_path + os.path.sep + self.logfilename
            else:
                dest_log = self.circuit_radic + ('%d.log' % self.runno)
            # print simulation time
            sim_time = time.strftime("%H:%M:%S", time.gmtime(time.clock() - start_time))
            # handle simstate
            if retcode == 0:
                # simulation succesfull
                print(time.asctime() + ": Simulation Successful. Time elapsed %s:\n" % sim_time)
                os.replace(self.circuit_radic + '.log', dest_log)
                self.write_log("%d, %s\n" % (self.runno, self.parameters))
                self.okSim += 1
            else:
                # simulation failed
                try:
                    os.replace(self.circuit_radic + '.log', dest_log + '.fail')
                except:
                    pass
                # update failed parameters and counter
                self.failSim += 1
                curParam = self.parameters      # prepare modify
                curParam['runno'] = self.runno  # add run number
                self.failParam.append(curParam) # to list
                # raise exception for try/except construct
                # SRC: https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python
                raise ValueError(time.asctime() + ': Simulation number ' + str(self.runno) + ' Failed !')
        else:
            # no simulation required
            raise UserWarning('skipping simulation ' + str(self.runno))


if __name__ == "__main__":
    # get script absolute path
    meAbsPath = os.path.dirname(os.path.realpath(__file__));
    # select spice model
    LTC = LTCommander(meAbsPath + "\\test_files\\testfile.asc")
    # set default arguments
    LTC.set_defaults(res=0, cap=100e-6)
    # define simulation
    LTC.set_settings(
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
            continue    # skip loop iteration
    # Sim Statistics
    print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))
