# -*- coding: utf-8 -*-

# Convenience direct imports
from spicelib.raw.raw_read import RawRead, SpiceReadException
from spicelib.raw.raw_write import RawWrite, Trace
from spicelib.editor.spice_editor import SpiceEditor, SpiceCircuit
from spicelib.editor.asc_editor import AscEditor
from PyLTSpice.sim.sim_runner import SimRunner
from spicelib.simulators.ltspice_simulator import LTspice
from PyLTSpice.sim.sim_batch import SimCommander
from spicelib.log.ltsteps import LTSpiceLogReader


def all_loggers():
    """
    Returns all the name strings used as logger identifiers.

    :return: A List of strings which contains all the logger's names used in this library.
    :rtype: list[str]
    """
    return [
        "spicelib.RunTask",
        "spicelib.SimClient",
        "spicelib.SimServer",
        "spicelib.ServerSimRunner",
        "spicelib.LTSteps",
        "spicelib.RawRead",
        "spicelib.LTSpiceSimulator",
        "spicelib.SimBatch",
        "spicelib.SimRunner",
        "spicelib.SimStepper",
        "spicelib.SpiceEditor",
        "spicelib.SimBatch",
        "spicelib.AscEditor",
        "spicelib.LTSpiceSimulator",
    ]


def set_log_level(level):
    """
    Sets the logging level for all loggers used in the library.

    :param level: The logging level to be used, eg. logging.ERROR, logging.DEBUG, etc.
    :type level: int
    """
    import logging
    for logger in all_loggers():
        logging.getLogger(logger).setLevel(level)


def add_log_handler(handler):
    """
    Sets the logging handler for all loggers used in the library.

    :param handler: The logging handler to be used, eg. logging.NullHandler
    :type handler: Handler
    """
    import logging
    for logger in all_loggers():
        logging.getLogger(logger).addHandler(handler)
