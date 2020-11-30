import os
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
    Shows a y-log histogram of data value distribution.

    :param numpy.ndarray ar: The radar array
    :param bool verbose: Verbose, defaults to False
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

def spectrogram(ar, header, freq, tr='auto', verbose=True):
    """
    Displays a spectrogram of the center trace of the array. This is for testing purposes and not accessible from the command prompt.

    :param numpy.ndarray ar: The radar array
    :param dict header: The file header dictionary
    :type tr: int or str
    :param tr: The trace to display the spectrogram for. Defaults to "auto" but can be an integer representing the trace number to plot. "auto" will pick a trace roughly halfway through the array.
    :param bool verbose: Verbose, defaults to False
    """
    import obspy.imaging.spectrogram as sg # buried here, to avoid obspy compatibility issues
    if tr == 'auto':
        tr = int(ar.shape[1] / 2)
    if verbose:
        fx.printmsg('converting trace %s to frequency domain and drawing spectrogram...' % (tr))
    samp_rate = header['samp_freq']
    trace = ar.T[tr]
    sg.spectrogram(data=trace, samp_rate=samp_rate, wlen=samp_rate/1000, per_lap = 0.99, dbscale=True,
             title='Trace %s Spectrogram - Antenna Frequency: %.2E Hz - Sampling Frequency: %.2E Hz' % (tr, freq, samp_rate))

