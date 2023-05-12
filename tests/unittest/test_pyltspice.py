#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        test_pyltspice.py
# Purpose:     Tool used to launch LTSpice simulation in batch mode. Netlsts can
#              be updated by user instructions
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
"""
@author:        Nuno Brum
@copyright:     Copyright 2022
@credits:       nunobrum

@license:       GPLv3
@maintainer:    Nuno Brum
@email:         me@nunobrum.com

@file:          test_pyltspice.py
@date:          2022-09-19

@note           pyltspice ltsteps + sim_commander + raw_read unit test
                  run ./test/unittest/test_pyltspice
"""

import os  # platform independent paths
# ------------------------------------------------------------------------------
# Python Libs
import sys  # python path handling
import unittest  # performs test

#
# Module libs

sys.path.append(
    os.path.abspath((os.path.dirname(os.path.abspath(__file__)) + "/../../")))  # add project root to lib search path
from PyLTSpice.log.ltsteps import LTSpiceLogReader
from PyLTSpice.sim.sim_batch import SimCommander
from PyLTSpice.raw.raw_read import RawRead
from PyLTSpice.sim.spice_editor import SpiceEditor
from PyLTSpice.sim.sim_runner import SimRunner
from PyLTSpice.sim.ltspice_simulator import LTspice

def has_ltspice_detect():
    from PyLTSpice.sim.ltspice_simulator import LTspice
    ltspice = LTspice
    return isinstance(ltspice.spice_exe, list) and os.path.exists(ltspice.spice_exe[0])


# ------------------------------------------------------------------------------
has_ltspice = has_ltspice_detect()
skip_ltspice_tests = not has_ltspice
print("skip_ltspice_tests", skip_ltspice_tests)
test_dir = '../' if os.path.abspath(os.curdir).endswith('unittest') else './tests/'
print("test_dir", test_dir)
# ------------------------------------------------------------------------------

# if has_ltspice:
#    os.chdir(os.path.abspath((os.path.dirname(os.path.abspath(__file__)))))

