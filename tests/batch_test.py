import os
from PyLTSpice.LTSpiceBatch import LTCommander

# get script absolute path
meAbsPath = os.path.dirname(os.path.realpath(__file__));
# select spice model
LTC = LTCommander(meAbsPath + "\\Batch_Test.asc")
# set default arguments
LTC.set_parameters(res=0, cap=100e-6)
LTC.set_component_value('R2', '2k')
LTC.set_component_value('R1', '4k')
# define simulation
LTC.add_commands(
    "; Simulation settings",
    "Vin IN 0 SINE(0 1 10K)",
    ".TRAN 1m",
    ".param run = 0"
)

run = 0
for opamp in ('AD712', 'AD820'):
    LTC.set_element_model('XU1', opamp)
    for supply_voltage in (5, 10, 15):
        LTC.set_component_value('V1', supply_voltage)
        LTC.set_component_value('V2', -supply_voltage)
        LTC.set_parameter('run', run)
        try:
            LTC.run()
            os.rename(LTC.run_netlist_file, "{}_{}.net".format(opamp, supply_voltage))  # Keep the netlist for reference
        except:
            pass
        run += 1

LTC.reset_netlist()
LTC.add_commands(
    "; Simulation settings",
    "Vin IN 0 AC 1",
    ".ac dec 30 10 1Meg",
    ".meas AC Gain MAX mag(V(out)) ; find the peak response and call it ""Gain""",
    ".meas AC Fcut TRIG mag(V(out))=Gain/sqrt(2) FALL=last"
)
try:
    LTC.run()
except:
    pass


# Sim Statistics
print('Successful/Total Simulations: ' + str(LTC.okSim) + '/' + str(LTC.runno))
