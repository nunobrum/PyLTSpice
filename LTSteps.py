#-------------------------------------------------------------------------------
# Name:        LTSteps.py
# Purpose:     Process LTSpice output files and align data for usage in a spread-
#              sheet tool such as Excel, or Calc.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     19-05-2014
# Licence:     Free
#-------------------------------------------------------------------------------

__author__ = "Nuno Canto Brum <me@nunobrum.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"

import re
import os
import sys

def valid_extension(f):
    return f.endswith('.txt') or f.endswith('.log') or f.endswith('.mout')

if len(sys.argv)>1:
    filename = sys.argv[1]
else:
    newer_date = 0
    for f in os.listdir():
        date = os.path.getmtime(f)
        if date > newer_date and valid_extension(f):
            newer_date = date
            filename = f


fin = open(filename,'r')
if filename.endswith('txt'):
    fname_out = filename.strip('txt')+'tsv'
elif filename.endswith('log'):
    fname_out = filename.strip('log')+'tlog'
elif filename.endswith('mout'):
    fname_out = filename.strip('mout')+'tmout'
else:
    print("Error in file type")
    exit(-1)

print("Processing File %s" % filename)
print("Creating File %s" % fname_out)
fout = open(fname_out, 'w')

if filename.endswith('txt'):
    print("Processing Data File")
    headers = fin.readline()
    # writing header
    go_header = True
    regx= re.compile("Step Information: ([\w=\d\. -]+) +\(Run: (\d*)/\d*\)\n")
    for line in fin:
        if line.startswith("Step Information:"):
            match = regx.match(line)
            #print(line, end="")
            if match:
                #print(match.groups())
                step, run_no = match.groups()
                #print(step, line, end="")
            params=[]
            for param in step.split():
                params.append(param.split('=')[1])
            param_values ="\t".join(params)

            if go_header:
                params=[]
                for param in step.split():
                    params.append(param.split('=')[0])
                param_header ="\t".join(params)
                fout.write("Run\t%s\t%s" % (param_header, headers))
                print("Run\t%s\t%s" % (param_header, headers))
                go_header=False
            #print("%s\t%s"% (run_no, param_values))

        else:
            fout.write("%s\t%s\t%s"% (run_no, param_values, line))
else:
    dataset = {}
    headers = []
    measurements = []
    dataname = None

    if filename.endswith("log"):
        step_count = 0
        stepset= {}
        steps = []
        print("Processing LOG file")
        # wait for the step information
        for line in fin:
            if line.startswith(".step "):
                break
        while line:
            if line.startswith(".step"):
                #print(line)
                step_count += 1
                tokens = line.strip('\n').split(' ')
                for tok in tokens[1:]:
                    lhs,rhs = tok.split("=")
                    ll = stepset.get(lhs,None)
                    if ll:
                        ll.append(rhs)
                    else:
                        stepset[lhs] = [rhs]
            elif line.startswith("Measurement:"):
                break
            line = fin.readline()
    else:
        print("Processing MOUT" )
        stepset = {}

    #print("Reading Measurements")
    measure_count = 0
    while line:
        line = line.strip('\n')
        if line.startswith("Measurement: "):
            if dataname:
                #store the info
                if len(measurements):
                    print("Storing Measurement %s (count %d)" % (dataname, len(measurements)))
                    headers.append(dataname)
                    dataset[dataname] = (param, measurements)
                measurements = []
            dataname = line[13:]
            print("Reading Measurement %s" % line[13:])
        else:
            tokens = line.split("\t")
            if len(tokens)>=2:
                try:
                    nstep=int(tokens[0])
                    measurements.append(tokens[1:])
                    measure_count += 1
                except:
                    param = "\t".join([dataname]+ tokens [2:])
            else:
                print("->",line)

        line = fin.readline() # advance to the next line

                #print(tokens)
    print("Storing Measurement %s" % dataname)
    if len(measurements):
        dataset[dataname] = (param, measurements)
    headers.append(dataname)
    print("%d measurements" % len(headers))
    print("Identified %d steps, read %d measurements" % (step_count, measure_count))
    print("Writing Data in %s" % fname_out)

    #fout.write("%s\t%s\n" % ("\t".join(stepset.keys()), "\t\t".join(headers)))
    meas_headers = ["\t".join(dataset[param][0:1]) for param in headers]
    fout.write("step\t%s\t%s\n" % ("\t".join(stepset.keys()),"\t".join(meas_headers)))
    for index in range(step_count):
        step_data = [stepset[param][index] for param in stepset.keys()]
        meas_data = [dataset[param][1][index] for param in headers]
        tokens = ["\t".join(tok) for tok in meas_data]
        fout.write("%d\t%s\t%s\n" % (index + 1,"\t".join(step_data), "\t".join(tokens)))


fin.close()
fout.close()
#input("Press Enter to Continue")

