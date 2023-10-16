#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
# Name:        logfile_data.py
# Purpose:     Store data related to log files. This is a superclass of LTSpiceLogReader
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

import logging

_logger = logging.getLogger("PyLTSpice.LTSteps")
_logger.info("This module is deprecated. Use spicelib.log.logfile_data instead")
from spicelib.log.logfile_data import LogfileData, LTComplex
