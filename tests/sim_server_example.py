

import PyLTSpice.sim.ltspice_simulator as ltsim
from PyLTSpice.sim.sim_server import SimServer

a = SimServer(ltsim.LTspiceSimulator.get_default_simulator())
a.run_server(9000)