histogram
=============
This module uses matplotlib to plot an histogram of a gaussian distribution and calculates the project n-sigma interval.

This module is installed on the Scripts folder on your python installation folder or virtual environment.
Add the Scripts path to your PATH environment variable in order to be able to use this tool in any other location on
your system.

The data can either collected from the clipboard or from a text file. Use the following command line text to call
this module.

.. code-block:: text

    histogram [options] [data_file] TRACE

The help can be obtained by calling the script without arguments

.. code-block:: text

    Usage: histogram [options] LOG_FILE TRACE

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -s SIGMA, --sigma=SIGMA
                            Sigma to be used in the distribution fit. Default=3
      -n NBINS, --nbins=NBINS
                            Number of bins to be used in the histogram. Default=20
      -c FILTERS, --condition=FILTERS
                            Filter condition writen in python. More than one
                            expression can be added but each expression should be
                            preceded by -c. EXAMPLE: -c V(N001)>4 -c parameter==1
                            -c  I(V1)<0.5
      -f FORMAT, --format=FORMAT
                            Format string for the X axis. Example: -f %3.4f
      -t TITLE, --title=TITLE
                            Title to appear on the top of the histogram.
      -r RANGE, --range=RANGE
                            Range of the X axis to use for the histogram in the
                            form min:max. Example: -r -1:1
      -C, --clipboard       If the data from the clipboard is to be used.
      -i IMAGEFILE, --image=IMAGEFILE
                            Name of the image File. extension 'png'

