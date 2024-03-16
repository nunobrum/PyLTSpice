Reading Log Information
========================

This module defines a class that can be used to parse LTSpice log files where the information about .STEP
information is written.

There are two possible usages of this module, either programmatically by running the utility
:doc:`../utilities/LTSteps`, or by accessing data through the class as exemplified here:

.. code-block:: python

	from PyLTSpice.log.ltsteps import LTSpiceLogReader

	data = LTSpiceLogReader("Batch_Test_AD820_15.log")

	print("Number of steps  :", data.step_count)
	
	# Get the names of the variables that were stepped, and the measurements taken
	step_names = data.get_step_vars()
	meas_names = data.get_measure_names()

	# Print headers for a table with steps and measurements
	print('\t'.join([f"{step}" for step in step_names]), end='\t')		
	print('\t'.join([f"{name}" for name in meas_names]), end='\n')

	# Print the data.  First values of all step variables, then values of the measurements
	for i in range(data.step_count):
		print('\t'.join([f"{data[step][i]}" for step in step_names]), end='\t')
		print('\t'.join([f"{data[name][i]}" for name in meas_names]), end='\n')

	print("Total number of measurements found :", data.measure_count)

For more information, see :py:class:`PyLTSpice.log.ltsteps.LTSpiceLogReader`