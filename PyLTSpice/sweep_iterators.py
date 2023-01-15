# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        sweep_iterators.py
# Purpose:     Iterators to use for sweeping values
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     24-07-2020
# Licence:     refer to the LICENSE file
#
# -------------------------------------------------------------------------------

@file:          sweep_iterators.py
@date:          2020-07-24

@brief          Iterator Helper

                relaxed parameter sweeps
"""
import math
from typing import Union, Optional, Iterable


class BaseIterator(object):
    """Common implementation to all Iterator classes"""

    def __init__(self, start: Union[int, float], stop: Optional[Union[int, float]] = None, step: Union[int, float] = 1):
        if stop is None:
            self.stop = start
            self.start = 0
        else:
            self.start = start
            self.stop = stop
        self.step = step
        self.finished = False

    def __iter__(self):
        self.finished = False
        return self

    def __next__(self):
        raise NotImplemented("This function needs to be overriden")


class sweep(BaseIterator):
    """
    Generator function to be used in sweeps.
    Advantages towards the range python built-in functions
    - Supports floating point arguments
    - Supports both up and down sweeps
    Usage:
        >>> list(sweep(0.3, 1.1, 0.2))
        [0.3, 0.5, 0.7, 0.9000000000000001, 1.1]
        >>> list(sweep(15, -15, 2.5))
        [15, 12.5, 10.0, 7.5, 5.0, 2.5, 0.0, -2.5, -5.0, -7.5, -10.0, -12.5, -15.0]
    """
    def __init__(self, start: Union[int, float], stop: Optional[Union[int, float]] = None,
                 step: Union[int, float] = 1):
        super().__init__(start, stop, step)
        assert step != 0, "Step cannot be 0"
        if self.step < 0 and self.start < self.stop:
            # The sign of the step determines whether it counts up or down.
            self.start, self.stop = self.stop, self.start
        elif self.step > 0 and self.stop < self.start:
            self.step = - self.step  # In this case invert the sigh
        self.niter = 0

    def __iter__(self):
        super().__iter__()
        # Resets the interator
        self.niter = 0
        return self

    def __next__(self):
        val = self.start + self.niter * self.step
        self.niter += 1
        if (self.step > 0 and val <= self.stop) or (self.step < 0 and val >= self.stop):
            return val
        else:
            self.finished = True
            raise StopIteration

def sweep_n(start: Union[int, float], stop: Union[int, float], N: int) -> Iterable[float]:
    """Helper function.
    Generator function that generates a 'N' number of points between a start and a stop interval.
    Advantages towards the range python built-in functions
    - Supports floating point arguments
    - Supports both up and down sweeps-
    Usage:
        >>> list(sweep_n(0.3, 1.1, 5))
        [0.3, 0.5, 0.7, 0.9000000000000001, 1.1]
        >>> list(sweep_n(15, -15, 13))
        [15, 12.5, 10.0, 7.5, 5.0, 2.5, 0.0, -2.5, -5.0, -7.5, -10.0, -12.5, -15.0]
        """
    return sweep(start, stop, (stop-start)/(N-1))



class sweep_log(BaseIterator):
    """
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
    def __init__(self, start: Union[int, float], stop: Optional[Union[int, float]] = None,
                 step: Optional[Union[int, float]] = 10):
        if stop is None:
            stop = start
            start = 1
        super().__init__(start, stop, step)
        assert step != 1 and step > 0, "Step must be higher than 0 and not 1"
        if self.start < self.stop and self.step < 1:
            self.start, self.stop = self.stop, self.start
        elif self.stop < self.start and self.step > 1:
            self.step = 1/self.step
        self.val = self.start

    def __iter__(self):
        super().__iter__()
        self.val = self. start
        return self

    def __next__(self):
        val = self.val  # Store previous value
        self.val *= self.step  # Calculate the next item
        if (self.start < self.stop and val <= self.stop) or \
           (self.start > self.stop and val >= self.stop):
            return val
        else:
            self.finished = True
            raise StopIteration


class sweep_log_n(BaseIterator):
    """Helper function.
    Generator function that generates a 'N' number of points between a start and a stop interval.
    Advantages towards the range python built-in functions
    - Supports floating point arguments
    - Supports both up and down sweeps-
    Usage:
        >>> list(sweep_log_n(1, 10, 6))
        [1.0, 1.5848931924611136, 2.5118864315095806, 3.9810717055349736, 6.309573444801934, 10.000000000000004]
        >>> list(sweep_log_n(10, 1, 5))
        [1.0, 0.5623413251903491, 0.31622776601683794, 0.17782794100389226, 0.09999999999999999]
        """
    def __init__(self, start: Union[int, float], stop: Optional[Union[int, float]], number_of_elements: int):
        step = math.exp(math.log(stop / start) / (number_of_elements - 1))
        assert step != 0, "Step cannot be 0"
        super().__init__(start, number_of_elements, step)
        self.niter = 0

    def __iter__(self):
        super().__iter__()
        self.niter = 0
        return self

    def __next__(self):
        if self.niter < self.stop:
            val = self.start * (self.step ** self.niter)
            self.niter += 1
            return val
        else:
            self.finished = True
            raise StopIteration


