import readgssi.functions as fx
import numpy as np
import pandas as pd

def flip(ar, verbose=False):
    """
    Read the array backwards. Used to reverse line direction. Usage covered in the :ref:`Reversing` tutorial section.
    
    :param numpy.ndarray ar: Input data array
    :param bool verbose: Verbose, defaults to False
    :rtype: radar array (:py:class:`numpy.ndarray`)

    """
    if verbose:
        fx.printmsg('flipping radargram...')
    return ar.T[::-1].T

def reducex(ar, header, by=1, chnum=1, number=1, verbose=False):
    """
    Reduce the number of traces in the array by a number. Not the same as :py:func:`stack` since it doesn't sum adjacent traces, however :py:func:`stack` uses it to resize the array prior to stacking.

    Used by :py:func:`stack` and :py:func:`distance_normalize` but not accessible from the command line or :py:func:`readgssi.readgssi`.

    :param numpy.ndarray ar: Input data array
    :param int by: Factor to reduce by. Default is 1.
    :param int chnum: Chunk number to display in console. Default is 1.
    :param int number: Number of chunks to display in console. Default is 1.
    :param bool verbose: Verbose, defaults to False.
    :rtype: radar array (:py:class:`numpy.ndarray`)

    """
    if verbose:
        if chnum/10 == int(chnum/10):
            fx.printmsg('%s/%s reducing %sx%s chunk by a factor of %s...' % (chnum, number, ar.shape[0], ar.shape[1], by))
    return ar[:,::by]

def stack(ar, header, stack='auto', verbose=False):
    """
    Stacking algorithm. Stacking is the process of summing adjacent traces in order to reduce noise --- the thought being that random noise around zero will cancel out and data will either add or subtract, making it easier to discern.

    It is also useful for displaying long lines on a computer screen. Usage is covered in the :ref:`stacking` section of the tutorial.

    :py:data:`stack='auto'` results in an approximately 2.5:1 x:y axis ratio. :py:data:`stack=3` sums three adjacent traces into a single trace across the width of the array.

    :param numpy.ndarray ar: Input data array
    :param int by: Factor to stack by. Default is "auto".
    :rtype: radar array (:py:class:`numpy.ndarray`)

    """
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
            fx.printmsg('NOTE: stacking must be indicated with an integer greater than 1, "auto", or None.')
            fx.printmsg('      a stacking value of 1 equates to None. "auto" will attempt to stack to')
            fx.printmsg('      about a 2.5:1 x to y axis ratio. the result will not be stacked.')
            stack = 1
    if stack > 1:
        if verbose:
            fx.printmsg('stacking %sx %s...' % (stack, am))
        i = list(range(stack))
        l = list(range(int(ar.shape[1]/stack)))
        arr = np.copy(reducex(ar=ar, by=stack, header=header, verbose=verbose))
        for s in l:
            arr[:,s] = arr[:,s] + ar[:,s*stack+1:s*stack+stack].sum(axis=1)
    else:
        arr = ar
        if str(stack0).lower() in 'auto': # this happens when distance normalization reduces the file
            pass
        else:
            fx.printmsg('WARNING: no stacking applied. this can result in very large and awkwardly-shaped figures.')

    if header['rh_nchan'] == 1:
        # this is a hack to prevent the rhf_spx vars from being changed multiple times
        # when stacking a multichannel file. this will go away when each array has its
        # own header and thus each can be dealt with individually.
        if header['rhf_sps'] != 0:
            header['rhf_sps'] = header['rhf_sps'] / stack
        if header['rhf_spm'] != 0:
            header['rhf_spm'] = header['rhf_spm'] / stack
    else:
        try:
            if header['spx_updates']:
                pass
            else:
                if header['rhf_sps'] != 0:
                    header['rhf_sps'] = header['rhf_sps'] / stack
                if header['rhf_spm'] != 0:
                    header['rhf_spm'] = header['rhf_spm'] / stack
                header['spx_updates'] = True
        except KeyError:
            header['spx_updates'] = False

    return header, arr, stack

def distance_normalize(header, ar, gps, verbose=False):
    """
    Distance normalization algorithm. Uses a GPS array to calculate expansion and contraction needed to convert from time-triggered to distance-normalized sampling interval. Then, the samples per meter is recalculated and inserted into the header for proper plotting.

    Usage described in the :ref:`Distance normalization` section of the tutorial.

    :param dict header: Input data array
    :param numpy.ndarray ar: Input data array
    :param pandas.DataFrame gps: GPS data from :py:func:`readgssi.gps.readdzg`. This is used to calculate the expansion and compression needed to normalize traces to distance.
    :param bool verbose: Verbose, defaults to False.
    :rtype: header (:py:class:`dict`), radar array (:py:class:`numpy.ndarray`), gps (False or :py:class:`pandas.DataFrame`)

    """
    if gps.empty:
        if verbose:
            fx.printmsg('no gps information for distance normalization')
    else:
        if verbose:
            fx.printmsg('normalizing GPS velocity records...')
        while np.min(gps['velocity']) < 0.01: # fix zero and negative velocity values
            gps['velocity'].replace(gps['velocity'].min(), 0.01, inplace=True)
        norm_vel = (gps['velocity'] * (1/gps['velocity'].max())*100).to_frame('normalized') # should end up as dataframe with one column
        # upsample to match radar array shape
        nanosec_samp_rate = int((1/header['rhf_sps'])*10**9) # nanoseconds
        start = np.datetime64(str(norm_vel.index[0])) - np.timedelta64(nanosec_samp_rate*(gps.iloc[0,0]), 'ns')
        newdf = pd.DataFrame(index=pd.date_range(start=start, periods=ar.shape[1], freq=str(nanosec_samp_rate)+'N', tz='UTC'))
        norm_vel = pd.concat([norm_vel, newdf], axis=1).interpolate('time').bfill()
        del newdf
        norm_vel = norm_vel.round().astype(int, errors='ignore')#, casting='unsafe')

        try:
            rm = int(round(ar.shape[1] / (norm_vel.shape[0] - ar.shape[1])))
            norm_vel = norm_vel.drop(norm_vel.index[::rm])
        except ZeroDivisionError as e:
            fx.printmsg('equal length radar & velocity arrays; no size adjustment')
        for i in range(0,abs(norm_vel.shape[0]-ar.shape[1])):
            s = pd.DataFrame({'normalized':[norm_vel['normalized'].iloc[-1]]}) # hacky, but necessary
            norm_vel = pd.concat([norm_vel, s])

        nvm = int(round(norm_vel['normalized'].mean()))
        proc = np.ndarray((ar.shape[0], 0))
        if verbose:
            fx.printmsg('expanding array using mean of normalized velocity %.2f' % (norm_vel['normalized'].mean()))
        on, i = 0, 0
        for c in np.array_split(ar, nvm, axis=1):
            # takes (array, [transform values to broadcast], axis)
            p = np.repeat(c, norm_vel['normalized'].astype(int, errors='ignore').values[on:on+c.shape[1]], axis=1)
            p = reducex(p, header=header, by=nvm, chnum=i, number=nvm, verbose=verbose)
            proc = np.concatenate((proc, p), axis=1)
            on = on + c.shape[1]
            i += 1
        if verbose:
            fx.printmsg('total GPS distance: %.2f m' % gps['meters'].iloc[-1])
            fx.printmsg('replacing old traces per meter value of %s with %s' % (header['rhf_spm'],
                                                                            ar.shape[1] / gps['meters'].iloc[-1]))
        header['rhf_spm'] = proc.shape[1] / gps['meters'].iloc[-1]
        header['rhf_sps'] = 0
    return header, proc, gps
