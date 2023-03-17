
import os
import glob

import numpy as np
import matplotlib.pyplot as plt
from tolerance import Tolerance

from PyLTSpice.LTSpice_RawRead import LTSpiceRawRead


os.chdir("sim")

##########   L O A D   C I R C U I T   ##########

LTC = Tolerance("../tolerance_demo.asc")

# LTC.run_nominal()

##########   D E F I N E   T O L E R A N C E S   ##########

LTC.set_deviation("V2", 0.003 )         # 3 mV deviation possible on voltage reference

LTC.set_tolerance(["R1", "R2"], 1)      # 1% tolerance on opamp resistors

LTC.set_deviation("V3", 80e-6 )         # 80uV max input offset voltage for LT1028

##########   R U N   S I M U L A T I O N S   ##########


# LTC.run_monte_carlo( 500 )

LTC.run_gauss( 500, 50 )

# LTC.run_worstcase()

LTC.wait_completion()

##########   L O A D   R E S U L T S    ##########

np_data = None                              # we'll collect all data in this variable

for name in glob.glob("tolerance_demo_gs_*.raw"):       # read all the .raw files
    lt = LTSpiceRawRead( name, ("run", "V(out)") )      # read the V(out) trace
    
    if np_data is None:                                 # first file ?
        np_data = lt.get_wave("V(out)")                 # get the data as numpy array
    else:
        np_data = np.append( np_data, lt.get_wave("V(out)") )   # append to existing data if not first file

##########  P L O T   R E S U L T S   ##########

plt.hist(np_data, 20, label="V(out) tolerance" )
plt.show()

