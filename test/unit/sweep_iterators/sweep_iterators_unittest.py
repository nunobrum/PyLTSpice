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
        # init
        dut = sweep_iterators.sweep_iterators()
        # check 
        self.assertEqual(dut.numTotalIterations, 0)
        self.assertEqual(dut.numCurrentIteration, 0)
        self.assertListEqual(dut.iteratorEntrys, [])
        self.assertListEqual(dut.idxForNextIter, [])
    #*****************************
    
    
    
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
#------------------------------------------------------------------------------
