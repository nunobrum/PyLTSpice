# -*- coding: utf-8 -*-
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

from typing import Union, Optional


class BaseIterator(object):

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


if __name__ == "__main__":

    print(list(sweep(10)))
    print(list(sweep(1, 8)))
    print(list(sweep(2, 8, 2)))
    print(list(sweep(2, 8, -2)))
    print(list(sweep(8, 2, 2)))
    print(list(sweep(0.3, 1.1, 0.2)))
    print(list(sweep(-2, 2, 2)))
    print(list(sweep(-2, 2, -2)))
    print(list(sweep(2, -2, 2)))
    print(list(sweep(2, -2, -2)))
    print(list(sweep_log(0.1, 11e3, 10)))
    print(list(sweep_log(1000, 1, 2)))


