
import time
import PyLTSpice.sim.ltspice_simulator as ltsim
from PyLTSpice.sim.srv_interface import SimServer

a = SimServer(ltsim.LTspiceSimulator.get_default_simulator(), port=9000)
while a.running():
    time.sleep(1)

print("stopping...SimServer")