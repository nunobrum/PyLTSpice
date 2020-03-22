# -------------------------------------------------------------------------------
# Name:        Histogram.py
# Purpose:     Make an histogram plot based on the results of LTSpice.py
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     17-01-2017
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
opts.add_option('-c', "--condition", action="append", type="string", dest="filters",
                help="Filter condition writen in python. More than one expression can be added but each expression should be preceded by -f.\n" +
                     "EXAMPLE: -c V(N001)>4 -c parameter==1 -c  I(V1)<0.5" )
opts.add_option('-f', "--format", action="store", type="string", dest="format", help="Format string for the X axis. Example: -f %3.4f")
#opts.add_option('-p', "--scaling",action="store", type="string", dest="prescaling", help="Prescaling function to be applied to the input value.")
opts.add_option('-t', "--title", action="store", type="string", dest="title", help="Title to appear on the top of the histogram.")
opts.add_option('-r', "--range", action="store", type="string", dest="range", help="Range of the X axis to use for the histogram in the form min:max. Example: -r -1:1")
opts.add_option('-C', "--clipboard", action="store_true", dest="clipboard", help="If the data from the clipboard is to be used.")
#opts.add_option('-x', "--xname", action="store", dest="xname", help="Name for the variable displayed")
opts.add_option('-i', "--image", action="store", type="string", dest="imagefile", help="Name of the image File. extension 'png'")

(options, args) = opts.parse_args()

values = []


if options.clipboard:
    try:
        import clipboard
    except ImportError:
        print("Failed to load clipboard package. Use PiP to install it.")
        exit(1)
    if len(args) > 0:
        TRACE = args[-1]
    else:
        TRACE = "var"
    text = clipboard.paste()
    for line in text.split('\n'):
        try:
            values.append(float(line))
        except ValueError:
            print("Failed to process ")
            print(line)
elif len(args)==0:
    opts.print_help()
    exit(-1)
else:
    if len(args) < 2:
        opts.error("Wrong number of parameters. Need to give the filename and the trace.")
        opts.print_help()
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
    TRACE = args[1]
    logfile = args[0]

    if not options.filters is None:
        print("Filters Applied:", options.filters)
    else:
        print("No filters defined")

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


    if (options.filters is None) or (len(options.filters) == 0):
        for line in log:
            #print(line)
            vs = line.split('\t')
            values.append(float(vs[sav_col]))
    else:
        for line in log:
            vs = map(float,line.split('\t'))
            env = dict(zip(vars,vs))

            for expression in options.filters:
                test = eval(expression, None, env)
                if test == False:
                    break
            else:
                values.append(float(env[TRACE]))


    log.close()

if len(values) == 0:
    print("No elements found")
elif len(values) < options.nbins:
    print("Not enough elements for an histogram")
else:
    x = np.array(values, dtype=float)
    mu = x.mean()
    mn = x.min()
    mx = x.max()
    sd = np.std(x)
    sigmin = mu - options.sigma*sd
    sigmax = mu + options.sigma*sd

    if options.range is None:
        # Automatic calculation of the range
        axisXmin = mu - (options.sigma+1)*sd
        axisXmax = mu + (options.sigma + 1) * sd

        if mn < axisXmin:
            axisXmin = mn

        if mx > axisXmax:
            axisXmax = mx
    else:
        try:
            smin, smax = options.range.split(":")
            axisXmin = float(smin)
            axisXmax = float(smax)
        except:
            opts.error("Invalid range setting")
            exit(-1)
    if options.format:
        fmt = options.format
    else:
        fmt = "%f"

    print("Collected %d elements" % len(values))
    print("Distributing in %d bins" % options.nbins)
    print("Minimum is " + fmt % mn)
    print("Maximum is " + fmt % mx)
    print("Mean is " + fmt % mu)
    print("Standard Deviation is " + fmt % sd)
    print(("Sigma %d boundaries are " + fmt + " and " + fmt) % (options.sigma, sigmin, sigmax))
    n, bins, patches = plt.hist(x, options.nbins, normed=True, facecolor='green', alpha=0.75, range=(axisXmin, axisXmax))
    axisYmax = n.max() * 1.1

    # add a 'best fit' line
    if hasattr(mlab, 'normpdf'):  # This was deprecated on version 2.2 of mlab
        y = mlab.normpdf(bins, mu, sd)
    else:
        from scipy.stats import norm
        y = norm.pdf(bins, mu, sd)

    l = plt.plot(bins, y, 'r--', linewidth=1)
    plt.axvspan(mu - options.sigma*sd, mu + options.sigma*sd, alpha=0.2, color="cyan")
    plt.xlabel(TRACE)
    plt.ylabel('Distribution [Normalised]')

    if options.title is None:
        title = (r'$\mathrm{Histogram\ of\ %s:}\ \mu='+fmt+r',\ stdev='+fmt+r',\ \sigma=%d$') % (TRACE, mu, sd, options.sigma)
    else:
        title = options.title
    plt.title(title)

    plt.axis([axisXmin, axisXmax, 0, axisYmax ])
    plt.grid(True)
    if options.imagefile is not None:
        plt.savefig(options.imagefile)
    else:
        plt.show()