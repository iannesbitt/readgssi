import readgssi.functions as fx
import numpy as np
import pandas as pd

def flip(ar, verbose=False):
    '''
    flip radargram horizontally (read backwards)
    '''
    if verbose:
        fx.printmsg('flipping radargram...')
    return ar.T[::-1].T

def reducex(ar, by=1, verbose=False):
    '''
    reduce the number of traces in the array by a number

    not the same as stacking since it doesn't sum adjacent traces
    '''
    if verbose:
        fx.printmsg('reducing array by a factor of %s...' % (by))
    return ar[:,::by]

def stack(ar, stack='auto', verbose=False):
    '''
    stacking algorithm

    stack='auto' results in an approximately 2.5:1 x:y axis ratio
    '''
    stack0 = stack
    if str(stack).lower() in 'auto':
        am = '(automatic)'
        ratio = (ar.shape[1]/ar.shape[0])/(75/30)
        if ratio > 1:
            stack = int(round(ratio))
        else:
            stack = 1
    else:
        am = '(manually set)'
        try:
            stack = int(stack)
        except ValueError:
            fx.printmsg('ERROR: stacking must be indicated with an integer greater than 1, "auto", or None.')
            fx.printmsg('a stacking value of 1 equates to None. "auto" will attempt to stack to about a 2.5:1 x to y axis ratio.')
            fx.printmsg('the result will not be stacked.')
            stack = 1
    if stack > 1:
        if verbose:
            fx.printmsg('stacking %sx %s...' % (stack, am))
        i = list(range(stack))
        l = list(range(int(ar.shape[1]/stack)))
        arr = np.copy(reducex(ar=ar, by=stack, verbose=verbose))
        for s in l:
            arr[:,s] = arr[:,s] + ar[:,s*stack+1:s*stack+stack].sum(axis=1)
    else:
        arr = ar
        if str(stack0).lower() in 'auto': # this happens when distance normalization reduces the file
            pass
        else:
            fx.printmsg('WARNING: no stacking applied. be warned: this can result in very large and awkwardly-shaped figures.')
    return arr, stack

def distance_normalize(header, ar, gps, verbose=False):
    '''
    distance normalization (not pretty but gets the job done)
    '''
    if ar[2] == []:
        if verbose:
            fx.printmsg('no gps information for distance normalization')
    else:
        if verbose:
            fx.printmsg('normalizing GPS velocity records...')
        while gps['velocity'].min() < 0.02: # fix zero and negative velocity values
            gps['velocity'].replace(gps['velocity'].min(), 0.02, inplace=True)
        norm_vel = (gps['velocity'] * (1/gps['velocity'].max())*100).to_frame('normalized') # should end up as dataframe with one column
        # upsample to match radar array shape
        nanosec_samp_rate = int((1/header['rhf_sps'])*10**9) # nanoseconds
        start = np.datetime64(str(norm_vel.index[0])) - np.timedelta64(nanosec_samp_rate*(gps.iloc[0,0]), 'ns')
        newdf = pd.DataFrame(index=pd.date_range(start=start, periods=ar.shape[1], freq=str(nanosec_samp_rate)+'N', tz='UTC'))
        norm_vel = pd.concat([norm_vel, newdf], axis=1).interpolate('time').bfill()
        norm_vel = norm_vel.round().astype(int, casting='unsafe')

        rm = round(ar.shape[1] / (norm_vel.shape[0] - ar.shape[1]))
        norm_vel = norm_vel.drop(norm_vel.index[::rm])
        for i in range(0,abs(norm_vel.shape[0]-ar.shape[1])):
            s = pd.DataFrame({'normalized':[norm_vel['normalized'].iloc[-1]]}) # hacky, but necessary
            norm_vel = pd.concat([norm_vel, s])
        if verbose:
            fx.printmsg('mean of normalized velocity is %.2f' % (norm_vel['normalized'].mean()))
            fx.printmsg('expanding array using normalized GPS velocity...')
        # takes (array, [transform values to broadcast], axis)
        ar = np.repeat(ar, norm_vel['normalized'].astype(int, casting='unsafe').values, axis=1)
        ar = reducex(ar, by=int(round(norm_vel['normalized'].mean())), verbose=verbose)
        if verbose:
            fx.printmsg('replacing traces per meter value of %s with %s' % (header['rhf_spm'],
                                                                                   ar.shape[1] / gps['meters'].iloc[-1]))
        header['rhf_spm'] = ar.shape[1] / gps['meters'].iloc[-1]
    return header, ar, gps