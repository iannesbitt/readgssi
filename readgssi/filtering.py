import numpy as np
from obspy.signal.filter import bandpass
import readgssi.functions as fx

'''
Mathematical filtering routines for array manipulation
Written in part by François-Xavier Simon (@fxsimon)
'''

def bgr(ar, verbose=False):
    '''
    Instrument background removal (BGR)
    Subtracts off row averages
    '''
    if verbose:
        fx.printmsg('removing horizontal background...')
    i = 0
    for row in ar:          # each row
        mean = np.mean(row)
        ar[i] = row - mean
        i += 1
    return ar

def dewow(ar, verbose=False):
    '''
    Polynomial dewow filter
    '''
    if verbose:
        fx.printmsg('dewowing data...')
    signal = list(zip(*ar))[10]
    model = np.polyfit(range(len(signal)), signal, 3)
    predicted = list(np.polyval(model, range(len(signal))))
    i = 0
    for column in ar.T:      # each column
        ar.T[i] = column + predicted
        i += 1
    return ar

def bp(ar, header, freqmin, freqmax, verbose=False):
    '''
    Vertical frequency domain bandpass
    '''
    if verbose:
        fx.printmsg('vertical frequency filtering...')
    samp_freq = 1 / (header['rhf_depth'] / header['cr'] / header['rh_nsamp'])
    freqmin = freqmin * 10 ** 6
    freqmax = freqmax * 10 ** 6
    
    if verbose:
        fx.printmsg('Sampling frequency:       %.2E Hz' % samp_freq)
        fx.printmsg('Minimum filter frequency: %.2E Hz' % freqmin)
        fx.printmsg('Maximum filter frequency: %.2E Hz' % freqmax)
    
    i = 0
    for t in ar.T:
        f = bandpass(data=t, freqmin=freqmin, freqmax=freqmax, df=samp_freq, corners=2, zerophase=False)
        ar[:,i] = f
        i += 1
    return ar
