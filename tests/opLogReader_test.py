# coding=utf-8
"""
Tests the opLogReader function in the LTSpice_SemiDevOpReader
"""

from PyLTSpice.LTSpice_SemiDevOpReader import opLogReader
result = opLogReader("circuit.log")
for dev_type in result:
    print(" -- ", dev_type, ' --')
    for device in result[dev_type]:
        print("\t", device)
        for param in result[dev_type][device]:
            print("\t\t{:10s}{}".format(param, result[dev_type][device][param]))
