
from PyLTSpice.LTSpiceBatch import SimCommander


class SimAnalysis(SimCommander):

    def __init__(self, circuit_file: str, parallel_sims=4):
        SimCommander.__init__(self, circuit_file, parallel_sims=parallel_sims)
