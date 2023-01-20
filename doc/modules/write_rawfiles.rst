Writing Raw Files
=================

The RawWrite class can be used to generate .RAW-files with generated or calculated data.

The functionality is limited to adding traces with a single series of values.  Stepped data (like with a DC sweep) is not supported.

| First, generate your trace data, e.g. using numpy.
| Then, make a Trace object from this data.
| Then, add all Trace objects to the RawWrite object.
| Lastly, write the data to a file on disk.

The following example writes a RAW file with a 3 milliseconds transient simulation,
containing a 10kHz sine and a 9.997kHz cosine wave.

.. code-block::

	import numpy as np
	from PyLTSpice import Trace, RawWrite

	LW = RawWrite()

	tx = Trace('time', np.arange(0.0, 3e-3, 997E-11))
	vy = Trace('N001', np.sin(2 * np.pi * tx.data * 10000))
	vz = Trace('N002', np.cos(2 * np.pi * tx.data * 9970))

	LW.add_trace(tx)
	LW.add_trace(vy)
	LW.add_trace(vz)

	LW.save("test_sincos.raw")


For more information, see :

- :doc:`../varia/raw_file`
- :py:class:`PyLTSpice.raw_write.RawWrite`
- :py:class:`PyLTSpice.raw_write.Trace`
