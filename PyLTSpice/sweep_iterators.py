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
#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
class sweep_iterators:

    #*****************************
    def __init__(self):
        """
        Initialization
        """
        self.numTotalIterations = 0     # total of iteartion if all loops are executed
        self.numCurrentIteration = 0    # current iteration
        self.iteratorEntrys = []        # list of dicts for iterator entrys
        self.idxForNextIter = []        # currently used entry value for loop
    #*****************************
    
    
    #*****************************
    def add(self, name="", vals = []):
        """
        @note               adds entry to list of iterators
                            
        @param name         component name in ltspice schematic
        @param vals         component values
        @rtype              boolean
        @return             successful
        """
        # check for valid arguments
        if ( 0 == len(name) or 0 == len(vals) ):
            raise ValueError("Empty arguments provided")
        # add to iterator list
        self.iteratorEntrys.append({'name': name, 'values': vals})  # add entry
        self.idxForNextIter.append(0)                               # start on first element
        # update total number of iteration
        self.numTotalIterations = 1;    # prepare for mutiplication
        for i in self.iteratorEntrys:
            self.numTotalIterations = self.numTotalIterations * len(i['values'])
        # reset current iterator to ensure restart
        self.numCurrentIteration = 0
        # succesfull end
        return True
    #*****************************
    
    
    #*****************************
    def done(self):
        """
        @note               check if iteration is done
        @rtype              boolean
        @retval     True    Iteration done
        @retval     False   Iteration needs to continue
        @return             successful
        """
        # check for proper init
        if ( 0 == len(self.iteratorEntrys) ):
            return True
        # iteration done?
        if ( self.numCurrentIteration < self.numTotalIterations ):
            return False
        return True
    #*****************************
    
    
    #*****************************
    def next(self):
        """
        @note               creates next parameter set for sweep
        
        @rtype              dict
        @return             parameter set
        """
        # check for iterators
        if ( 0 == len(self.iteratorEntrys) ):
            raise ValueError("No iterator entrys defined. Use 'add' procedure")
        # assemble dict with new iterator values
        nextIter = {}
        for i in range(len(self.iteratorEntrys)):
            nextIter[self.iteratorEntrys[i]['name']] = self.iteratorEntrys[i]['values'][self.idxForNextIter[i]]
        # prepare for next cycle
        for i in range(len(self.idxForNextIter)-1, -1, -1):
            # increment inner loop
            if ( i == len(self.idxForNextIter)-1 ):
                self.idxForNextIter[i] = self.idxForNextIter[i] + 1
            # inner loop overflow, inc outer loop
            if ( self.idxForNextIter[i] >= len(self.iteratorEntrys[i]['values']) ):
                self.idxForNextIter[i]              = 0                             # restart inner loop at first element
                self.idxForNextIter[max(i-1, 0)]    = self.idxForNextIter[i-1] + 1  # go to next element in outer loop
        # increment iterator
        self.numCurrentIteration = self.numCurrentIteration + 1
        # next iteration element
        return nextIter
    #*****************************
    
#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
if __name__ == '__main__':
    
    # init class
    mySI = sweep_iterators()    
    
    # add to sweep
    mySI.add('R1', [10, 20])
    mySI.add('R2', [0, 1])
    mySI.add('X1', ["abc", "def"])
    
    # generate iterator
    while ( not mySI.done() ):
        print(mySI.next())
#------------------------------------------------------------------------------
