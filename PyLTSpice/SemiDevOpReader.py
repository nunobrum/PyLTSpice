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
# Name:        SemiDevOpReader.py
# Purpose:     Read Semiconductor Device Operating Points from a log file
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     19-09-2021
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

"""
Implements a parser for extracting Semiconductor Devices Operating Points from an LTSpice log file.
"""

import re
from .detect_encoding import detect_encoding


def opLogReader(filename: str) -> dict:
    """
    This function is exclusively dedicated to retrieving operation point parameters of Semiconductor Devices. This is
    handled separately from the main LogReader class because of its specialization and therefore not judged to be
    of interest to the typical LTSpice user making board level simulations.

    Below is an excerpt of a Semiconductor Device Operating Points log.py

    .. code-block:: text

        Semiconductor Device Operating Points:

                                --- Diodes ---
        Name:         d:m6:1:para2:1               d:m4:1:para2:1               d:m3:1:para2:1         d:m6:1:para1:2
        Model: m6:1:para2:dpar_5v_psubnburd m4:1:para2:dpar_5v_psubnburd m3:1:para2:dpar_5v_psubnburd dpar_pburdnburdsw
        Id:              3.45e-19                     3.45e-19                     3.45e-19                1.11e-13
        Vd:              3.27e-07                     3.27e-07                     3.27e-07                9.27e-02
        ...
        CAP:             3.15e-14                     3.15e-14                     3.15e-14                5.20e-14

                            --- Bipolar Transistors ---
        Name:     q:q2:1:2    q:q2:1:1     q:q1:1:2    q:q1:1:1     q:q7:3
        Model:  q2:1:qnl_pnp q2:1:qnl_m  q1:1:qnl_pnp q1:1:qnl_m   qpl_parc
        Ib:       3.94e-12     4.69e-08    7.43e-13     4.70e-08    3.75e-12
        Ic:      -2.34e-12     4.57e-06   -7.44e-13     4.50e-06   -2.35e-12
        Vbe:      1.60e+00     7.40e-01   -7.88e-04     7.40e-01    1.40e+00


    This function will parse the log file and will produce a dictionary that contains all the information retrieved with
    the following format:

    .. code-block:: python

        semi_ops = {
            'Diodes': {
                'd:m6:1:para2:1': {
                    'Model': 'm6:1:para2:dpar_5v_psubnburd', 'Id': 3.45e-19, 'Vd': 3.27e-07, ... 'CAP': 3.15e-14 },
                'd:m4:1:para2:1': {
                    'Model': 'm4:1:para2:dpar_5v_psubnburd', 'Id': 3.45e-19, 'Vd': 3.27e-07, ..., 'CAP': 3.15e-14 },
                'd:m3:1:para2:1': {
                    'Model': 'm3:1:para2:dpar_5v_psubnburd', 'Id': 3.45e-19, 'Vd': 3.27e-07, ..., 'CAP': 3.15e-14 },
                'd:m6:1:para1:2': {
                    'Model': 'dpar_pburdnburdsw', 'Id': 1.11e-13, 'Vd': 0.0927, ..., 'CAP': 5.2e-14 },
            },
            'Bipolar Transistors': {
                'q:q2:1:2': {
                    'Model': 'q2:1:qnl_pnp', 'Ib': 3.94e-12, 'Ic': -2.34e-12, 'Vbe': 160, ... },
                'q:q2:1:1': {
                    'Model': 'q2:1:qnl_m', 'Ib': 4.69e-08, 'Ic': 4.57e-06, 'Vbe': 0.074, ... },
                'q:q1:1:2': {
                    'Model': 'q1:1:qnl_pnp', 'Ib': 7.43e-13, 'Ic': -7.44e-13, 'Vbe': -0.000788, ... },
                'q:q1:1:1': {
                    'Model': 'q1:1:qnl_m', 'Ib': 4.7e-08, 'Ic': 4.5e-06, 'Vbe': 0.74, ... },
                'q:q7:3': {
                    'Model': 'qpl_parc', 'Ib': 3.75e-12, 'Ic': -2.35e-12, 'Vbe': 1.4, ... },
            },
        }


    :param filename: path to the log file containing the Semiconductor Device Operating Points
    :type filename: str
    :return: Dictionary containing the information as described above.
    :rtype: dict
    """
    dataset = {}
    is_title = re.compile(r"^\s*--- (.*) ---\s*$")
    encoding = detect_encoding(filename)
    log = open(filename, 'r', encoding=encoding)
    where = None
    n_devices = 0
    line = None
    for line in log:
        if line.startswith("Semiconductor Device Operating Points:"):
            break

    if line is not None and line.startswith("Semiconductor Device Operating Points:"):
        for line in log:
            match = is_title.search(line)
            if match is not None:
                where = match.group(1)
                dataset[where] = {}  # Creates a dictionary for each component type
            else:
                cols = re.split(r'\s+', line.rstrip('\r\n'))
                if len(cols) > 1 and (cols[0].endswith(":") or cols[0] == 'Gmb'):  # The last 'or condition solves an
                    # LTSpice bug where the Gmb parameter is not suffixed by :  - Thanks to Amitkumar for finding this.
                    if cols[0] == "Name:":
                        devices = cols[1:]
                        n_devices = len(devices)
                        for dev in cols[1:]:
                            dataset[where][dev] = {}
                    else:
                        if n_devices > 0 and len(cols) == (n_devices + 1):
                            param = cols[0].rstrip(':')
                            for i, val in enumerate(cols[1:]):
                                try:
                                    value = float(val)
                                except ValueError:
                                    value = val
                                dataset[where][devices[i]][param] = value
    log.close()
    return dataset
