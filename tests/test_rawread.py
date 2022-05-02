import os
import sys
# sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('..'))
from PyLTSpice.LTSpice_RawRead import RawRead as RawRead

files = [
    'tran.raw',
    'tran - step.raw',
    'ac.raw',
    'ac - step.raw',
]
control_file = open("control_data_file.txt", 'w')
for file in files:
    if 'tests' in os.getcwd():
        file = os.getcwd() + os.sep + file
    else:
        file = os.getcwd() + r'\tests' + os.sep + file
    print(file)
    ltr = RawRead(file)
    control_file.write("%s %s %s\r\n" % (20 * "=", file, "=" * (20 - len(file))))
    for name in ltr.get_trace_names():
        control_file.write("Trace : %s\r\n" % name)
        for step in ltr.get_steps():
            tr = ltr.get_trace(name)
            print(name)
            print('step {:d} {}'.format(step, tr.get_wave(step)))
            control_file.write("\r\n\r\nSTEP : %d\r\n" % step)
            for v in tr.get_wave(step):
                control_file.write("{}\n".format(v))
        control_file.write("\r\n\r\n")

control_file.close()