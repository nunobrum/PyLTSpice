# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 14:39:01 2019

@author: yyk
"""

import matplotlib.pyplot as plt
from LTSpice_RawRead import LTSpiceRawRead

test_directory = "C:/Users/Bruce Banner/Documents/GitHub/ADC_experiments/ideal_sims/"
filename = 'dyn_comparator.raw'

raw_filename = test_directory + filename
LTR = LTSpiceRawRead(raw_filename)
print(LTR.get_trace_names())
print(LTR.get_raw_property())

plt.figure()

vip_signals = LTR.get_trace('V(vip)')
vin_signals = LTR.get_trace('V(vin)')
done_signals = LTR.get_trace('V(done)')
comp_results = LTR.get_trace('V(result)')
input_curve  = []
output_curve = []

output_curves = []
time_curves = []

x = LTR.get_trace('time')  # Zero is always the X axis

#steps = LTR.get_steps(ana=4.0)
steps = LTR.get_steps()
for step in steps[1:]:
   vip = vip_signals.get_point(0, step=step)
   vin = vin_signals.get_point(0, step=step)
   
   time_curves.append(x.get_wave(step))
   input_voltage = vip-vin
   output_voltage = comp_results.get_point(-1,step=step)
   output_curves.append(comp_results.get_wave(step))
   input_curve.append(input_voltage)
   output_curve.append(output_voltage)
   
   print("Step:\t" + str(step) + "\t"
         "Input:\t" + str(round(1000*input_voltage,2)) + "mV\t"+
         "Output:\t" + str(round(output_voltage)))

plt.plot(input_curve, output_curve, marker='x')
plt.grid(True)
plt.figure()
plt.plot(time_curves[-1], output_curves[-1])
plt.grid(True)