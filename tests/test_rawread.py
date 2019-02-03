import os
import sys
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('..'))
from LTSpice_RawRead import RawRead

files = [
    'tran.raw',
    'tran - step.raw',
    'ac.raw',
    'ac - step.raw',
]

for file in files:
    if 'tests' in os.getcwd():
        file = os.getcwd() + os.sep + file
    else:
        file = os.getcwd() + r'\tests' + os.sep + file
    ltr = RawRead(file)
    for name in ltr.get_trace_names():
        for step in ltr.get_steps():
            tr = ltr.get_trace(name)
            print(name)
            print('step {:d} {}'.format(step, tr.get_wave(step)))