# -------------------------------------------------------------------------------
# Name:        LTSteps.py
# Purpose:     Process LTSpice output files and align data for usage in a spread-
#              sheet tool such as Excel, or Calc.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     19-05-2014
# Licence:     Free
# -------------------------------------------------------------------------------

__author__ = "Nuno Canto Brum <me@nunobrum.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"

#!/usr/bin/env python
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from optparse import OptionParser

usage = "usage: %prog [options] LOG_FILE TRACE"
opts = OptionParser(usage=usage, version="%prog 0.1")
#opts.add_option('v', "var", action="store", type="string", dest="trace", help="The trace to be used in the histogram")
opts.add_option('-s',"--sigma", action ="store", type="int", dest="sigma", default=3, help="Sigma to be used in the distribution fit. Default=3")
opts.add_option('-n', "--nbins", action="store",  type="int", dest="nbins", default=20, help="Number of bins to be used in the histogram. Default=20")
opts.add_option('-f', "--filter", action="append", type="string", dest="filters", help="Filter to a given setting step parameter")

(options, args) = opts.parse_args()

if not options.filters is None:
    print(options.filters)
else:
    print("No filters defined")

if len(args)==2:
    TRACE = args[1]
    logfile = args[0]

else :
    opts.error("Wrong number of parameters")
    exit(-1)
    # if (len(args)==1): # This will search for the most recent file
    #     newer_date = 0
    #     filename = None
    #     for f in os.listdir():
    #         date = os.path.getmtime(f)
    #         if date > newer_date and f.endswith(".tlog"):
    #             newer_date = date
    #             filename = f
    #     if filename == None:
    #         opts.error("A LOG_FILE should be given")


log = open(logfile,'r')
header = log.readline().rstrip('\n')
vars = header.split('\t')
try:
    sav_col = vars.index(TRACE)
except ValueError:
    log.close()
    print("File '%s' doesn't have trace '%s'" % (logfile, TRACE))
    print("LOG FILE contains %s" % vars)
    exit(-1)

filters = {}
for filter in options.filters:
    trace, value = filter.split("=", 2)
    try:
        filt_col = vars.index(trace)
    except ValueError:
        print ("Trace '%s' is not known." % trace)
        continue

    filters[filt_col] = float(value)


values = []
if len(filters) == 0:
    for line in log:
        #print(line)
        vs = line.split('\t')
        values.append(float(vs[sav_col]))
else:
    for line in log:
        vs = line.split('\t')

        for col_filt, value in  filters.items():
            if float(vs[col_filt]) != value:
                break
        else:
            values.append(float(vs[sav_col]))

log.close()
if len(values) == 0:
    print("No elements found")
elif len(values) < options.nbins:
    print("Not enough elements for an histogram")
else:
    x = np.array(values, dtype=float) * 100
    mu = x.mean()
    mn = x.min()
    mx = x.max()
    sd = np.std(x)
    sigmin = mu - options.sigma*sd
    sigmax = mu + options.sigma*sd
    axisXmin = mu - (options.sigma+1)*sd
    axisXmax = mu + (options.sigma + 1) * sd

    print("Distributing in %d bins" % options.nbins)
    print("Minimum is %f" % mn)
    print("Maximum is %f" % mx)
    print("Mean is %f", mu)
    print("Standard Deviation is %f" % sd)
    print("Sigma %d boundaries are %f and %f" % (options.sigma, sigmin, sigmax))
    n, bins, patches = plt.hist(x, options.nbins, normed=True, facecolor='green', alpha=0.75, range=(axisXmin, axisXmax))
    axisYmax = n.max() * 1.1

    # add a 'best fit' line
    y = mlab.normpdf( bins, mu, sd)
    l = plt.plot(bins, y, 'r--', linewidth=1)
    plt.axvspan(mu - options.sigma*sd, mu + options.sigma*sd, alpha=0.2, color="red")
    plt.xlabel(TRACE)
    plt.ylabel('Probability')
    plt.title(r'$\mathrm{Histogram\ of\ %s:}\ \mu=%f,\ \sigma=%d$' % (TRACE, mu, options.sigma))
    plt.axis([axisXmin, axisXmax, 0, axisYmax ])
    plt.grid(True)
    plt.show()