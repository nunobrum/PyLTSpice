from PyLTSpice import SimRunner
from PyLTSpice import AscEditor
from PyLTSpice.sim.tookit.montecarlo import Montecarlo

# Force another simulatior
simulator = r"C:\Users\nunob\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

# select spice model
LTC = SimRunner(output_folder='./temp', simulator=simulator)
sallenkey = AscEditor("./testfiles/salenkey.asc")

mc = Montecarlo(sallenkey, runner=LTC)

mc.set_tolerance('R', 0.01)  # 1% tolerance
mc.set_tolerance('C', 0.1)  # 10% tolerance
mc.set_tolerance('V', 0.1)  # 10% tolerance

mc.set_parameter_deviation('Vos', 3e-4, 5e-3, 'uniform')
mc.save_netlist('./testfiles/salenkey_mc.net')