class test_pyltspice(unittest.TestCase):
    """Unnittesting PyLTSpice"""
    # *****************************
    @unittest.skipIf(skip_ltspice_tests, "Skip if not in windows environment")
    def test_batch_test(self):
        """
        @note   inits class
        """
        # prepare
        self.sim_files = []
        self.measures = {}

        def processing_data(raw_file, log_file):
            print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))
            self.sim_files.append((raw_file, log_file))

        # select spice model
        LTC = SimCommander(test_dir + "Batch_Test.asc")
        LTC.set_parameters(res=0, cap=100e-6)
        LTC.set_component_value('R2', '2k')  # Modifying the value of a resistor
        LTC.set_component_value('R1', '4k')
        LTC.set_element_model('V3', "SINE(0 1 3k 0 0 0)")  # Modifying the
        LTC.set_component_value('XU1:C2', 20e-12)  # modifying a
        # define simulation
        LTC.add_instructions(
                "; Simulation settings",
                ".param run = 0",
                # ".step dec param freq 10k 1Meg 10",
        )

        for opamp in ('AD712', 'AD820'):
            LTC.set_element_model('XU1', opamp)
            for supply_voltage in (5, 10, 15):
                LTC.set_component_value('V1', supply_voltage)
                LTC.set_component_value('V2', -supply_voltage)
                # overriding the automatic netlist naming
                run_netlist_file = "{}_{}_{}.net".format(LTC.circuit_file.name, opamp, supply_voltage)
                LTC.run(run_filename=run_netlist_file, callback=processing_data)

        LTC.wait_completion()

        # Sim Statistics
        print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))
        self.assertEqual(LTC.okSim, 6)
        self.assertEqual(LTC.runno, 6)

        # check
        LTC.reset_netlist()
        LTC.set_element_model('V3', "AC 1 0")
        LTC.add_instructions(
                "; Simulation settings",
                ".ac dec 30 1 10Meg",
                ".meas AC GainAC MAX mag(V(out)) ; find the peak response and call it ""Gain""",
                ".meas AC FcutAC TRIG mag(V(out))=GainAC/sqrt(2) FALL=last"
        )

        raw_file, log_file = LTC.run(run_filename="no_callback.net").wait_results()
        LTC.wait_completion()
        print("no_callback", raw_file, log_file)
        log = LTSpiceLogReader(log_file)
        for measure in log.get_measure_names():
            print(measure, '=', log.get_measure_value(measure))
        self.assertEqual(log.get_measure_value('fcutac'), 8479370.0)
        self.assertEqual(str(log.get_measure_value('vout1m')), '6.02059dB,-5.37934e-08°')
        self.assertEqual(log.get_measure_value('vout1m').mag, 6.02059)

    @unittest.skipIf(skip_ltspice_tests, "Skip if not in windows environment")
    def test_run_from_spice_editor(self):
        """Run command on SpiceEditor"""
        LTC = SimRunner()
        # select spice model
        LTC.create_netlist("../../tests/testfile.asc")
        netlist = SpiceEditor("../../tests/testfile.net")
        # set default arguments
        netlist.set_parameters(res=0.001, cap=100e-6)
        # define simulation
        netlist.add_instructions(
                "; Simulation settings",
                # [".STEP PARAM Rmotor LIST 21 28"],
                ".TRAN 3m",
                # ".step param run 1 2 1"
        )
        # do parameter sweep
        for res in range(5):
            # LTC.runs_to_do = range(2)
            netlist.set_parameters(ANA=res)
            raw, log = LTC.run(netlist).wait_results()
            print("Raw file '%s' | Log File '%s'" % (raw, log))
        # Sim Statistics
        print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))

    @unittest.skipIf(skip_ltspice_tests, "Skip if not in windows environment")
    def test_sim_runner(self):
        """SimRunner and SpiceEditor singletons"""
        # Old legacy class that merged SpiceEditor and SimRunner
        def callback_function(raw_file, log_file):
            print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))

        LTC = SimRunner()
        SE = SpiceEditor("../../tests/testfile.net")
        #, parallel_sims=1)
        tstart = 0
        for tstop in (2, 5, 8, 10):
            tduration = tstop - tstart
            SE.add_instruction(".tran {}".format(tduration), )
            if tstart != 0:
                SE.add_instruction(".loadbias {}".format(bias_file))
                # Put here your parameter modifications
                # LTC.set_parameters(param1=1, param2=2, param3=3)
            bias_file = "sim_loadbias_%d.txt" % tstop
            SE.add_instruction(".savebias {} internal time={}".format(bias_file, tduration))
            tstart = tstop
            LTC.run(SE, callback=callback_function)

        SE.reset_netlist()
        SE.add_instruction('.ac dec 40 1m 1G')
        SE.set_component_value('V1', 'AC 1 0')
        LTC.run(SE, callback=callback_function)
        LTC.wait_completion()

    @unittest.skipIf(False, "Execute All")
    def test_ltsteps_measures(self):
        """LTSteps Measures from Batch_Test.asc"""
        assert_data = {
            'vout1m'   : [
                -0.0186257,
                -1.04378,
                -1.64283,
                -0.622014,
                1.32386,
                -1.35125,
                -1.88222,
                1.28677,
                1.03154,
                0.953548,
                -0.192821,
                -1.42535,
                0.451607,
                0.0980979,
                1.55525,
                1.66809,
                0.11246,
                0.424023,
                -1.30035,
                0.614292,
                -0.878185,
            ],
            'vin_rms'  : [
                0.706221,
                0.704738,
                0.708225,
                0.707042,
                0.704691,
                0.704335,
                0.704881,
                0.703097,
                0.70322,
                0.703915,
                0.703637,
                0.703558,
                0.703011,
                0.702924,
                0.702944,
                0.704121,
                0.704544,
                0.704193,
                0.704236,
                0.703701,
                0.703436,
            ],
            'vout_rms' : [
                1.41109,
                1.40729,
                1.41292,
                1.40893,
                1.40159,
                1.39763,
                1.39435,
                1.38746,
                1.38807,
                1.38933,
                1.38759,
                1.38376,
                1.37771,
                1.37079,
                1.35798,
                1.33252,
                1.24314,
                1.07237,
                0.875919,
                0.703003,
                0.557131,

            ],
            'gain'     : [
                1.99809,
                1.99689,
                1.99502,
                1.99271,
                1.98894,
                1.98432,
                1.97814,
                1.97336,
                1.97387,
                1.97372,
                1.97202,
                1.9668,
                1.95973,
                1.95012,
                1.93184,
                1.89246,
                1.76445,
                1.52284,
                1.24379,
                0.999007,
                0.792014,
            ],
            'period'   : [
                0.000100148,
                7.95811e-005,
                6.32441e-005,
                5.02673e-005,
                3.99594e-005,
                3.1772e-005,
                2.52675e-005,
                2.01009e-005,
                1.59975e-005,
                1.27418e-005,
                1.01541e-005,
                8.10036e-006,
                6.47112e-006,
                5.18241e-006,
                4.16639e-006,
                3.37003e-006,
                2.75114e-006,
                2.26233e-006,
                1.85367e-006,
                1.50318e-006,
                1.20858e-006,

            ],
            'period_at': [
                0.000100148,
                7.95811e-005,
                6.32441e-005,
                5.02673e-005,
                3.99594e-005,
                3.1772e-005,
                2.52675e-005,
                2.01009e-005,
                1.59975e-005,
                1.27418e-005,
                1.01541e-005,
                8.10036e-006,
                6.47112e-006,
                5.18241e-006,
                4.16639e-006,
                3.37003e-006,
                2.75114e-006,
                2.26233e-006,
                1.85367e-006,
                1.50318e-006,
                1.20858e-006,
            ]
        }
        if has_ltspice:
            LTC = SimCommander("../../tests/Batch_Test.asc")
            raw_file, log_file = LTC.run().wait_results()
            print(raw_file, log_file)
        else:
            log_file = test_dir + "Batch_Test_1.log"
        log = LTSpiceLogReader(log_file)
        # raw = RawRead(raw_file)
        for measure in assert_data:
            print("measure", measure)
            for step in range(log.step_count):
                self.assertEqual(log.get_measure_value(measure, step), assert_data[measure][step])

                print(log.get_measure_value(measure, step), assert_data[measure][step])

    @unittest.skipIf(False, "Execute All")
    def test_operating_point(self):
        """Operating Point Simulation Test"""
        if has_ltspice:
            LTC = SimCommander("../../tests/DC op point.asc")
            raw_file, log_file = LTC.run().wait_results()
        else:
            raw_file = test_dir + "DC op point_1.raw"
            # log_file = test_dir + "DC op point_1.log"
        raw = RawRead(raw_file)
        traces = [raw.get_trace(trace)[0] for trace in raw.get_trace_names()]

        self.assertListEqual(traces, [1.0, 0.5, 4.999999873689376e-05, 4.999999873689376e-05, -4.999999873689376e-05], "Lists are different")

    @unittest.skipIf(False, "Execute All")
    def test_operating_point_step(self):
        """Operating Point Simulation with Steps """
        if has_ltspice:
            LTC = SimCommander("../../tests/DC op point - STEP.asc")
            raw_file, log_file = LTC.run().wait_results()
        else:
            raw_file = test_dir + "DC op point - STEP_1.raw"
        raw = RawRead(raw_file)
        vin = raw.get_trace('V(in)')

        for i, b in enumerate(('V(in)', 'V(b4)', 'V(b3)', 'V(b2)', 'V(b1)', 'V(b0)'),):
            meas = raw.get_trace(b)
            for step in range(raw.nPoints):
                self.assertEqual(meas[step], vin[step] * 2**-i)

    @unittest.skipIf(False, "Execute All")
    def test_transient(self):
        """Transient Simulation test """
        if has_ltspice:
            LTC = SimCommander("../../tests/TRAN.asc")
            raw_file, log_file = LTC.run().wait_results()
        else:
            raw_file = test_dir + "TRAN_1.raw"
            log_file = test_dir + "TRAN_1.log"
        raw = RawRead(raw_file)
        log = LTSpiceLogReader(log_file)
        vout = raw.get_trace('V(out)')
        meas = ('t1', 't2', 't3', 't4', 't5',)
        time = (1e-3, 2e-3, 3e-3, 4e-3, 5e-3,)
        for m, t in zip(meas, time):
            log_value = log.get_measure_value(m)
            raw_value = vout.get_point_at(t)
            print(log_value, raw_value, log_value - raw_value)
            self.assertAlmostEqual(log_value, raw_value, 2, "Mismatch between log file and raw file")

    @unittest.skipIf(False, "Execute All")
    def test_transient_steps(self):
        """Transient simulation with stepped data."""
        if has_ltspice:
            LTC = SimCommander("../../tests/TRAN - STEP.asc")
            raw_file, log_file = LTC.run().wait_results()
        else:
            raw_file = test_dir + "TRAN - STEP_1.raw"
            log_file = test_dir + "TRAN - STEP_1.log"

        raw = RawRead(raw_file)
        log = LTSpiceLogReader(log_file)
        vout = raw.get_trace('V(out)')
        meas = ('t1', 't2', 't3', 't4', 't5',)
        time = (1e-3, 2e-3, 3e-3, 4e-3, 5e-3,)
        for m, t in zip(meas, time):
            print(m)
            for step, step_dict in enumerate(raw.steps):
                log_value = log.get_measure_value(m, step)
                raw_value = vout.get_point_at(t, step)
                print(step, step_dict, log_value, raw_value, log_value - raw_value)
                self.assertAlmostEqual(log_value, raw_value, 2, f"Mismatch between log file and raw file in step :{step_dict} measure: {m} ")

    @unittest.skipIf(False, "Execute All")
    def test_ac_analysis(self):
        """AC Analysis Test"""
        from numpy import pi, angle
        if has_ltspice:
            LTC = SimCommander("../../tests/AC.asc")
            raw_file, log_file = LTC.run().wait_results()
            R1 = LTC.get_component_floatvalue('R1')
            C1 = LTC.get_component_floatvalue('C1')
        else:
            raw_file = test_dir + "AC_1.raw"
            log_file = test_dir + "AC_1.log"
            R1 = 100
            C1 = 10E-6
        # Compute the RC AC response with the resistor and capacitor values from the netlist.
        raw = RawRead(raw_file)
        vout_trace = raw.get_trace('V(out)')
        vin_trace = raw.get_trace('V(in)')
        for point, freq in enumerate(raw.axis):
            vout1 = vout_trace.get_point_at(freq)
            vout2 = vout_trace.get_point(point)
            vin = vin_trace.get_point(point)
            self.assertEqual(vout1, vout2)
            self.assertEqual(abs(vin), 1)
            # Calculate the magnitude of the answer Vout = Vin/(1+jwRC)
            h = vin/(1 + 2j * pi * freq * R1 * C1)
            self.assertAlmostEqual(abs(vout1), abs(h), 5, f"Difference between theoretical value ans simulation at point {point}")
            self.assertAlmostEqual(angle(vout1), angle(h), 5, f"Difference between theoretical value ans simulation at point {point}")

    @unittest.skipIf(False, "Execute All")
    def test_ac_analysis_steps(self):
        """AC Analysis Test with steps"""
        from numpy import pi, angle
        if has_ltspice:
            LTC = SimCommander("../../tests/AC - STEP.asc")
            raw_file, log_file = LTC.run().wait_results()
            C1 = LTC.get_component_floatvalue('C1')
        else:
            raw_file = test_dir + "AC - STEP_1.raw"
            log_file = test_dir + "AC - STEP_1.log"
            C1 = 159.1549e-6  # 159.1549uF
        # Compute the RC AC response with the resistor and capacitor values from the netlist.
        raw = RawRead(raw_file)
        vin_trace = raw.get_trace('V(in)')
        vout_trace = raw.get_trace('V(out)')
        for step, step_dict in enumerate(raw.steps):
            R1 = step_dict['r1']
            # print(step, step_dict)
            for point in range(0, raw.get_len(step), 10):  # 10 times less points
                print(point, end=' - ')
                vout = vout_trace.get_point(point, step)
                vin = vin_trace.get_point(point, step)
                freq = raw.axis.get_point(point, step)
                # Calculate the magnitude of the answer Vout = Vin/(1+jwRC)
                h = vin/(1 + 2j * pi * freq * R1 * C1)
                # print(freq, vout, h, vout - h)
                self.assertAlmostEqual(abs(vout), abs(h), 5,
                                       f"Difference between theoretical value ans simulation at point {point}:")
                self.assertAlmostEqual(angle(vout), angle(h), 5,
                                       f"Difference between theoretical value ans simulation at point {point}")

    # 
    # def test_pathlib(self):
    #     """pathlib support"""
    #     import pathlib
    #     DIR = pathlib.Path("../tests")
    #     raw_file = DIR / "AC - STEP_1.raw"
    #     raw = RawRead(raw_file)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
# ------------------------------------------------------------------------------
