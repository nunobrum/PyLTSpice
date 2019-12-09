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

### Using PiP Installer ###

 `pip install --upgrade PyLTSpice`

### Using GITHub ###

 `git clone https://github.com/nunobrum/PyLTSpice.git`
 
If using this method it would be good to add the path where you cloned the site to python path.

 `import sys`
 `sys.path.append(<path to PyLTSpice>)`

## How to use ##

### LTSpice_RawRead.py ###
Include the following line on your scripts

 `from PyLTSpice.LTSpiceRaw_Reader import LTSpiceRawRead`
 `LTR = LTSpiceRawRead(raw_filename)`

 `print(LTR.get_trace_names())`
 `print(LTR.get_raw_property())`

### LTSpice_Batch ###

 `from PyLTSpice.LTSpiceBatch import *`
 `LTC = LTCommander("testfile.asc")`

### LTSteps.py ###

 `python -m PyLTSpice.LTSteps <logfile or directory where last simulation was made>`

### Histogram.py ###

 `python -m PyLTSpice.Histogram` 

## To whom do I talk to? ##

* Tools website : [https://www.nunobrum.com/pyspicer.html](https://www.nunobrum.com/pyspicer.html)
* Repo owner : [me@nunobrum.com](me@nunobrum.com) 
* Alternative contact : nuno.brum@gmail.com

## History ##
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
