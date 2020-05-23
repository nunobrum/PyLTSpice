# README #

PySpicer is a toolchain of python utilities design to interact with LTSpice Electronic Simulator.

## What is contained in this repository ##

* __LTSteps.py__ 
An utility that extracts from LTSpice output files data, and formats it for import in a spreadsheet,s uch like Excel or Calc. 

* __LTSpice_RawRead.py__
A pure python class that serves to read raw files into a python class.

* __Histogram.py__
A python script that uses numpy and matplotlib to create an histogram and calculate the sigma deviations. This is useful for Monte-Carlo analysis. 

* __LTSpiceBatch.py__
This is a script to launch LTSpice Simulations. This is useful because:

    - Can overcome the limitation of only stepping 3 parameters
    - Different types of simulations .TRAN .AC .NOISE can be run in a single batch
    - The RAW Files are smaller and easier to treat
    - When used with the LTSpiceRaw_Reader.py and LTSteps.py, validattion of the circuit can be done automatically.
    - Different models can be simulation in a single batch. The principle of operation is the following :
        1. Add to the Spice circuit a .INC sim_settings.lib  . In this include simulation directives are written by the script per each simulation call.
        1. Use the python script to update the simulation directives and call LTSpice to run the simulation in command line.
        1. When the simulation is complete, the simulation results are renamed according to user guidance.

    Note: It only works with Windows based installations.

## How to Install ##
`pip install PyLTSpice `  

### Updating PyLTSpice ###

 `pip install --upgrade PyLTSpice `  

### Using GITHub ###

 `git clone https://github.com/nunobrum/PyLTSpice.git `  
 
If using this method it would be good to add the path where you cloned the site to python path.

 `import sys `  
 `sys.path.append(<path to PyLTSpice>) `  

## How to use ##

### LTSpice_RawRead.py ###
Include the following line on your scripts

 `from PyLTSpice.LTSpice_RawRead import LTSpiceRawRead `
 
 `from matplotlib import plot `  
 
 
 `LTR = LTSpiceRawRead("Draft1.raw") `  

 `print(LTR.get_trace_names()) `  
 `print(LTR.get_raw_property()) `  
 
 `IR1 = LTR.get_trace("I(R1)") `  
 `x = LTR.get_trace('time') # Gets the time axis `  
 `steps = LTR.get_steps() `  
 `for step in range(len(steps)): `  
 `....# print(steps[step]) `  
 `....plt.plot(x.get_time_axis(step), IR1.get_wave(step), label=steps[step]) `  

 `plt.legend() # order a legend `  
 `plt.show() `  

### LTSpice_Batch ###
This module is used to launch LTSPice simulations. Results then can be processed with either the LTSpiceRawRead
or with the LTSteps module to read the log file which can contain .MEAS results.

The script will firstly invoke the LTSpice in command line to generate a netlist, and then this netlist can be 
updated directly by the script, in order to change component values, parameters or simulation commands.

Here follows an example of operation.

 ` import os `  
 ` from PyLTSpice.LTSpiceBatch import LTCommander `  
 ` from shutil import copyfile `  
 
 ` # get script absolute path `  
 ` meAbsPath = os.path.dirname(os.path.realpath(__file__)) `  
 ` # select spice model `  
 ` LTC = LTCommander(meAbsPath + "\\Batch_Test.asc") `  
 
 ` LTC.set_parameters(res=0, cap=100e-6)  # Redefining parameters in the netlist `  
 ` LTC.set_component_value('R2', '2k')  # Redefining component values `  
 ` LTC.set_component_value('R1', '4k') `  
 ` # define simulation `  
 ` LTC.add_instructions( `  
 `     "; Simulation settings", `  
 `     ".param run = 0"  # Commands can be set directly with the .param command instad of the set_parameters(...) `  
 ` ) `  
 
 ` for opamp in ('AD712', 'AD820'): `  
 ` ....# Setting a model of the U1 Component. Note that subcircuits need the X prefix `  
 ` ....LTC.set_element_model('XU1', opamp): `  
 ` ....for supply_voltage in (5, 10, 15): `  
 ` ........LTC.set_component_value('V1', supply_voltage)  # Set a voltage source value `  
 ` ........LTC.set_component_value('V2', -supply_voltage) `  
 ` ........rawfile, logfile = LTC.run()  # Runs the simulation with the updated netlist ` 
 ` ........# The run() returns the RAW filename and LOG filenames so that can be processed with `  
 ` ........# the LTSpice_ReadRaw and LTSteps modules. `  
 ` ........# The command below is optional, used just to keep a copy of the netlist for debug purposes `  
 ` ........copyfile(LTC.run_netlist_file, `  
 ` ................."{}_{}_{}.net".format(LTC.circuit_radic, opamp, supply_voltage))  # Keep the netlist for reference `  
 
 ` LTC.reset_netlist()  # This resets all the changes done to the checklist `  
 ` LTC.add_instructions(  # Changing the simulation file`  
 `     "; Simulation settings", `  
 `     ".ac dec 30 10 1Meg", `  
 `     ".meas AC Gain MAX mag(V(out)) ; find the peak response and call it ""Gain""", `  
 `     ".meas AC Fcut TRIG mag(V(out))=Gain/sqrt(2) FALL=last" `  
 ` ) `  
 `  `  
 ` raw, log = LTC.run() `  


### LTSteps.py ###

 `python -m PyLTSpice.LTSteps <logfile or directory where last simulation was made `

### Histogram.py ###

 `python -m PyLTSpice.Histogra ` 

## To whom do I talk to? ##

* Tools website : [https://www.nunobrum.com/pyspicer.html](https://www.nunobrum.com/pyspicer.html)
* Repo owner : [me@nunobrum.com](me@nunobrum.com) 
* Alternative contact : nuno.brum@gmail.com

## History ##
* Version 1.0
LTSpiceBatch.py: 
Implemented an new approach (NOT BACKWARDS COMPATIBLE), that avoids the usage of the sim_settings.inc file.
And allows to modify not only parameters, but also models and even the simulation commands.

LTSpice_RawRead.py: 
Added the get_time_axis method to the RawRead class to avoid the problems with negative values on
time axis, when 2nd order compression is enabled in LTSpice.

LTSteps.py: 
Modified the LTSteps so it can also read measurements on log files without any steps done.


* Version 0.6
Histogram.py now has an option to make the histogram directly from values stored in the clipboard

* Version 0.5
The LTSpice_RawReader.py now uses the struc.unpack function for a faster execution

* Version 0.4
Added LTSpiceBatch.py to the collection of tools

* Version 0.3
A version of LTSteps that can be imported to use in a higher level script 

* Version 0.2
Adding LTSteps.py and Histogram.py

* Version 0.1 
First commit to the bitbucket repository.
