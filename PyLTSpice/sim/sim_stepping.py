#!/usr/bin/env python

# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        sim_stepping.py
# Purpose:     Spice Simulation Library intended to automate the exploring of
#              design corners, try different models and different parameter
#              settings.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     31-07-2020
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"

import logging
_logger = logging.getLogger("PyLTSpice.SimStepper")
_logger.info("This module is maintained for compatibility reasons."
             " Please use the new SimStepper class from PyLTSpice.sim.sim_stepping instead")

from spicelib.sim.sim_stepping import SimStepper


if __name__ == "__main__":
    from PyLTSpice.utils.sweep_iterators import *

    test = SimStepper("../../tests/DC sweep.asc")
    test.verbose = True
    test.set_parameter('R1', 3)
    test.add_param_sweep("res", [10, 11, 9])
    test.add_value_sweep("R1", sweep_log(0.1, 10))
    # test.add_model_sweep("D1", ("model1", "model2"))
    test.run_all()
    print("Finished")
    exit(0)
