# coding=utf-8

import numpy as np
from obspy.signal.filter import bandpass

'''
Mathematical filtering routines for array manipulation
Written in part by François-Xavier Simon (@fxsimon)
'''

def bgr(arr):
	'''
	Instrument background removal (BGR)
	Subtracts off row averages
	'''
    print('removing horizontal background...')
    i = 0
    for row in arr:          # each row
        mean = np.mean(row)
        arr[i] = row - mean
        i += 1
    return arr

def dewow(arr):
	'''
	Polynomial dewow filter
	'''
    print('dewowing data...')
    signal = list(zip(*arr))[10]
    model = np.polyfit(range(len(signal)), signal, 3)
    predicted = list(np.polyval(model, range(len(signal))))
    i = 0
    for column in arr.T:      # each column
        arr.T[i] = column + predicted
        i += 1
    return arr

def bp(arr, rhf_depth, cr, rh_nsamp, freqmin, freqmax):
	'''
	Vertical frequency domain bandpass
	'''
    print('vertical frequency filtering...')
    fq = 1 / (rhf_depth / cr / rh_nsamp)
    freqmin = freqmin * 10 ** 6
    freqmax = freqmax * 10 ** 6
    
    print('Sampling frequency:       %.2E Hz' % fq)
    print('Minimum filter frequency: %.2E Hz' % freqmin)
    print('Maximum filter frequency: %.2E Hz' % freqmax)
    
    i = 0
    for t in arr.T:
        f = bandpass(data=t, freqmin=freqmin, freqmax=freqmax, df=fq, corners=2, zerophase=False)
        arr[:,i] = f
        i += 1
