import numpy as np
from scipy.ndimage.filters import uniform_filter1d
from scipy.signal import firwin, lfilter
import readgssi.functions as fx

"""
Mathematical filtering routines for array manipulation
Written in part by François-Xavier Simon (@fxsimon)
"""

def bgr(ar, header, win=0, verbose=False):
    """
    Horizontal background removal (BGR). Subtracts off row averages for full-width or window-length slices. For usage see :ref:`Getting rid of horizontal noise`.

    :param numpy.ndarray ar: The radar array
    :param dict header: The file header dictionary
    :param int win: The window length to process. 0 resolves to full-width, whereas positive integers dictate the window size in post-stack traces.
    :rtype: :py:class:`numpy.ndarray`
    """
    if (int(win) > 1) & (int(win) < ar.shape[1]):
        window = int(win)
        how = 'boxcar (%s trace window)' % window
    else:
        how = 'full only'
    if verbose:
        fx.printmsg('removing horizontal background using method=%s...' % (how))
    i = 0
    for row in ar:          # each row
        mean = np.mean(row)
        ar[i] = row - mean
        i += 1
    if how != 'full only':
        if window < 10:
            fx.printmsg('WARNING: BGR window size is very short. be careful, this may obscure horizontal layering')
        if window < 3:
            window = 3
        elif (window / 2. == int(window / 2)):
            window = window + 1
        ar -= uniform_filter1d(ar, size=window, mode='constant', cval=0, axis=1)

    return ar

def dewow(ar, verbose=False):
    """
    Polynomial dewow filter. Written by fxsimon.
    
    .. warning:: This filter is still experimental.

    :param numpy.ndarray ar: The radar array
    :param bool verbose: Verbose, default is False
    :rtype: :py:class:`numpy.ndarray`
    """
    fx.printmsg('WARNING: dewow filter is experimental')
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

def bp(ar, header, freqmin, freqmax, zerophase=True, verbose=False):
    """
    Vertical butterworth bandpass. This filter is not as effective as :py:func:`triangular` and thus is not available through the command line interface or through :py:func:`readgssi.readgssi.readgssi`.

    Filter design and implementation are dictated by :py:func:`obspy.signal.filter.bandpass`.

    :param np.ndarray ar: The radar array
    :param dict header: The file header dictionary
    :param int freqmin: The lower corner of the bandpass
    :param int freqmax: The upper corner of the bandpass
    :param bool zerophase: Whether to run the filter forwards and backwards in order to counteract the phase shift
    :param bool verbose: Verbose, defaults to False
    :rtype: :py:class:`numpy.ndarray`
    """
    from obspy.signal.filter import bandpass

    if verbose:
        fx.printmsg('vertical butterworth bandpass filter')
        fx.printmsg('NOTE: better results are achieved with readgssi.filtering.triangular()')
    #samp_freq = 1 / ((header['rhf_depth'] * 2) / header['cr'] / header['rh_nsamp'])
    samp_freq = header['samp_freq']
    freqmin = freqmin * 10 ** 6
    freqmax = freqmax * 10 ** 6
    
    corners = 1

    if verbose:
        fx.printmsg('sampling frequency:       %.2E Hz' % samp_freq)
        fx.printmsg('minimum filter frequency: %.2E Hz' % freqmin)
        fx.printmsg('maximum filter frequency: %.2E Hz' % freqmax)
        fx.printmsg('corners: %s, zerophase: %s' % (corners, zerophase))
    
    i = 0
    for t in ar.T:
        f = bandpass(data=t, freqmin=freqmin, freqmax=freqmax, df=samp_freq, corners=corners, zerophase=zerophase)
        ar[:,i] = f
        i += 1
    return ar

def triangular(ar, header, freqmin, freqmax, zerophase=True, verbose=False):
    """
    Vertical triangular FIR bandpass. This filter is designed to closely emulate that of RADAN.

    Filter design is implemented by :py:func:`scipy.signal.firwin` with :code:`numtaps=25` and implemented with :py:func:`scipy.signal.lfilter`.

    .. note:: This function is not compatible with scipy versions prior to 1.3.0.

    :param np.ndarray ar: The radar array
    :param dict header: The file header dictionary
    :param int freqmin: The lower corner of the bandpass
    :param int freqmax: The upper corner of the bandpass
    :param bool zerophase: Whether to run the filter forwards and backwards in order to counteract the phase shift
    :param bool verbose: Verbose, defaults to False
    :rtype: :py:class:`numpy.ndarray`
    """
    if verbose:
        fx.printmsg('vertical triangular FIR bandpass filter')
    #samp_freq = 1 / ((header['rhf_depth'] * 2) / header['cr'] / header['rh_nsamp'])
    samp_freq = header['samp_freq']
    freqmin = freqmin * 10 ** 6
    freqmax = freqmax * 10 ** 6
    
    numtaps = 25

    if verbose:
        fx.printmsg('sampling frequency:       %.2E Hz' % samp_freq)
        fx.printmsg('minimum filter frequency: %.2E Hz' % freqmin)
        fx.printmsg('maximum filter frequency: %.2E Hz' % freqmax)
        fx.printmsg('numtaps: %s, zerophase: %s' % (numtaps, zerophase))

    filt = firwin(numtaps=numtaps, cutoff=[freqmin, freqmax], window='triangle', pass_zero='bandpass', fs=samp_freq)

    far = lfilter(filt, 1.0, ar, axis=0).copy()
    if zerophase:
        far = lfilter(filt, 1.0, far[::-1], axis=0)[::-1]

    return far
