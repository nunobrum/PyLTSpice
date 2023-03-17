#   ____       _    _                                     
#  |  _ \  ___| | _(_)_ __ ___   ___    Copyright  | Title   : Tolerance analysis on existing .asc file
#  | | | |/ _ \ |/ / | '_ ` _ \ / _ \   (c) 2020   | Project : -
#  | |_| |  __/   <| | | | | | | (_) |   Dekimo    | Authors : MVR
#  |____/ \___|_|\_\_|_| |_| |_|\___/   Products   | Created : 28/11/2022
#__________________________________________________|_________________________________________________________
#
# Uses package PyLTSpice
# Install using pip install PyLTSpice
#
# https://www.nunobrum.com/pyspicer.html

from PyLTSpice.LTSpiceBatch import SimCommander
import os
import shutil

class Tolerance(SimCommander):
    
    def __init__(self, circuit_file:str, simdir=None, **kwargs):
        
        super().__init__(circuit_file,**kwargs)
    
        self.__refidx = 0                           # for keeping count of #changes for worst-case analysis
        self.__lines = list()                       # list of modified lines, for reverting changes
        self.changed = False                        # no lines have been added to .ASC file yet

        self.orig_dir = os.getcwd()
        self.fname = os.path.splitext(os.path.basename(circuit_file))[0]    # base name of sim
        
        self.pltname = os.path.abspath(os.path.splitext(circuit_file)[0]+".plt")    # plot settings file
        if not os.path.exists(self.pltname):
            self.pltname = None
                    
        if simdir is not None:                      # simulations must be executed in different dir
            if not os.path.exists(simdir):          # make sure that dir exists
                os.makedirs(simdir)
            os.chdir(simdir)                        # change working path to sim dir
            
    def pop_dir(self):
        ''' Return to the directory that was active before the simulation was run.
        '''
        os.chdir(self.orig_dir)
        
    def copy_plot(self, suffix):
        ''' copies plotfile to current directory, with suffix matchin new analysis.
        '''
        if self.pltname is None:
            return 
        
        fname = os.path.splitext(os.path.basename(self.pltname))[0] + suffix + ".plt"
        shutil.copy(self.pltname, fname)
        
    
    def add_line(self, line):
        ''' Add an instruction for analysis, and keep list of it.
            This way we can remove them later to do a different analysis.
        '''
        self.__lines.append(line)
        self.add_instruction(line)
        
    def clear_lines(self):
        ''' Remove all the instructions that were added for a certain kind of analysis.
        '''
        for line in self.__lines:
            self.remove_instruction(line)
        self.__lines.clear()

    def run_nominal(self):
        ''' Execute the simulation using nominal values.
        '''
        assert self.changed==False, "Run nominal simulation before assigning tolerances."
        self.clear_lines()
        self.copy_plot("_nom")
        self.run(run_filename="%s_nom.net" % self.fname )

    
    def make_gauss(self, num_runs=100):
        ''' Prepare netlist for running Gaussian tolerance analysis.
            tol_val function gives Gaussian distribution of nominal value with tolerance=sigma/3
        '''
        self.clear_lines()
        self.add_line(".function tol_val(nom,tol,idx) {nom*(1+gauss(tol/3))}")
        self.add_line(".step param run 0 %d 1" % (num_runs-1) )
        
    def run_gauss(self, num_runs, split_runs=-1):
        ''' Execute a number of Gaussian analysis, split over several processes.
        '''
        if split_runs<1:
            split_runs = num_runs
        n = 0
        i = 0
        while n < num_runs:
            
            if n + (2*split_runs) < num_runs:
                amount = split_runs
            elif n + split_runs < num_runs:
                amount = split_runs//2
            else:
                amount = num_runs - n
            
            self.make_gauss(amount)
            self.copy_plot("_gs_%03d" % i)
            self.run(run_filename="%s_gs_%03d.net" % (self.fname, i) )
            i += 1
            n += amount

            if n>999:
                break


    def make_monte_carlo(self, num_runs=100):
        ''' Prepare netlist for running Monte-Carlo tolerance analysis.
            tol_val function gives random distribution of nominal value between mam+tol and nom-tol
        '''       
        self.clear_lines()
        self.add_line(".function tol_val(nom,tol,idx) {mc(nom,tol)}")
        self.add_line(".step param run 0 %d 1" % num_runs)

    def run_monte_carlo(self, num_runs, split_runs=-1):
        ''' Execute a number of Monte Carlo analysis, split over several processes.
        '''
        if split_runs<1:
            split_runs = num_runs
        n = 0
        i = 0
        while n < num_runs:
            
            if n + (2*split_runs) < num_runs:
                amount = split_runs
            elif n + split_runs < num_runs:
                amount = split_runs//2
            else:
                amount = num_runs - n
                            
            self.make_monte_carlo(amount)
            self.copy_plot("_mc_%03d" % i)
            self.run(run_filename="%s_mc_%03d.net" % (self.fname, i) )
            i += 1
            n += amount
            
            if n>999:
                break

    def make_worstcase(self, *, from_step=None, to_step=None):
        ''' Prepare netlist for running Monte-Carlo tolerance analysis.
            tol_val function alternatively chooses nom+tol or nom-tol depending on its index number.
            Then steps are defined to have enough runs to simulate each combination of values.
            
            Note: you must first apply the tolerances to all components
        '''
        assert self.__refidx>0, "You need to specify the tolerance for all components first"

        if from_step is None:
            from_step = 0
        elif from_step > 2**self.__refidx:
            return False
        
        if to_step is None or to_step > 2**self.__refidx - 1:
            to_step = 2**self.__refidx - 1

        if from_step>to_step:
            return False

        self.clear_lines()
        self.add_line(".function tol_val(nom,tol,idx) {nom*if(binary(run,idx),1+tol,1-tol)}")
        self.add_line(".func binary(run,idx) floor(run/(2**idx))-2*floor(run/(2**(idx+1)))")
        
        if to_step - from_step > 0:
            self.add_line(".step param run %d %d 1" % (from_step, to_step ))
        else:
            self.add_line(".param run %d" % from_step )
        return True

    def run_worstcase(self, suffix=None, split_runs=-1):
        ''' Execute a number of Monte Carlo analysis, split over several processes.
        '''
        if split_runs<1:
            split_runs = 2**self.__refidx
        
        if suffix is None:
            suffix = ""
        else:
            suffix = "_"+suffix
            
        n = 0
        i = 0

        while True:
            have_sim = self.make_worstcase(from_step=n, to_step=n+split_runs-1)
            if not have_sim:
                break
            
            self.copy_plot("_wc_%03d%s" % (i,suffix) )
            self.run(run_filename="%s_wc_%03d%s.net" % (self.fname, i,suffix) )
            i += 1
            n += split_runs
            
            if n>999:
                break

    def set_tolerance(self, refdesses, percent):
        ''' Replace value of component with a formula for statistical analysis.
        
            @param refdesses   Single refdes or list of refdesses.
            @param percent     Tolerance to apply, in percent
        '''
        if not isinstance(refdesses, list):                                 # change parameter to list if just 1 refdes given
            refdesses = [ refdesses ]
            
        self.changed = True
        tolstr = ('%f' % (percent/100)).rstrip('0').rstrip('.')             # make string tolerances as a nice number
        
        for refdes in refdesses:                                            # go over all the refdesses
            val = self.get_component_value(refdes)                          # get there present value
            new_val = "{tol_val(%s,%s,%d)}" % (val,tolstr,self.__refidx)    # calculate expression for new value
            self.set_component_value(refdes, new_val)                       # update the value
            self.__refidx = self.__refidx+1                                 # update refdes counter

    def set_param_tolerance(self, params, percent):
        ''' Replace value of component with a formula for statistical analysis.
        
            @param refdesses   Single refdes or list of refdesses.
            @param percent     Tolerance to apply, in percent
        '''
        if not isinstance(params, list):                                 # change parameter to list if just 1 refdes given
            params = [ params ]
            
        self.changed = True
        tolstr = ('%f' % (percent/100)).rstrip('0').rstrip('.')             # make string tolerances as a nice number
        
        for param in params:                                            # go over all the refdesses
            val = self.get_parameter(param)                          # get there present value
            new_val = "{tol_val(%s,%s,%d)}" % (val,tolstr,self.__refidx)    # calculate expression for new value
            self.set_parameter(param, new_val)                       # update the value
            self.__refidx = self.__refidx+1                                 # update refdes counter


    def set_deviation(self, refdesses, deviation):
        ''' Add a deviation to the value of a component
        
            @param refdesses   Single refdes or list of refdesses.
            @param deviation   Value to add to actual value
        '''
        if not isinstance(refdesses, list):                                 # change parameter to list if just 1 refdes given
            refdesses = [ refdesses ]
            
        self.changed = True
        
        for refdes in refdesses:                                            # go over all the refdesses
            val = self.get_component_value(refdes)                          # get there present value
            new_val = "{{%s}+tol_val(%s,1,%d)-%s}" % (val,deviation,self.__refidx, deviation)    # calculate expression for new value
            self.set_component_value(refdes, new_val)                       # update the value
            self.__refidx = self.__refidx+1                                 # update refdes counter






