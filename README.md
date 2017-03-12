# README #

PySpicer is a toolchain of python utilities design to interact with LTSpice Electronic Simulator.

### What is contained in this repository ###

* __LTSteps.py__ 
An utility that extracts from LTSpice output files data, and formats it for import in a spreadsheet,s uch like Excel or Calc. 

* __LTSpiceRaw_Reader.py__
A pure python class that serves to read raw files into a python class.

* __Histogram.py__
Uses numpy and matplotlib to create an histogram and calculate the sigma deviations. This is useful for Monte-Carlo analysis. 

* __LTSpiceBatch.py__
This is a script to launch LTSpice Simulations. This is useful because:

- Can overcome the limitation of only stepping 3 parameters
- Different types of simulations .TRAN .AC .NOISE can be run in a single batch
- The RAW Files are smaller and easier to treat
- When used with the LTSpiceRaw_Reader.py and LTSteps.py, validattion of the circuit can be done automatically

Different models can be simulation in a single batch.

The principle of operation is the following,:
  1. Add to the Spice circuit a .INC sim_settings.lib  . In this include simulation directives are written by the script per each simulation call.

  2. Use the python script to update the simulation directives and call LTSpice to run the simulation in command line.

  3. When the simulation is complete, the simulation results are renamed according to user guidance.

Note: It only works with Windows based installations.

### To whom do I talk to? ###

* Tools website : [http://www.nunobrum.com/ltspicer2.html](http://www.nunobrum.com/ltspicer2.html)
* Repo owner : [me@nunobrum.com](me@nunobrum.com) 
* Alternative contact : nuno.brum@gmail.com

### History ###
* Version 0.4
Added LTSpiceBatch.py to the collection of tools

* Version 0.3
A version of LTSteps that can be imported to use in a higher level script 

* Version 0.2
Adding LTSteps.py and Histogram.py

* Version 0.1 
First commit to the bitbucket repository.