def radargram(ar, ant, header, freq, figsize='auto', gain=1, stack=1, x='seconds', z='nanoseconds', title=True,
              colormap='gray', colorbar=False, absval=False, noshow=False, win=None, outfile='readgssi_plot', zero=2,
              zoom=[0,0,0,0], dpi=150, showmarks=False, verbose=False):
    """
    Function that creates, modifies, and saves matplotlib plots of radargram images. For usage information, see :doc:`plotting`.

    :param numpy.ndarray ar: The radar array
    :param int ant: Antenna channel number
    :param dict header: Radar file header dictionary
    :param int freq: Antenna frequency
    :param float plotsize: The height of the output plot in inches
    :param float gain: The gain applied to the image. Must be positive but can be between 0 and 1 to reduce gain.
    :param int stack: Number of times the file was stacked horizontally. Used to calculate traces on the X axis.
    :param str x: The units to display on the x-axis during plotting. Defaults to :py:data:`x='seconds'`. Acceptable values are :py:data:`x='distance'` (which sets to meters), :py:data:`'km'`, :py:data:`'m'`, :py:data:`'cm'`, :py:data:`'mm'`, :py:data:`'kilometers'`, :py:data:`'meters'`, etc., for distance; :py:data:`'seconds'`, :py:data:`'s'`, :py:data:`'temporal'` or :py:data:`'time'` for seconds, and :py:data:`'traces'`, :py:data:`'samples'`, :py:data:`'pulses'`, or :py:data:`'columns'` for traces.
    :param str z: The units to display on the z-axis during plotting. Defaults to :py:data:`z='nanoseconds'`. Acceptable values are :py:data:`z='depth'` (which sets to meters), :py:data:`'m'`, :py:data:`'cm'`, :py:data:`'mm'`, :py:data:`'meters'`, etc., for depth; :py:data:`'nanoseconds'`, :py:data:`'ns'`, :py:data:`'temporal'` or :py:data:`'time'` for seconds, and :py:data:`'samples'` or :py:data:`'rows'` for samples.
    :param bool title: Whether to add a title to the figure. Defaults to True.
    :param matplotlib.colors.Colormap colormap: The matplotlib colormap to use, defaults to 'gray' which is to say: the same as the default RADAN colormap
    :param bool colorbar: Whether to draw the colorbar. Defaults to False.
    :param bool absval: Whether to draw the array with an absolute value scale. Defaults to False.
    :param bool noshow: Whether to suppress the matplotlib figure GUI window. Defaults to False, meaning the dialog will be displayed.
    :param int win: Window size for background removal filter :py:func:`readgssi.filtering.bgr` to display in plot title.
    :param str outfile: The name of the output file. Defaults to 'readgssi_plot.png' in the current directory.
    :param int zero: The zero point. This represents the number of samples sliced off the top of the profile by the timezero option in :py:func:`readgssi.readgssi.readgssi`.
    :param list[int,int,int,int] zoom: Zoom extents for matplotlib plots. Must pass a list of four integers: :py:data:`[left, right, up, down]`. Since the z-axis begins at the top, the "up" value is actually the one that displays lower on the page. All four values are axis units, so if you are working in nanoseconds, 10 will set a limit 10 nanoseconds down. If your x-axis is in seconds, 6 will set a limit 6 seconds from the start of the survey. It may be helpful to display the matplotlib interactive window at full extents first, to determine appropriate extents to set for this parameter. If extents are set outside the boundaries of the image, they will be set back to the boundaries. If two extents on the same axis are the same, the program will default to plotting full extents for that axis.
    :param int dpi: The dots per inch value to use when creating images. Defaults to 150.
    :param bool showmarks: Whether to plot user marks as vertical lines. Defaults to False.
    :param bool verbose: Verbose, defaults to False
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
        fig, ax = plt.subplots(figsize=(figx, figy), dpi=dpi)
    else:
        if verbose:
            fx.printmsg('plotting with gain=%s...' % gain)
        fig, ax = plt.subplots()

    mean = np.mean(ar)
    if verbose:
        fx.printmsg('image stats')
        fx.printmsg('size:               %sx%s' % (ar.shape[0], ar.shape[1]))
        fx.printmsg('mean:               %.3f' % mean)

    if absval:
        fx.printmsg('plotting absolute value of array gradient')
        ar = np.abs(np.gradient(ar, axis=1))
        flip = 1
        ll = np.min(ar)
        ul = np.max(ar)
        std = np.std(ar)
    else:
        if mean > 1000:
            fx.printmsg('WARNING: mean pixel value is very high. consider filtering with -t')
        flip = 1
        std = np.std(ar)
        ll = mean - (std * 3) # lower color limit
        ul = mean + (std * 3) # upper color limit
        fx.printmsg('stdev:              %.3f' % std)
        fx.printmsg('lower color limit:  %.2f [mean - (3 * stdev)]' % (ll))
        fx.printmsg('upper color limit:  %.2f [mean + (3 * stdev)]' % (ul))

    # X scaling routine
    if (x == None) or (x in 'seconds'): # plot x as time by default
        xmax = header['sec']
        xlabel = 'Time (s)'
    else:
        if (x in ('cm', 'm', 'km')) and (header['rhf_spm'] > 0): # plot as distance based on unit
            xmax = ar.shape[1] / header['rhf_spm']
            if 'cm' in x:
                xmax = xmax * 100.
            if 'km' in x:
                xmax = xmax / 1000.
            xlabel = 'Distance (%s)' % (x)
        else: # else we plot in units of stacked traces
            if header['rhf_spm'] == 0:
                fx.printmsg('samples per meter value is zero. plotting trace numbers instead.')
            xmax = ar.shape[1] # * float(stack)
            xlabel = 'Trace number'
            if stack > 1:
                xlabel = 'Trace number (after %sx stacking)' % (stack)
    # finally, relate max scale value back to array shape in order to set matplotlib axis scaling
    try:
        xscale = ar.shape[1]/xmax
    except ZeroDivisionError:
        fx.printmsg('ERROR: cannot plot x-axis in "%s" mode; header value is zero. using time instead.' % (x))
        xmax = header['sec']
        xlabel = 'Time (s)'
        xscale = ar.shape[1]/xmax

    zmin = 0
    # Z scaling routine
    if (z == None) or (z in 'nanoseconds'): # plot z as time by default
        zmax = header['rhf_range'] #could also do: header['ns_per_zsample'] * ar.shape[0] * 10**10 / 2
        zlabel = 'Two-way time (ns)'
    else:
        if z in ('mm', 'cm', 'm'): # plot z as TWTT based on unit and cr/rhf_epsr value
            zmax = header['rhf_depth'] - header['rhf_top']
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
                     norm=colors.SymLogNorm(linthresh=float(std)/float(gain), linscale=flip,
                                            vmin=ll, vmax=ul), extent=extent)
    except:
        fx.printmsg('ERROR: matplotlib did not accept colormap "%s", using gray instead' % colormap)
        fx.printmsg('see examples here: https://matplotlib.org/users/colormaps.html#grayscale-conversion')
        img = ax.imshow(ar, cmap='gray', clim=(ll, ul), interpolation='bicubic', aspect=float(zscale)/float(xscale),
                     norm=colors.SymLogNorm(linthresh=float(std)/float(gain), linscale=flip,
                                            vmin=ll, vmax=ul), extent=extent)

    # user marks
    if showmarks:
        if verbose:
            fx.printmsg('plotting marks at traces: %s' % header['marks'])
        for mark in header['marks']:
            plt.axvline(x=mark/xscale, color='r', linestyle=(0, (14,14)), linewidth=1, alpha=0.7)

    # zooming
    if zoom != [0,0,0,0]: # if zoom is set
        zoom = fx.zoom(zoom=zoom, extent=extent, x=x, z=z, verbose=verbose) # figure out if the user set extents properly
    else:
        zoom = extent # otherwise, zoom is full extents
    if zoom != extent: # if zoom is set correctly, then set new axis limits
        if verbose:
            fx.printmsg('zooming in to %s [xmin, xmax, ymax, ymin]' % zoom)
        ax.set_xlim(zoom[0], zoom[1])
        ax.set_ylim(zoom[2], zoom[3])
        # add zoom extents to file name via the Seth W. Campbell honorary naming scheme
        outfile = fx.naming(outfile=outfile, zoom=[int(i) for i in zoom])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(zlabel)

    if colorbar:
        fig.colorbar(img)
    if title:
        try:
            antfreq = freq[ant]
        except TypeError:
            antfreq = freq
        title = '%s - %s MHz - stacking: %s - gain: %s' % (
                    os.path.basename(header['infile']), antfreq, stack, gain)
        if win:
            if win == 0:
                win = 'full'
            title = '%s - bgr: %s' % (title, win)
        plt.title(title)
    if figx / figy >=1: # if x is longer than y (avoids plotting error where data disappears for some reason)
        plt.tight_layout()#pad=fig.get_size_inches()[1]/4.) # then it's ok to call tight_layout()
    else:
        try:
            # the old way of handling
            #plt.tight_layout(w_pad=2, h_pad=1)

            # the new way of handling
            fx.printmsg('WARNING: axis lengths are funky. using alternative sizing method. please adjust manually in matplotlib gui.')
            figManager = plt.get_current_fig_manager()
            try:
                figManager.window.showMaximized()
            except:
                figManager.resize(*figManager.window.maxsize())
            for item in ([ax.xaxis.label, ax.yaxis.label] +
                        ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(5)
            ax.title.set_fontsize(7)
            plt.draw()
            fig.canvas.start_event_loop(0.1)
            plt.tight_layout()
        except:
            fx.printmsg('WARNING: tight_layout() raised an error because axis lengths are funky. please adjust manually in matplotlib gui.')
    if outfile != 'readgssi_plot':
        # if outfile doesn't match this then save fig with the outfile name
        if verbose:
            fx.printmsg('saving figure as %s.png' % (outfile))
        plt.savefig('%s.png' % (outfile), dpi=dpi, bbox_inches='tight')
    else:
        # else someone has called this function from outside and forgotten the outfile field
        if verbose:
            fx.printmsg('saving figure as %s_%sMHz.png with dpi=%s' % (os.path.splitext(header['infile'])[0], freq, dpi))
        plt.savefig('%s_%sMHz.png' % (os.path.splitext(header['infile'])[0], freq), bbox_inches='tight')
    if noshow:
        if verbose:
            fx.printmsg('not showing matplotlib')
        plt.close()
    else:
        if verbose:
            fx.printmsg('showing matplotlib figure...')
        plt.show()
