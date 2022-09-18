import os
import sys
# sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('..'))
from PyLTSpice.LTSpice_RawRead import RawRead as RawRead

x = RawRead(r"C:\sandbox\PyLTSpice_GitHub_nunobrum\test_files\pyltspiceversion2_0_1issue\diffpair_ee114-DM.raw")