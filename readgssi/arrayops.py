import readgssi.functions as fx
import numpy as np

def flip(ar, verbose=False):
    if verbose:
        fx.printmsg('flipping radargram...')
    return ar.T[::-1].T

def stack(ar, stack='auto', verbose=False):
    '''
    stacking algorithm
    stack='auto' results in an approximately 2.5:1 x:y axis ratio
    '''
    if str(stack).lower() in 'auto':
        am = '(automatic)'
        ratio = (ar.shape[1]/ar.shape[0])/(75/30)
        if ratio > 1:
            stack = int(ratio)
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
        arr = np.copy(ar[:,::stack])
        for s in l:
            arr[:,s] = arr[:,s] + ar[:,s*stack+1:s*stack+stack].sum(axis=1)
    else:
        if str(stack).lower() in 'auto':
            pass
        else:
            fx.printmsg('WARNING: no stacking applied. be warned: this can result in very large and awkwardly-shaped figures.')
    return arr, stack

def reduce(ar, by=1, verbose=False):
    if verbose:
        fx.printmsg('reducing number of array columns by a factor of %s' % (by))
    return ar[::by]

def distance_normalize(ar, verbose=False):
    if ar[2] == []:
        if verbose:
            fx.printmsg('no gps information for distance normalization')
    else:
        norm_vel = ar[0]['rhf_sps'] * (ar[2]['sec_elapsed']/ar[2]['meters']) # should end up as array of samples per meter
        # takes (array, [transform values to broadcast], axis)
        ar[1] = np.repeat(ar[1], norm_vel, axis=1)
        ar[1] = reduce(ar[1], by=np.max(norm_vel))
    return ar