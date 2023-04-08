
import time
import PyLTSpice.sim.ltspice_simulator as ltsim
from PyLTSpice.client_server.srv_interface import SimServer

a = SimServer(ltsim.LTspice, port=9000)
while a.running():
    time.sleep(1)

print("stopping...SimServer")