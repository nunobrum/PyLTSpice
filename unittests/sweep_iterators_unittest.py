# -*- coding: utf-8 -*-
"""
@author:        Andreas Kaeberlein
@copyright:     Copyright 2021
@credits:       AKAE

@license:       GPLv3
@maintainer:    Andreas Kaeberlein
@email:         andreas.kaeberlein@web.de

@file:          sweep_iterators_unittest.py
@date:          2021-01-09

@note           'sweep_iterators.py' unit test
                  run ./test/unit/sweep_iterators/sweep_iterators_unittest.py
"""



#------------------------------------------------------------------------------
# Python Libs
import sys        # python path handling
import os         # platform independent paths
import unittest   # performs test
#
# Module libs
sys.path.append(os.path.abspath((os.path.dirname(os.path.abspath(__file__)) + "/../")))   # add project root to lib search path
from PyLTSpice.utils.sweep_iterators import sweep, sweep_n, sweep_log, sweep_log_n, sweep_iterators  # Python Script under test
#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
class test_sweep_iterators(unittest.TestCase):

    #*****************************
    def setUp(self):
        """
        @note   set-ups test
        """
    #*****************************
    
    
    #*****************************
    def test_init(self):
        """
        @note   inits class
        """
        # prepare
        dut = sweep_iterators()
        # check
        self.assertEqual(dut.numTotalIterations, 0)
        self.assertEqual(dut.numCurrentIteration, 0)
        self.assertListEqual(dut.iteratorEntrys, [])
        self.assertListEqual(dut.idxForNextIter, [])


    #*****************************
    def test_add(self):
        """
        @note   add
        """
        # prepare
        dut = sweep_iterators()
        # add entries
        dut.add('elem1', [1, 2, 3])
        dut.add('elem2', [1.5, 1.8, 2.0])
        dut.add('elem3', ["entry1", "entry2"])
        # check
        self.assertEqual(dut.numTotalIterations, 18)
        self.assertEqual(dut.numCurrentIteration, 0)
        self.assertDictEqual(dut.iteratorEntrys[0], {'name': 'elem1', 'values': [1, 2, 3]})
        self.assertDictEqual(dut.iteratorEntrys[1], {'name': 'elem2', 'values': [1.5, 1.8, 2.0]})
        self.assertDictEqual(dut.iteratorEntrys[2], {'name': 'elem3', 'values': ['entry1', 'entry2']})
    #*****************************


    #*****************************
    def test_next(self):
        """
        @note   next
        """
        # prepare
        dut = sweep_iterators()
        dut.add('e1', [10])
        dut.add('e2', [1e-6, 3e-6])
        dut.add('e3', [1e3, 3e3, 5e3])
        # caclulate iterators & check
        self.assertEqual(dut.numTotalIterations, 6)
        self.assertEqual(dut.numCurrentIteration, 0)
        self.assertDictEqual(dut.next(), {'e1': 10, 'e2': 1e-06, 'e3': 1000.0})
        self.assertDictEqual(dut.next(), {'e1': 10, 'e2': 1e-06, 'e3': 3000.0})
        self.assertDictEqual(dut.next(), {'e1': 10, 'e2': 1e-06, 'e3': 5000.0})
        self.assertDictEqual(dut.next(), {'e1': 10, 'e2': 3e-06, 'e3': 1000.0})
        self.assertDictEqual(dut.next(), {'e1': 10, 'e2': 3e-06, 'e3': 3000.0})
        self.assertDictEqual(dut.next(), {'e1': 10, 'e2': 3e-06, 'e3': 5000.0})

    #*****************************
    def test_done(self):
        """
        @note   next
        """
        # prepare
        dut = sweep_iterators()
        dut.add('e1', [10])
        # check
        self.assertDictEqual(dut.next(), {'e1': 10})
        self.assertTrue(dut.done())
    #*****************************

#------------------------------------------------------------------------------

    def test_iterator_objects(self):
        """
        @note  iterator_objects
        """
        # *****************************
        # check
        self.assertListEqual(list(sweep(10)), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertListEqual(list(sweep(1, 8)), [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertListEqual(list(sweep(2, 8, 2)), [2, 4, 6, 8])
        self.assertListEqual(list(sweep(2, 8, -2)), [8, 6, 4, 2])
        self.assertListEqual(list(sweep(8, 2, 2)), [8, 6, 4, 2])
        self.assertListEqual(list(sweep(0.3, 1.1, 0.2)), [0.3, 0.5, 0.7, 0.9000000000000001, 1.1])
        self.assertListEqual(list(sweep(15, -15, 2.5)),
                             [15.0, 12.5, 10.0, 7.5, 5.0, 2.5, 0.0, -2.5, -5.0, -7.5, -10.0, -12.5, -15.0])
        self.assertListEqual(list(sweep(-2, 2, 2)), [-2, 0, 2])
        self.assertListEqual(list(sweep(-2, 2, -2)), [2, 0, -2])
        self.assertListEqual(list(sweep(2, -2, 2)), [2, 0, -2])
        self.assertListEqual(list(sweep(2, -2, -2)), [2, 0, -2])
        self.assertListEqual(list(sweep_n(0.3, 1.1, 5)), [0.3, 0.5, 0.7, 0.9000000000000001, 1.1])
        self.assertListEqual(list(sweep_n(15, -15, 13)),
                             [15.0, 12.5, 10.0, 7.5, 5.0, 2.5, 0.0, -2.5, -5.0, -7.5, -10.0, -12.5, -15.0])
        self.assertListEqual(list(sweep_log(0.1, 11e3, 10)), [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0])
        self.assertListEqual(list(sweep_log(1000, 1, 2)),
                             [1000, 500.0, 250.0, 125.0, 62.5, 31.25, 15.625, 7.8125, 3.90625, 1.953125])
        for a, b in zip(list(sweep_log_n(1, 10, 6)),
                             [1.0, 1.584893192461113, 2.5118864315095806, 3.981071705534973, 6.309573444801934,
                              10.0]):

            self.assertAlmostEqual(a, b)
        for a, b in zip(list(sweep_log_n(10, 1, 5)),
                             [10.0, 5.623413251903491, 3.1622776601683795, 1.7782794100389228, 1]):
            self.assertAlmostEqual(a, b)


#------------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
#------------------------------------------------------------------------------
