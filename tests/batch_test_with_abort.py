import os
from PyLTSpice.sim_batch import SimCommander

def processing_data(raw_file, log_file):
    print("Handling the simulation data of %s, log file %s" % (raw_file, log_file))

# select spice model
LTC = SimCommander("Batch_Test.asc")
# set default arguments
LTC.set_parameters(res=0, cap=100e-6)
LTC.set_component_value('R2', '2k')  # Modifying the value of a resistor
LTC.set_component_value('R1', '4k')
LTC.set_element_model('V3', "SINE(0 1 3k 0 0 0)")  # Modifying the
LTC.set_component_value('XU1:C2', 20e-12)  # modifying a
# define simulation
LTC.add_instructions(
    "; Simulation settings",
    ".param run = 0"
)

for opamp in ('AD712', 'AD820'):
    LTC.set_element_model('XU1', opamp)
    for supply_voltage in (5, 10, 15):
        LTC.set_component_value('V1', supply_voltage)
        LTC.set_component_value('V2', -supply_voltage)
        # overriding he automatic netlist naming
        run_netlist_file = "{}_{}_{}.net".format(LTC.circuit_radic, opamp, supply_voltage)
        LTC.run(run_filename=run_netlist_file, callback=processing_data)


LTC.reset_netlist()
LTC.add_instructions(
    "; Simulation settings",
    ".ac dec 30 10 1Meg",
    ".meas AC Gain MAX mag(V(out)) ; find the peak response and call it ""Gain""",
    ".meas AC Fcut TRIG mag(V(out))=Gain/sqrt(2) FALL=last"
)

raw, log = LTC.run(run_filename="no_callback.net").wait_results()
processing_data(raw, log)

LTC.wait_completion(1, abort_all_on_timeout=True)

# Sim Statistics
print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))
