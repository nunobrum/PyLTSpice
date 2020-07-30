import os
from PyLTSpice.sim_stepping import SimStepper

def processing_data(raw_file, log_file):
    print("Handling the simulation data of %s" % log_file )

# get script absolute path
meAbsPath = os.path.dirname(os.path.realpath(__file__))
# select spice model

Stepper = SimStepper(meAbsPath + "\\Batch_Test.asc")
# set default arguments
Stepper.set_parameters(res=0, cap=100e-6)
Stepper.set_component_value('R2', '2k')
Stepper.set_component_value('R1', '4k')
Stepper.set_element_model('V3', "SINE(0 1 3k 0 0 0)")
# define simulation
Stepper.add_instructions(
    "; Simulation settings",
    ".param run = 0"
)

Stepper.add_model_sweep('XU1',('AD712', 'AD820'))
Stepper.add_value_sweep('V1', (5, 10, 15))
Stepper.add_value_sweep('V1', (-5, -10, -15))

# run_netlist_file = "{}_{}_{}.net".format(Stepper.circuit_radic, opamp, supply_voltage)
Stepper.run_all(callback=processing_data)

# Sim Statistics
print('Successful/Total Simulations: ' + str(Stepper.okSim) + '/' + str(Stepper.runno))
