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

from spicelib.utils.sweep_iterators import *

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