# ------------------------------------------------------------------------------
# ======================== Andreas Kaeberlein Iterator =========================

class sweep_iterators:

    # *****************************
    def __init__(self):
        """
        Initialization
        """
        self.numTotalIterations = 0  # total of iteartion if all loops are executed
        self.numCurrentIteration = 0  # current iteration
        self.iteratorEntrys = []  # list of dicts for iterator entrys
        self.idxForNextIter = []  # currently used entry value for loop

    # *****************************

    # *****************************
    def add(self, name="", vals=[]):
        """
        @note               adds entry to list of iterators

        @param name         component name in ltspice schematic
        @param vals         component values
        @rtype              boolean
        @return             successful
        """
        # check for valid arguments
        if (0 == len(name) or 0 == len(vals)):
            raise ValueError("Empty arguments provided")
        # add to iterator list
        self.iteratorEntrys.append({'name': name, 'values': vals})  # add entry
        self.idxForNextIter.append(0)  # start on first element
        # update total number of iteration
        self.numTotalIterations = 1;  # prepare for mutiplication
        for i in self.iteratorEntrys:
            self.numTotalIterations = self.numTotalIterations * len(i['values'])
        # reset current iterator to ensure restart
        self.numCurrentIteration = 0
        # succesfull end
        return True

    # *****************************

    # *****************************
    def done(self):
        """
        @note               check if iteration is done
        @rtype              boolean
        @retval     True    Iteration done
        @retval     False   Iteration needs to continue
        @return             successful
        """
        # check for proper init
        if (0 == len(self.iteratorEntrys)):
            return True
        # iteration done?
        if (self.numCurrentIteration < self.numTotalIterations):
            return False
        return True

    # *****************************

    # *****************************
    def next(self):
        """
        @note               creates next parameter set for sweep

        @rtype              dict
        @return             parameter set
        """
        # check for iterators
        if (0 == len(self.iteratorEntrys)):
            raise ValueError("No iterator entrys defined. Use 'add' procedure")
        # assemble dict with new iterator values
        nextIter = {}
        for i in range(len(self.iteratorEntrys)):
            nextIter[self.iteratorEntrys[i]['name']] = self.iteratorEntrys[i]['values'][self.idxForNextIter[i]]
        # prepare for next cycle
        for i in range(len(self.idxForNextIter) - 1, -1, -1):
            # increment inner loop
            if (i == len(self.idxForNextIter) - 1):
                self.idxForNextIter[i] = self.idxForNextIter[i] + 1
            # inner loop overflow, inc outer loop
            if (self.idxForNextIter[i] >= len(self.iteratorEntrys[i]['values'])):
                self.idxForNextIter[i] = 0  # restart inner loop at first element
                self.idxForNextIter[max(i - 1, 0)] = self.idxForNextIter[i - 1] + 1  # go to next element in outer loop
        # increment iterator
        self.numCurrentIteration = self.numCurrentIteration + 1
        # next iteration element
        return nextIter
    # *****************************


if __name__ == "__main__":

    print("list(sweep(10))", list(sweep(10)))
    print("list(sweep(1, 8))", list(sweep(1, 8)))
    print("list(sweep(2, 8, 2))", list(sweep(2, 8, 2)))
    print("list(sweep(2, 8, -2))", list(sweep(2, 8, -2)))
    print("list(sweep(8, 2, 2))", list(sweep(8, 2, 2)))
    print("list(sweep(0.3, 1.1, 0.2))", list(sweep(0.3, 1.1, 0.2)))
    print("list(sweep(15, -15, 2.5))", list(sweep(15, -15, 2.5)))
    print("list(sweep(-2, 2, 2))", list(sweep(-2, 2, 2)))
    print("list(sweep(-2, 2, -2))", list(sweep(-2, 2, -2)))
    print("list(sweep(2, -2, 2))", list(sweep(2, -2, 2)))
    print("list(sweep(2, -2, -2))", list(sweep(2, -2, -2)))
    print("list(sweep_n(0.3, 1.1, 4)", list(sweep_n(0.3, 1.1, 5)))
    print("list(sweep_n(15, -15, 13))", list(sweep_n(15, -15, 13)))
    print("list(sweepLog(0.1, 11e3, 10))", list(sweep_log(0.1, 11e3, 10)))
    print("list(sweep_log(1000, 1, 2))", list(sweep_log(1000, 1, 2)))
    print("list(sweep_log_n(1, 10, 6))", list(sweep_log_n(1, 10, 6)))
    print("list(sweep_log_(10, 1, 5))", list(sweep_log_n(10, 1, 5)))

    # ============= Andreas Kaeberlein Iterator =========================
    # init class
    mySI = sweep_iterators()

    # add to sweep
    mySI.add('R1', [10, 20])
    mySI.add('R2', [0, 1])
    mySI.add('X1', ["abc", "def"])

    # generate iterator
    while (not mySI.done()):
        print(mySI.next())
# ------------------------------------------------------------------------------

