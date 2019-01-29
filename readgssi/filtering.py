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

def stack(ar, stack='auto', verbose=False):
    '''
    stacking algorithm
    stack='auto' results in an approximately 2.5:1 x:y axis ratio
    '''
    if str(stack).lower() in 'auto':
        if verbose:
            fx.printmsg('attempting automatic stacking method...')
        ratio = (ar.shape[1]/ar.shape[0])/(75/30)
        if ratio > 1:
            stack = int(ratio)
        else:
            stack = 1
    else:
        try:
            stack = int(stack)
        except ValueError:
            fx.printmsg('ERROR: stacking must be indicated with an integer greater than 1, "auto", or None.')
            fx.printmsg('a stacking value of 1 equates to None. "auto" will attempt to stack to about a 2.5:1 x to y axis ratio.')
            fx.printmsg('the result will not be stacked.')
            stack = 1
    if stack > 1:
        if verbose:
            fx.printmsg('stacking %sx' % stack)
        i = list(range(stack))
        l = list(range(int(ar.shape[1]/stack)))
        arr = np.copy(ar[:,::stack])
        for s in l:
            arr[:,s] = arr[:,s] + ar[:,s*stack+1:s*stack+stack].sum(axis=1)
    else:
        if str(stack).lower() in 'auto':
            pass
        else:
            fx.printmsg('WARNING: no stacking applied. be warned: this can result in very large and awkwardly-shaped figures.')
    return arr, stack