#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
# Name:        ltsteps.py
# Purpose:     Process LTSpice output files and align data for usage in a spread-
#              sheet tool such as Excel, or Calc.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import logging

_logger = logging.getLogger("spicelib.LTSteps")
_logger.info("This module is maintained for backward compatibility. Use spicelib.log.ltsteps instead")

from spicelib.log.ltsteps import reformat_LTSpice_export, LTSpiceExport, LTSpiceLogReader
