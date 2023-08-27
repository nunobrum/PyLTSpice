from PyLTSpice import RawRead
from PyLTSpice.sim.sim_runner import SimRunner
from PyLTSpice.editor.spice_editor import SpiceEditor
from PyLTSpice.sim.qspice_simulator import Qspice
from PyLTSpice.utils.sweep_iterators import sweep_log


def processing_data(raw_file, log_file):
    print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))
    raw_data = RawRead(raw_file)
    vout = raw_data.get_wave('V(out)')
    return raw_file, vout.max()


# select spice model
sim = SimRunner(output_folder='./temp', simulator=Qspice.create_from('C:/Program Files/QSPICE/QSPICE64.exe'))
netlist = SpiceEditor('./testfiles/testfile.net')
# set default arguments
netlist.set_component_value('R1', '4k')
netlist.set_element_model('V1', "SINE(0 1 3k 0 0 0)")  # Modifying the
netlist.add_instruction(".tran 1n 3m")
netlist.add_instruction(".plot V(out)")
netlist.add_instruction(".save all")

sim_no = 1
# .step dec param cap 1p 10u 1
for cap in sweep_log(1e-12, 10e-6, 10):
    netlist.set_component_value('C1', cap)
    sim.run(netlist, callback=processing_data, run_filename=f'testfile_qspice_{sim_no}.net')
    sim_no += 1

# Reading the data
results = {}
for raw_file, vout_max in sim:  # Iterate over the results of the callback function
    results[raw_file.name] = vout_max
# The block above can be replaced by the following line
# results = {raw_file.name: vout_max for raw_file, vout_max in sim}

print(results)

# Sim Statistics
print('Successful/Total Simulations: ' + str(sim.okSim) + '/' + str(sim.runno))

sim.file_cleanup()
