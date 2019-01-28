# coding=utf-8

import numpy as np
from obspy.signal.filter import bandpass
import readgssi.functions as fx

'''
Mathematical filtering routines for array manipulation
Written in part by François-Xavier Simon (@fxsimon)
'''

def bgr(arr, verbose=False):
    '''
    Instrument background removal (BGR)
    Subtracts off row averages
    '''
    if verbose:
        fx.printmsg('removing horizontal background...')
    i = 0
    for row in arr:          # each row
        mean = np.mean(row)
        arr[i] = row - mean
        i += 1
    return arr

def dewow(arr, verbose=False):
    '''
    Polynomial dewow filter
    '''
    if verbose:
        fx.printmsg('dewowing data...')
    signal = list(zip(*arr))[10]
    model = np.polyfit(range(len(signal)), signal, 3)
    predicted = list(np.polyval(model, range(len(signal))))
    i = 0
    for column in arr.T:      # each column
        arr.T[i] = column + predicted
        i += 1
    return arr

def bp(arr, rhf_depth, cr, rh_nsamp, freqmin, freqmax, verbose=False):
    '''
    Vertical frequency domain bandpass
    '''
    if verbose:
        fx.printmsg('vertical frequency filtering...')
    fq = 1 / (rhf_depth / cr / rh_nsamp)
    freqmin = freqmin * 10 ** 6
    freqmax = freqmax * 10 ** 6
    
    if verbose:
        fx.printmsg('Sampling frequency:       %.2E Hz' % fq)
        fx.printmsg('Minimum filter frequency: %.2E Hz' % freqmin)
        fx.printmsg('Maximum filter frequency: %.2E Hz' % freqmax)
    
    i = 0
    for t in arr.T:
        f = bandpass(data=t, freqmin=freqmin, freqmax=freqmax, df=fq, corners=2, zerophase=False)
        arr[:,i] = f
        i += 1
    return arr
