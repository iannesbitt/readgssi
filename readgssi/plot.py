import os
import obspy.imaging.spectrogram as sg
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import readgssi.functions as fx
from readgssi.constants import *

"""
contains several plotting functions
"""

def histogram(ar, verbose=True):
    """
    shows a y-log histogram of data value distribution
    """
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
    """
    displays a spectrogram of the center trace of the array

    this is for testing purposes and not accessible from the command prompt
    """
    tr = int(ar.shape[1] / 2)
    if verbose:
        fx.printmsg('converting trace %s to frequency domain and drawing spectrogram...' % (tr))
    samp_rate = 1 / header['ns_per_zsample']
    trace = ar.T[tr]
    sg.spectrogram(data=trace, samp_rate=samp_rate, wlen=samp_rate/1000, per_lap = 0.99, dbscale=True,
             title='Trace %s Spectrogram - Antenna Frequency: %.2E Hz - Sampling Frequency: %.2E Hz' % (tr, freq, samp_rate))

def radargram(ar, header, freq, verbose=False, figsize='auto', gain=1, stack=1, x='seconds', z='nanoseconds', title=True,
              colormap='Greys', colorbar=False, noshow=False, win=None, outfile='readgssi_plot', aspect='auto', zero=2,
              zoom=[0,0,0,0]):
    """
    let's do some matplotlib

    requirements:
    ar          - a radar array
    verbose     - boolean, whether to print progress. defaults to True
    plotsize    - the size of the plot in inches
    zero        - the zero point (number of samples sliced off the top of the profile by the timezero option)
    stack       - number of times stacked horizontally
    colormap    - the matplotlib colormap to use, defaults to 'Greys' which is to say: the same as the default RADAN colormap
    colorbar    - boolean, whether to draw the colorbar. defaults to False
    noshow      - boolean, whether to bring up the matplotlib figure dialog when drawing. defaults to False, meaning the dialog will be displayed.
    outfile     - name of the output file. defaults to 'readgssi_plot.png' in the current directory.
    """

    # having lots of trouble with this line not being friendly with figsize tuple (integer coercion-related errors)
    # so we will force everything to be integers explicitly
    if figsize != 'auto':
        figx, figy = int(int(figsize)*int(int(ar.shape[1])/int(ar.shape[0]))), int(figsize)-1 # force to integer instead of coerce
        if figy <= 1:
            figy += 1 # avoid zero height error in y dimension
        if figx <= 1:
            figx += 1 # avoid zero height error in x dimension
        if verbose:
            fx.printmsg('plotting %sx%sin image with gain=%s...' % (figx, figy, gain))
        fig, ax = plt.subplots(figsize=(figx, figy), dpi=300)
    else:
        if verbose:
            fx.printmsg('plotting with gain=%s...' % gain)
        fig, ax = plt.subplots()

    zmin = 0
    mean = np.mean(ar)
    if mean > 1000:
        fx.printmsg('WARNING: mean pixel value is very high. consider filtering with -t')
    std = np.std(ar)
    ll = mean - (std * 3) # lower color limit
    ul = mean + (std * 3) # upper color limit
    if verbose:
        fx.printmsg('image stats')
        fx.printmsg('size:               %sx%s' % (ar.shape[0], ar.shape[1]))
        fx.printmsg('mean:               %.3f' % mean)
        fx.printmsg('stdev:              %.3f' % std)
        fx.printmsg('lower color limit:  %.2f [mean - (3 * stdev)]' % ll)
        fx.printmsg('upper color limit:  %.2f [mean + (3 * stdev)]' % ul)

    # X scaling routine
    if (x == None) or (x in 'seconds'): # plot x as time by default
        xmax = header['sec']
        xlabel = 'Time (s)'
    else:
        if x in ('cm', 'm', 'km'): # plot as distance based on unit
            xmax = (ar.shape[1] * float(stack)) / header['rhf_spm']
            if 'cm' in x:
                xmax = xmax * 100.
            if 'km' in x:
                xmax = xmax / 1000.
            xlabel = 'Distance (%s)' % (x)
        else: # else we plot in units of stacked traces
            xmax = ar.shape[1] # * float(stack)
            xlabel = 'Trace (after stacking)'
    # finally, relate max scale value back to array shape in order to set matplotlib axis scaling
    try:
        xscale = ar.shape[1]/xmax
    except ZeroDivisionError:
        fx.printmsg('ERROR: cannot plot x-axis in "%s" mode; header value is zero. using time instead.' % (x))
        xmax = header['sec']
        xlabel = 'Time (s)'
        xscale = ar.shape[1]/xmax

    # Z scaling routine
    if (z == None) or (z in 'nanoseconds'): # plot z as time by default
        zmax = header['ns_per_zsample'] * ar.shape[0] * 10**9
        zlabel = 'Two-way time (ns)'
    else:
        if z in ('mm', 'cm', 'm'): # plot z as TWTT based on unit and cr/rhf_epsr value
            zmax = header['rhf_depth']
            if 'cm' in z:
                zmax = zmax * 100.
            if 'mm' in z:
                zmax = zmax * 1000.
            zlabel = r'Depth at $\epsilon_r$=%.2f (%s)' % (header['rhf_epsr'], z)
        else: # else we plot in units of samples
            zmin = zero
            zmax = ar.shape[0] + zero
            zlabel = 'Sample'
    # finally, relate max scale value back to array shape in order to set matplotlib axis scaling
    try:
        zscale = ar.shape[0]/zmax
    except ZeroDivisionError: # apparently this can happen even in genuine GSSI files
        fx.printmsg('ERROR: cannot plot z-axis in "%s" mode; header max value is zero. using samples instead.' % (z))
        zmax = ar.shape[0]
        zlabel = 'Sample'
        zscale = ar.shape[0]/zmax

    if verbose:
        fx.printmsg('xmax: %.4f %s, zmax: %.4f %s' % (xmax, xlabel, zmax, zlabel))

    extent = [0, xmax, zmax, zmin]

    try:
        if verbose:
            fx.printmsg('attempting to plot with colormap %s' % (colormap))
        img = ax.imshow(ar, cmap=colormap, clim=(ll, ul), interpolation='bicubic', aspect=float(zscale)/float(xscale),
                     norm=colors.SymLogNorm(linthresh=float(std)/float(gain), linscale=1,
                                            vmin=ll, vmax=ul), extent=extent)
    except:
        fx.printmsg('ERROR: matplotlib did not accept colormap "%s", using viridis instead' % colormap)
        fx.printmsg('see examples here: https://matplotlib.org/users/colormaps.html#grayscale-conversion')
        img = ax.imshow(ar, cmap='Greys', clim=(ll, ul), interpolation='bicubic', aspect=float(zscale)/float(xscale),
                     norm=colors.SymLogNorm(linthresh=float(std)/float(gain), linscale=1,
                                            vmin=ll, vmax=ul), extent=extent)

    # zooming
    if zoom != [0,0,0,0]: # if zoom is set
        for i in range(4):
            if zoom[i] < 0:
                zoom[i] = 0
                if verbose:
                    fx.printmsg('WARNING: %s zoom limit was negative, now set to zero' % ['left','right','up','down'])
        if (zoom[0] > 0) or (zoom[1] > 0): # if a LR value has been set
            if zoom[0] > extent[1]: # if L zoom is beyond extents, set back to extent limit
                zoom[0] = extent[1]
                if verbose:
                    fx.printmsg('WARNING: left zoom limit out of bounds (limit is %s %s)' % (extent[1], x))
            if zoom[1] > extent[1]: # if R zoom is beyond extents, set back to extent limit
                zoom[1] = extent[1]
                if verbose:
                    fx.printmsg('WARNING: right zoom limit out of bounds (limit is %s %s)' % (extent[1], x))
            if zoom[0] == zoom[1]: # if LR extents are impossible,
                zoom[0] = extent[0] # set both to full extents
                zoom[1] = extent[1]
                if verbose:
                    fx.printmsg('WARNING: left and right zoom values were equal or both out of bounds, now set to full extent')
        else:
            zoom[0] = extent[0]
            zoom[1] = extent[1]
        if (zoom[2] > 0) or (zoom[3] > 0): # if a UD value has been set
            if zoom[2] > extent[2]: # if upper zoom is beyond extents, set back to extent limit
                zoom[2] = extent[2]
                if verbose:
                    fx.printmsg('WARNING: upper zoom limit out of bounds (limit is %s %s)' % (extent[3], x))
            if zoom[3] > extent[2]: # if lower zoom is beyond extents, set back to extent limit
                zoom[3] = extent[2]
                if verbose:
                    fx.printmsg('WARNING: lower zoom limit out of bounds (limit is %s %s)' % (extent[3], x))
            if zoom[2] == zoom[3]: # if UD extents are impossible,
                zoom[2] = extent[2] # set both to full extents
                zoom[3] = extent[3]
                if verbose:
                    fx.printmsg('WARNING: top and bottom zoom values were equal or both out of bounds, now set to full extent')
        else:
            zoom[2] = extent[2]
            zoom[3] = extent[3]
    else:
        zoom = extent
    if zoom != extent:
        if verbose:
            fx.printmsg('zooming in to %s [xmin, xmax, ymax, ymin]' % zoom)
        ax.set_xlim(zoom[0], zoom[1])
        ax.set_ylim(zoom[2], zoom[3])

        # adding to the Seth W. Campbell honorary naming scheme
        outfile = '%sZ' % (outfile)
        for ex in zoom:
            outfile = '%s.%s' % (outfile, ex)


    ax.set_xlabel(xlabel)
    ax.set_ylabel(zlabel)

    if colorbar:
        fig.colorbar(img)
    if title:
        title = '%s - %s MHz - stacking: %s - gain: %s' % (
                    os.path.basename(header['infile']), freq, stack, gain)
        if win:
            if win == 0:
                win = 'full'
            title = '%s - bgr: %s' % (title, win)
        plt.title(title)
    if figx / figy >=1: # if x is longer than y (avoids plotting error where data disappears for some reason)
        plt.tight_layout()#pad=fig.get_size_inches()[1]/4.) # then it's ok to call tight_layout()
    else:
        try:
            plt.tight_layout(w_pad=2, h_pad=1)
            fx.printmsg('WARNING: axis lengths are funky. current axis sizes may cut off text. please adjust manually in matplotlib gui.')
        except:
            fx.printmsg('WARNING: tight_layout() raised an error because axis lengths are funky. please adjust manually in matplotlib gui.')
    if outfile != 'readgssi_plot':
        # if outfile doesn't match this then save fig with the outfile name
        if verbose:
            fx.printmsg('saving figure as %s.png' % (outfile))
        plt.savefig('%s.png' % (outfile), bbox_inches='tight')
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
