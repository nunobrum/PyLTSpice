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
sys.path.append(os.path.abspath((os.path.dirname(os.path.abspath(__file__)) + "/../../../")))   # add project root to lib search path
import PyLTSpice.sweep_iterators as sweep_iterators                                             # Python Script under test
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
        dut = sweep_iterators.sweep_iterators()
        # check 
        self.assertEqual(dut.numTotalIterations, 0)
        self.assertEqual(dut.numCurrentIteration, 0)
        self.assertListEqual(dut.iteratorEntrys, [])
        self.assertListEqual(dut.idxForNextIter, [])
    #*****************************
    
    
    #*****************************
    def test_add(self):
        """
        @note   add 
        """
        # prepare
        dut = sweep_iterators.sweep_iterators()
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
        dut = sweep_iterators.sweep_iterators()
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
    
    
    #*****************************
    def test_done(self):
        """
        @note   next
        """
        # prepare
        dut = sweep_iterators.sweep_iterators()
        dut.add('e1', [10])
        # check
        self.assertDictEqual(dut.next(), {'e1': 10})
        self.assertTrue(dut.done())
    #*****************************
    
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
#------------------------------------------------------------------------------
