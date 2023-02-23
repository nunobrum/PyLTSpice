from PyLTSpice.sim.sim_runner import SimRunner
from PyLTSpice.sim.spice_editor import SpiceEditor
from PyLTSpice.sim.ngspice_simulator import NGspiceSimulator
from PyLTSpice.utils.sweep_iterators import sweep_log


def processing_data(raw_file, log_file):
    print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))


# select spice model
LTC = SimRunner(output_folder='./temp', simulator=NGspiceSimulator.create_from('C:/Apps/NGSpice64/bin/ngspice.exe'))
netlist = SpiceEditor('testfile_ngspice.net')
# set default arguments
netlist.set_parameters(res=0, cap=100e-6)
netlist.set_component_value('R1', '4k')
netlist.set_element_model('V1', "SINE(0 1 3k 0 0 0)")  # Modifying the
netlist.add_instruction(".tran 1n 3m")
netlist.add_instruction(".plot V(out)")

# .step dec param cap 1p 10u 1
for cap in sweep_log(1e-12, 10e-6, 10):
    netlist.set_parameter('cap', cap)
    LTC.run(netlist, callback=processing_data)

LTC.wait_completion()

# Sim Statistics
print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))
