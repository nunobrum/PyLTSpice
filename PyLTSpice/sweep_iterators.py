"""
@author:        Nuno Brum; Andreas Kaeberlein
@copyright:     Copyright 2020

@license:       GPLv3
@maintainer:    Nuno Brum
@email:         me@nunobrum.com

@file:          sweep_iterators.py
@date:          2020-07-24

@brief          Iterator Helper

                relaxed parameter sweeps
"""



#------------------------------------------------------------------------------
# Python Libs
#
from typing import Union
#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
class sweep_iterators:

    #*****************************
    def __init__(self):
        """
        Initialization
        """
        pass
    #*****************************
    
    
    #*****************************
    def sweep(start: Union[int, float], stop: Union[int, float], step: Union[int, float] = 1):
        """Helper function.
        Generator function to be used in sweeps.
        Advantages towards the range python built-in functions
        - Supports floating point arguments
        - Supports both up and down sweeps-
        Usage:
            >>> list(sweep(0.3, 1.1, 0.2))
            [0.3, 0.5, 0.7, 0.9000000000000001, 1.1]
            >>> list(sweep(15, -15, 2.5))
            [15, 12.5, 10.0, 7.5, 5.0, 2.5, 0.0, -2.5, -5.0, -7.5, -10.0, -12.5, -15.0]
            """
        if step < 0:
            step = -step
        assert step != 0, "Step cannot be 0"
        val = start
        inc = 0
        if start < stop:
            while val <= stop:
                yield val
                inc += 1
                val = start + inc * step
        elif start > stop:
            while val >= stop:
                yield val
                inc += 1
                val = start - inc * step
    #*****************************


    #*****************************
    def sweep_log(start: Union[int, float], stop: Union[int, float], step: Union[int, float] = 10):
        """Helper function.
        Generator function to be used in logarithmic sweeps.
    Advantages towards the range python built-in functions_
        - Supports floating point arguments
        - Supports both up and down sweeps.
        Usage:
            >>> list(sweep_log(0.1, 11e3, 10))
            [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0]
            >>> list(sweep_log(1000, 1, 2))
            [1000, 500.0, 250.0, 125.0, 62.5, 31.25, 15.625, 7.8125, 3.90625, 1.953125]
            """
        stp = abs(step)
        assert stp > 1.0, "The Step should be higher than 1"
        if start < stop:
            while start <= stop:
                yield start
                start *= stp
        elif start > stop:
            while start >= stop:
                yield start
                start /= stp
    #*****************************

#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
if __name__ == '__main__':
    
    print("Test")
    
#------------------------------------------------------------------------------
