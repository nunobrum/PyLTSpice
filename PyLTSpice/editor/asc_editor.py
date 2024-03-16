#!/usr/bin/env python
# coding=utf-8
# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        asc_editor.py
# Purpose:     Class made to update directly the ltspice ASC files
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import logging

_logger = logging.getLogger("spicelib.AscEditor")
_logger.info("This is maintained for backward compatibility. Use spicelib.editor.asc_editor instead")

from spicelib.editor.asc_editor import *
