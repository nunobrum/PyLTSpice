from PyLTSpice.sim.sim_runner import SimRunner
from PyLTSpice.sim.spice_editor import SpiceEditor

def processing_data(raw_file, log_file):
    print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))


# select spice model
LTC = SimRunner(output_folder='./temp')
LTC.create_netlist('Batch_Test.asc')
netlist = SpiceEditor('Batch_Test.net')
# set default arguments
netlist.set_parameters(res=0, cap=100e-6)
netlist.set_component_value('R2', '2k')  # Modifying the value of a resistor
netlist.set_component_value('R1', '4k')
netlist.set_element_model('V3', "SINE(0 1 3k 0 0 0)")  # Modifying the
netlist.set_component_value('XU1:C2', 20e-12)  # modifying a define simulation
netlist.add_instructions(
    "; Simulation settings",
    ".param run = 0"
)

for opamp in ('AD712', 'AD820'):
    netlist.set_element_model('XU1', opamp)
    for supply_voltage in (5, 10, 15):
        netlist.set_component_value('V1', supply_voltage)
        netlist.set_component_value('V2', -supply_voltage)
        # overriding he automatic netlist naming
        run_netlist_file = "{}_{}_{}.net".format(netlist.netlist_file.stem, opamp, supply_voltage)
        LTC.run(netlist, callback=processing_data, run_filename=run_netlist_file)


netlist.reset_netlist()
netlist.add_instructions(
    "; Simulation settings",
    ".ac dec 30 10 1Meg",
    ".meas AC Gain MAX mag(V(out)) ; find the peak response and call it ""Gain""",
    ".meas AC Fcut TRIG mag(V(out))=Gain/sqrt(2) FALL=last"
)

raw, log = netlist.run("no_callback.net").wait_results()
processing_data(raw, log)

LTC.wait_completion()

# Sim Statistics
print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))

enter = input("Press enter to delete created files")
if enter == '':
    LTC.file_cleanup()