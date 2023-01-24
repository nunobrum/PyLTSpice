import matplotlib.pyplot as plt
import numpy as np
from numpy import abs as np_mag
from numpy import angle as np_angle
from PyLTSpice import RawRead



def get_fra_data(logfile):
    log = open(logfile, 'r' )

    log_file_info = log.readlines()
    log.close()
    for line in log_file_info:
        if line[0:12] == 'FRA Instance':
            line = line.strip()
            _, FRA_info = line.split(': ')
            return( FRA_info )
    return( None )
    
    
def plot_fra(name, freq, complex_data, FRA_data ):
    bode_fig, ax1 = plt.subplots(figsize=(8,4))
    ax2 = ax1.twinx()

    gain = 20*np.log10(np_mag(complex_data))
    phase = np_angle( complex_data, deg=True)
    for i in range(len(phase)):
        if phase[i] > 0:
            phase[i] = phase[i] - 360

    ax1.semilogx(freq, gain, color='blue')
    #ax1.set_title(name)
    
    ax1.legend([name])
    ax1.yaxis.label.set_color('blue')
    ax1.set(xlabel='Frequency', ylabel='Gain (dB)')
    ax2.semilogx(freq, phase, color='red', ls='dashed')
    ax2.set_ylim([-280, -20])
    ax2.yaxis.label.set_color('red')
    ax2.set(xlabel='Frequency', ylabel='Phase (o)')
    ax1.minorticks_on()
    ax1.xaxis.get_major_locator().set_params(numticks=99)
    ax1.xaxis.get_minor_locator().set_params(numticks=99, subs=[.2, .4, .6, .8])
    ax1.grid(True, which='both', axis='both', ls='-')
    ax2.grid(which='major', ls='dashed')
    plt.title(FRA_data, ha='center')
    plt.show()
    
    
lt_file_name = 'fra_eg1'
lt_fra_raw = RawRead(lt_file_name+'.fra_1.raw')
FRA_info = get_fra_data(lt_file_name+'.log')

freq = lt_fra_raw.get_axis()
data = lt_fra_raw.get_trace('gain_1').get_wave(0)

plot_fra( 'gain_1', freq, data, FRA_info )