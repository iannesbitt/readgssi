import os
import obspy.imaging.spectrogram as sg
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import readgssi.functions as fx
from readgssi.constants import *

'''
contains several plotting functions
'''

def histogram(ar, verbose=True):
    '''
    shows a y-log histogram of data value distribution
    '''
    mean = np.mean(ar)
    std = np.std(ar)
    ll = mean - (std * 3) # lower color limit
    ul = mean + (std * 3) # upper color limit

    if verbose:
        fx.printmsg('drawing log histogram...')
        fx.printmsg('mean:               %s (if high, use background removal)' % mean)
        fx.printmsg('stdev:              %s' % std)
        fx.printmsg('lower limit:        %s [mean - (3 * stdev)]' % ll)
        fx.printmsg('upper limit:        %s [mean + (3 * stdev)]' % ul)
    fig = plt.figure()
    hst = plt.hist(ar.ravel(), bins=256, range=(ll, ul), fc='k', ec='k')
    plt.yscale('log', nonposy='clip')
    plt.show()

def spectrogram(ar, header, freq, verbose=True):
    '''
    displays a spectrogram of the center trace of the array

    this is for testing purposes and not accessible from the command prompt
    '''
    tr = int(ar.shape[1] / 2)
    if verbose:
        fx.printmsg('converting trace %s to frequency domain and drawing spectrogram...' % (tr))
    samp_rate = 1 / (header['rhf_depth'] / header['cr'] / header['rh_nsamp'])
    trace = ar.T[tr]
    sg.spectrogram(data=trace, samp_rate=samp_rate, wlen=samp_rate/1000, per_lap = 0.99, dbscale=True,
             title='Trace %s Spectrogram - Antenna Frequency: %.2E Hz - Sampling Frequency: %.2E Hz' % (tr, freq, samp_rate))

def radargram(ar, header, freq, verbose=True, figsize='auto', gain=1, stack='auto', colormap='Greys', colorbar=False, noshow=False, outfile='readgssi_plot'):
    '''
    let's do some matplotlib

    requirements:
    ar   - a radar array
    verbose   - boolean, whether to print progress. defaults to True
    plotsize  - the size of the plot in inches
    stack     - number of times to stack horizontally
    colormap  - the matplotlib colormap to use, defaults to 'Greys' which is to say: the same as the default RADAN colormap
    colorbar  - boolean, whether to draw the colorbar. defaults to False
    noshow    - boolean, whether to bring up the matplotlib figure dialog when drawing. defaults to False, meaning the dialog will be displayed.
    outfile   - name of the output file. defaults to 'readgssi_plot.png' in the current directory.
    '''

    # having lots of trouble with this line not being friendly with figsize tuple (integer coercion-related errors)
    # so we will force everything to be integers explicitly
    if figsize != 'auto':
        figx, figy = int(int(figsize)*int(int(ar.shape[1])/int(ar.shape[0]))), int(figsize) # force to integer instead of coerce
        if verbose:
            fx.printmsg('plotting %sx%sin image with gain=%s...' % (figx, figy, gain))
        fig = plt.figure(figsize=(figx, figy-1), dpi=150)
    else:
        if verbose:
            fx.printmsg('plotting with gain=%s...' % gain)
        fig = plt.figure()

    mean = np.mean(ar)
    std = np.std(ar)
    ll = mean - (std * 3) # lower color limit
    ul = mean + (std * 3) # upper color limit
    if verbose:
        fx.printmsg('image stats')
        fx.printmsg('mean:               %s' % mean)
        fx.printmsg('stdev:              %s' % std)
        fx.printmsg('lower color limit:  %s [mean - (3 * stdev)]' % ll)
        fx.printmsg('upper color limit:  %s [mean + (3 * stdev)]' % ul)

    try:
        if verbose:
            fx.printmsg('attempting to plot with colormap %s' % (colormap))
        img = plt.imshow(ar, cmap=colormap, clim=(ll, ul),
                     norm=colors.SymLogNorm(linthresh=float(std)/float(gain), linscale=1,
                                            vmin=ll, vmax=ul),)
    except:
        fx.printmsg('ERROR: matplotlib did not accept colormap "%s", using viridis instead' % colormap)
        fx.printmsg('see examples here: https://matplotlib.org/users/colormaps.html#grayscale-conversion')
        img = plt.imshow(ar, cmap='viridis', clim=(ll, ul),
                     norm=colors.SymLogNorm(linthresh=float(std)/float(gain), linscale=1,
                                            vmin=ll, vmax=ul),)

    if colorbar:
        fig.colorbar(img)
    if verbose:
        plt.title('%s - %s MHz - stacking: %s - gain: %s' % (os.path.basename(header['infile']), freq, stack, gain))
    plt.tight_layout(pad=fig.get_size_inches()[1]/2.)
    if outfile != 'readgssi_plot':
        # if outfile doesn't match this then save fig with the outfile name
        if verbose:
            fx.printmsg('saving figure as %s.png' % (outfile))
        plt.savefig('%s.png' % (outfile))
    else:
        # else someone has called this function from outside and forgotten the outfile field
        if verbose:
            fx.printmsg('saving figure as %s_%sMHz.png' % (os.path.splitext(header['infile'])[0], freq))
        plt.savefig('%s_%sMHz.png' % (os.path.splitext(header['infile'])[0], freq))
    if noshow:
        if verbose:
            fx.printmsg('not showing matplotlib')
        plt.close()
    else:
        if verbose:
            fx.printmsg('showing matplotlib figure...')
        plt.show()
