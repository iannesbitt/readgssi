# coding=utf-8

## readgssi.py
## intended to translate radar data from DZT to other more workable formats.
## DZT is a file format maintained by Geophysical Survey Systems Incorporated (GSSI).
## specifically, this script is intended for use with radar data recorded
## with GSSI SIR 3000 and 4000 field units. Other field unit models may record DZT slightly
## differently, in which case this script may need to be modified.

# readgssi was originally written as matlab code by
# Gabe Lewis, Dartmouth College Department of Earth Sciences.
# matlab code was adapted for python with permission by
# Ian Nesbitt, University of Maine School of Earth and Climate Sciences.
# Copyleft (c) 2017 Ian Nesbitt

# this code is freely available under the GNU Affero General Public License 3.0.
# if you did not receive a copy of the license upon obtaining this software, please visit
# (https://opensource.org/licenses/AGPL-3.0) to obtain a copy.

import sys, getopt, os
import numpy as np
from datetime import datetime, timedelta
import readgssi.functions as fx
import readgssi.plot as plot
from readgssi import translate
from readgssi import filtering
from readgssi import arrayops
from readgssi import config
from readgssi.constants import *
from readgssi.dzt import *
from readgssi.gps import pause_correct


def readgssi(infile, outfile=None, verbose=False, antfreq=None, frmt='python',
             plotting=False, figsize=7, dpi=150, stack=1, x='seconds',
             z='nanoseconds', histogram=False, colormap='gray', colorbar=False,
             zero=[None,None,None,None], gain=1, freqmin=None, freqmax=None, 
             reverse=False, bgr=False, win=0, dewow=False, absval=False,
             normalize=False, specgram=False, noshow=False, spm=None,
             start_scan=0, num_scans=-1, epsr=None, title=True, zoom=[0,0,0,0],
             pausecorrect=False, showmarks=False):
    """
    This is the primary directive function. It coordinates calls to reading, filtering, translation, and plotting functions, and should be used as the overarching processing function in most cases.

    :param str infile: Input DZT data file
    :param str outfile: Base output file name for plots, CSVs, and other products. Defaults to :py:data:`None`, which will cause the output filename to take a form similar to the input. The default will let the file be named via the descriptive naming function :py:data:`readgssi.functions.naming()`.
    :param bool verbose: Whether or not to display (a lot of) information about the workings of the program. Defaults to :py:data:`False`. Can be helpful for debugging but also to see various header values and processes taking place.
    :param int antfreq: User setting for antenna frequency. Defaults to :py:data:`None`, which will cause the program to try to determine the frequency from the antenna name in the header of the input file. If the antenna name is not in the dictionary :py:data:`readgssi.constants.ANT`, the function will try to determine the frequency by decoding integers in the antenna name string.
    :param str frmt: The output format to be passed to :py:mod:`readgssi.translate`. Defaults to :py:data:`None`. Presently, this can be set to :py:data:`frmt='dzt'`, :py:data:`frmt='csv'`, :py:data:`'numpy'`, :py:data:`'gprpy'`, or :py:data:`'object'` (which will return the header dictionary, the image arrays, and the gps coordinates as objects). Plotting will not interfere with output (i.e. you can output to CSV and plot a PNG in the same command).
    :param bool plotting: Whether to plot the radargram using :py:func:`readgssi.plot.radargram`. Defaults to :py:data:`False`.
    :param int figsize: Plot size in inches to be passed to :py:func:`readgssi.plot.radargram`.
    :param int dpi: Dots per inch (DPI) for figure creation.
    :param int stack: Number of consecutive traces to stack (horizontally) using :py:func:`readgssi.arrayops.stack`. Defaults to 1 (no stacking). Especially good for handling long radar lines. Algorithm combines consecutive traces together using addition, which reduces noise and enhances signal. The more stacking is done, generally the clearer signal will become. The tradeoff is that you will reduce the length of the X-axis. Sometimes this is desirable (i.e. for long survey lines).
    :param str x: The units to display on the x-axis during plotting. Defaults to :py:data:`x='seconds'`. Acceptable values are :py:data:`x='distance'` (which sets to meters), :py:data:`'km'`, :py:data:`'m'`, :py:data:`'cm'`, :py:data:`'mm'`, :py:data:`'kilometers'`, :py:data:`'meters'`, etc., for distance; :py:data:`'seconds'`, :py:data:`'s'`, :py:data:`'temporal'` or :py:data:`'time'` for seconds, and :py:data:`'traces'`, :py:data:`'samples'`, :py:data:`'pulses'`, or :py:data:`'columns'` for traces.
    :param str z: The units to display on the z-axis during plotting. Defaults to :py:data:`z='nanoseconds'`. Acceptable values are :py:data:`z='depth'` (which sets to meters), :py:data:`'m'`, :py:data:`'cm'`, :py:data:`'mm'`, :py:data:`'meters'`, etc., for depth; :py:data:`'nanoseconds'`, :py:data:`'ns'`, :py:data:`'temporal'` or :py:data:`'time'` for seconds, and :py:data:`'samples'` or :py:data:`'rows'` for samples.
    :param bool histogram: Whether to plot a histogram of array values at plot time.
    :type colormap: :py:class:`str` or :class:`matplotlib.colors.Colormap`
    :param colormap: Plot using a Matplotlib colormap. Defaults to :py:data:`gray` which is colorblind-friendly and behaves similarly to the RADAN default, but :py:data:`seismic` is a favorite of many due to its diverging nature.
    :param bool colorbar: Whether to display a graded color bar at plot time.
    :param list[int,int,int,int] zero: A list of values representing the amount of samples to slice off each channel. Defaults to :py:data:`None` for all channels, which will end up being set by the :code:`rh_zero` variable in :py:func:`readgssi.dzt.readdzt`.
    :param int gain: The amount of gain applied to plots. Defaults to 1. Gain is applied as a ratio of the standard deviation of radargram values to the value set here.
    :param int freqmin: Minimum frequency value to feed to the vertical triangular FIR bandpass filter :py:func:`readgssi.filtering.triangular`. Defaults to :py:data:`None` (no filter).
    :param int freqmax: Maximum frequency value to feed to the vertical triangular FIR bandpass filter :py:func:`readgssi.filtering.triangular`. Defaults to :py:data:`None` (no filter).
    :param bool reverse: Whether to read the array backwards (i.e. flip horizontally; :py:func:`readgssi.arrayops.flip`). Defaults to :py:data:`False`. Useful for lining up travel directions of files run opposite each other.
    :param int bgr: Background removal filter applied after stacking (:py:func:`readgssi.filtering.bgr`). Defaults to :py:data:`False` (off). :py:data:`bgr=True` must be accompanied by a valid value for :py:data:`win`.
    :param int win: Window size for background removal filter (:py:func:`readgssi.filtering.bgr`). If :py:data:`bgr=True` and :py:data:`win=0`, the full-width row average will be subtracted from each row. If :py:data:`bgr=True` and :py:data:`win=50`, a moving window will calculate the average of 25 cells on either side of the current cell, and subtract that average from the cell value, using :py:func:`scipy.ndimage.uniform_filter1d` with :py:data:`mode='constant'` and :py:data:`cval=0`. This is useful for removing non-uniform horizontal average, but the tradeoff is that it creates ghost data half the window size away from vertical figures, and that a window size set too low will obscure any horizontal layering longer than the window size.
    :param bool dewow: Whether to apply a vertical dewow filter (experimental). See :py:func:`readgssi.filtering.dewow`.
    :param bool absval: If :py:data:`True`, displays the absolute value of the vertical gradient of the array when plotting. Good for displaying faint array features.
    :param bool normalize: Distance normalization (:py:func:`readgssi.arrayops.distance_normalize`). Defaults to :py:data:`False`.
    :param bool specgram: Produce a spectrogram of a trace in the array using :py:func:`readgssi.plot.spectrogram`. Defaults to :py:data:`False` (if :py:data:`True`, defaults to a trace roughly halfway across the profile). This is mostly for debugging and is not currently accessible from the command line.
    :param bool noshow: If :py:data:`True`, this will suppress the matplotlib interactive window and simply save a file. This is useful for processing many files in a folder without user input.
    :param float spm: User-set samples per meter. This overrides the value read from the header, and typically doesn't need to be set if the samples per meter value was set correctly at survey time. This value does not need to be set if GPS input (DZG file) is present and the user sets :py:data:`normalize=True`.
    :param int start_scan: zero based start scan to read data from. Defaults to zero.
    :param int num_scans: number of scans to read from the file, Defaults to -1, which reads from start_scan to end of file.
    :param float epsr: Epsilon_r, otherwise known as relative permittivity, or dielectric constant. This determines the speed at which waves travel through the first medium they encounter. It is used to calculate the profile depth if depth units are specified on the Z-axis of plots.
    :param bool title: Whether to display descriptive titles on plots. Defaults to :py:data:`True`.
    :param list[int,int,int,int] zoom: Zoom extents to set programmatically for matplotlib plots. Must pass a list of four integers: :py:data:`[left, right, up, down]`. Since the z-axis begins at the top, the "up" value is actually the one that displays lower on the page. All four values are axis units, so if you are working in nanoseconds, 10 will set a limit 10 nanoseconds down. If your x-axis is in seconds, 6 will set a limit 6 seconds from the start of the survey. It may be helpful to display the matplotlib interactive window at full extents first, to determine appropriate extents to set for this parameter. If extents are set outside the boundaries of the image, they will be set back to the boundaries. If two extents on the same axis are the same, the program will default to plotting full extents for that axis.
    :rtype: header (:py:class:`dict`), radar array (:py:class:`numpy.ndarray`), gps (False or :py:class:`pandas.DataFrame`)
    :param bool pausecorrect: If :py:data:`True`, search the DZG file for pauses, where GPS keeps recording but radar unit does not, and correct them if necessary. Defaults to :py:data:`False`.
    :param bool showmarks: If :py:data:`True`, display mark locations in plot. Defaults to :py:data:`False`.
    """

    if infile:
        # read the file
        try:
            if verbose:
                fx.printmsg('reading...')
                fx.printmsg('input file:         %s' % (infile))
            header, data, gps = readdzt(infile, gps=normalize, spm=spm,
                                        start_scan=start_scan, num_scans=num_scans,
                                        epsr=epsr, antfreq=antfreq, zero=zero,
                                        verbose=verbose)
            # print a bunch of header info
            if verbose:
                fx.printmsg('success. header values:')
                header_info(header, data)
        except IOError as e: # the user has selected an inaccessible or nonexistent file
            fx.printmsg("ERROR: DZT file is inaccessable or does not exist at %s" % (os.path.abspath(infile)))
            raise IOError(e)
        infile_ext = os.path.splitext(infile)[1]
        infile_basename = os.path.splitext(infile)[0]
    else:
        raise IOError('ERROR: no input file specified')

    rhf_sps = header['rhf_sps']
    rhf_spm = header['rhf_spm']
    line_dur = header['sec']
    for chan in list(range(header['rh_nchan'])):
        try:
            ANT[header['rh_antname'][chan]]
        except KeyError as e:
            print('--------------------WARNING - PLEASE READ---------------------')
            fx.printmsg('WARNING: could not read frequency for antenna name "%s"' % e)
            if (antfreq != None) and (antfreq != [None, None, None, None]):
                fx.printmsg('using user-specified antenna frequency. Please ensure frequency value or list of values is correct.')
                fx.printmsg('old values: %s' % (header['antfreq']))
                fx.printmsg('new values: %s' % (antfreq))
                header['antfreq'] = antfreq
            else:
                fx.printmsg('WARNING: trying to use frequencies of %s MHz (estimated)...' % (header['antfreq'][chan]))
            fx.printmsg('more info: rh_ant=%s' % (header['rh_ant']))
            fx.printmsg('           known_ant=%s' % (header['known_ant']))
            fx.printmsg("please submit a bug report with this warning, the antenna name and frequency")
            fx.printmsg('at https://github.com/iannesbitt/readgssi/issues/new')
            fx.printmsg('or send via email to ian (dot) nesbitt (at) gmail (dot) com.')
            fx.printmsg('if possible, please attach a ZIP file with the offending DZT inside.')
            print('--------------------------------------------------------------')

    chans = list(range(header['rh_nchan']))

    if (pausecorrect) and (not gps.empty):
        fx.printmsg('correcting GPS errors created by user-initiated recording pauses...')
        gps = pause_correct(header=header, dzg_file=os.path.splitext(infile)[0] + ".DZG", verbose=verbose)
    elif (pausecorrect) and (gps.empty):
        fx.printmsg("can't correct pauses without a valid DZG file to look for. are you sure the DZG has the same name as the DZT file?")


    for ar in data:
        """
        filter and construct an output file or plot from the current channel's array
        """
        if verbose:
            fx.printmsg('beginning processing for channel %s (antenna %s)' % (ar, header['rh_antname'][ar]))
        # execute filtering functions if necessary
        if normalize:
            header, data[ar], gps = arrayops.distance_normalize(header=header, ar=data[ar], gps=gps,
                                                                  verbose=verbose)
        if dewow:
            # dewow
            data[ar] = filtering.dewow(ar=data[ar], verbose=verbose)
        if freqmin and freqmax:
            # vertical triangular bandpass
            data[ar] = filtering.triangular(ar=data[ar], header=header, freqmin=freqmin, freqmax=freqmax,
                                               zerophase=True, verbose=verbose)
        if stack != 1:
            # horizontal stacking
            header, data[ar], stack = arrayops.stack(ar=data[ar],
                                                      header=header,
                                                      stack=stack,
                                                      verbose=verbose)
        else:
            stack = 1 # just in case it's not an integer
        if bgr:
            # background removal
            data[ar] = filtering.bgr(ar=data[ar], header=header, win=win, verbose=verbose)
        else:
            win = None
        if reverse:
            # read array backwards
            data[ar] = arrayops.flip(data[ar], verbose=verbose)


        ## file naming
        # name the output file
        if ar == 0: # first channel?
            orig_outfile = outfile # preserve the original
        else:
            outfile = orig_outfile # recover the original

        if outfile:
            outfile_ext = os.path.splitext(outfile)[1]
            outfile = '%s' % (os.path.join(os.path.splitext(outfile)[0]))
            if len(chans) > 1:
                outfile = '%sc%s' % (outfile, ar) # avoid naming conflicts
        else:
            outfile = fx.naming(infile_basename=infile_basename, chans=chans, chan=ar, normalize=normalize,
                                zero=header['timezero'][ar], stack=stack, reverse=reverse, bgr=bgr, win=win,
                                dewow=dewow, freqmin=freqmin, freqmax=freqmax, plotting=plotting,
                                gain=gain, absval=absval)

        if plotting:
            plot.radargram(ar=data[ar], ant=ar, header=header, freq=header['antfreq'][ar], verbose=verbose,
                           figsize=figsize, dpi=dpi, stack=stack, x=x, z=z, gain=gain, colormap=colormap,
                           colorbar=colorbar, noshow=noshow, outfile=outfile, win=win, title=title,
                           zero=header['timezero'][ar], zoom=zoom, absval=absval, showmarks=showmarks)

        if histogram:
            plot.histogram(ar=data[ar], verbose=verbose)

        if specgram:
            plot.spectrogram(ar=data[ar], header=header, freq=header['antfreq'][ar], verbose=verbose)

    if frmt != None:
        if verbose:
            fx.printmsg('outputting to %s...' % frmt)
        for ar in data:
            # is there an output filepath given?
            outfile_abspath = os.path.abspath(outfile) # set output to given location

            # what is the output format
            if frmt in 'csv':
                translate.csv(ar=data[ar], outfile_abspath=outfile_abspath,
                              header=header, verbose=verbose)
            elif frmt in 'h5':
                translate.h5(ar=data[ar], infile_basename=infile_basename,
                             outfile_abspath=outfile_abspath, verbose=verbose)
            elif frmt in 'segy':
                translate.segy(ar=data[ar], outfile_abspath=outfile_abspath,
                               verbose=verbose)
            elif frmt in 'numpy':
                translate.numpy(ar=data[ar], outfile_abspath=outfile_abspath,
                                verbose=verbose)
            elif frmt in 'gprpy':
                translate.gprpy(ar=data[ar], outfile_abspath=outfile_abspath,
                                header=header, verbose=verbose)
            elif frmt in 'dzt':
                if ar == 0:
                    translate.dzt(ar=data, outfile_abspath=outfile_abspath,
                                  header=header, verbose=verbose)
        if frmt in ('object', 'python'):
            return header, data, gps
    
def main():
    """
    This function gathers and parses command line arguments with which to create function calls. It is not for use from the python console.
    """

    verbose = True
    title = True
    stack = 1
    win = 0
    dpi = 150
    zero = [None,None,None,None]
    zoom = [0,0,0,0]
    infile, outfile, antfreq, frmt, plotting, figsize, histogram, colorbar, dewow, bgr, noshow = None, None, None, None, None, None, None, None, None, None, None
    reverse, freqmin, freqmax, specgram, normalize, spm, epsr, absval, pausecorrect, showmarks = None, None, None, None, None, None, None, None, None, None
    colormap = 'gray'
    x, z = 'seconds', 'nanoseconds'
    gain = 1

# some of this needs to be tweaked to formulate a command call to one of the main body functions
# variables that can be passed to a body function: (infile, outfile, antfreq=None, frmt, plotting=False, stack=1)
    try:
        opts, args = getopt.getopt(sys.argv[1:],'hVqd:i:a:o:f:p:s:r:RNwnmc:bg:Z:E:t:x:z:Te:D:APM',
            ['help', 'version', 'quiet','spm=','input=','antfreq=','output=','format=','plot=','stack=','bgr=',
            'reverse', 'normalize','dewow','noshow','histogram','colormap=','colorbar','gain=',
            'zero=','epsr=','bandpass=', 'xscale=', 'zscale=', 'titleoff', 'zoom=', 'dpi=', 'absval','pausecorrect',
            'showmarks'])
    # the 'no option supplied' error
    except getopt.GetoptError as e:
        fx.printmsg('ERROR: invalid argument(s) supplied')
        fx.printmsg('error text: %s' % e)
        fx.printmsg(config.help_text)
        sys.exit(2)
    for opt, arg in opts: 
        if opt in ('-h', '--help'): # the help case
            fx.printmsg(config.help_text)
            sys.exit()
        if opt in ('-V', '--version'): # the help case
            print(config.version_text)
            sys.exit()
        if opt in ('-q', '--quiet'):
            verbose = False
        if opt in ('-i', '--input'): # the input file
            if arg:
                infile = arg
                if '~' in infile:
                    infile = os.path.expanduser(infile) # if using --input=~/... tilde needs to be expanded 
        if opt in ('-o', '--output'): # the output file
            if arg:
                outfile = arg
                if '~' in outfile:
                    outfile = os.path.expanduser(outfile) # expand tilde, see above
        if opt in ('-a', '--antfreq'):
            try:
                antfreq = [None, None, None, None]
                freq_arg = arg.split(',')
                for i in range(len(freq_arg)):
                    antfreq[i] = round(abs(float(freq_arg[i])))
            except ValueError:
                fx.printmsg('ERROR: %s is not a valid number or list of frequency values.' % arg)
                fx.printmsg(config.help_text)
                sys.exit(2)
            fx.printmsg('user specified frequency values of %s MHz will be overwritten if DZT header has valid antenna information.' % antfreq)

        if opt in ('-f', '--format'): # the format string
            # check whether the string is a supported format
            if arg:
                arg = arg.lower()
                if arg in ('.dzt', 'dzt', 'gssi', 'radan'):
                    frmt = 'dzt'
                elif arg in ('csv', '.csv'):
                    frmt = 'csv'
                elif arg in ('sgy', 'segy', 'seg-y', '.sgy', '.segy', '.seg-y'):
                    frmt = 'segy'
                elif arg in ('h5', 'hdf5', '.h5', '.hdf5'):
                    frmt = 'h5'
                elif arg in ('numpy', 'npy', '.npy', 'np'):
                    frmt = 'numpy'
                elif arg in ('gprpy'):
                    frmt = 'gprpy'
                elif arg in ('plot', 'png'):
                    plotting = True
                else:
                    # else the user has given an invalid format
                    fx.printmsg('Invalid file format given.')
                    fx.printmsg(config.help_text)
                    sys.exit(2)
            else:
                fx.printmsg('No file format specified.')
                fx.printmsg(config.help_text)
                sys.exit(2)
        if opt in ('-s', '--stack'):
            if arg:
                if 'auto' in str(arg).lower():
                    stack = 'auto'
                else:
                    try:
                        stack = abs(int(arg))
                    except ValueError:
                        fx.printmsg('ERROR: stacking argument must be a positive integer or "auto".')
                        fx.printmsg(config.help_text)
                        sys.exit(2)
        if opt in ('-r', '--bgr'):
            bgr = True
            if arg:
                try:
                    win = abs(int(arg))
                except:
                    fx.printmsg('ERROR: background removal window must be a positive integer. defaulting to full width.')
        if opt in ('-w', '--dewow'):
            dewow = True
        if opt in ('-R', '--reverse'):
            reverse = True
        if opt in ('-P', '--pausecorrect'):
            pausecorrect = True
        if opt in ('-N', '--normalize'):
            normalize = True
        if opt in ('-Z', '--zero'):
            if arg:
                try:
                    zero = list(map(int, arg.split(',')))
                except:
                    fx.printmsg('ERROR: zero correction must be an integer or list')
            else:
                fx.printmsg('WARNING: no zero correction argument supplied')
        if opt in ('-t', '--bandpass'):
            if arg:
                freqmin, freqmax = arg.split('-')
                try:
                    freqmin = int(freqmin)
                    freqmax = int(freqmax)
                except:
                    fx.printmsg('ERROR: filter frequency must be integers separated by a dash (-)')
                    freqmin, freqmax = None, None
            else:
                fx.printmsg('WARNING: no filter frequency argument supplied')
        if opt in ('-n', '--noshow'):
            noshow = True
        if opt in ('-p', '--plot'):
            plotting = True
            if arg:
                if 'auto' in arg.lower():
                    figsize = 8
                else:
                    try:
                        figsize = abs(int(arg))
                    except ValueError:
                        fx.printmsg('ERROR: plot size argument must be a positive integer or "auto".')
                        fx.printmsg(config.help_text)
                        sys.exit(2)
        if opt in ('-d', '--spm'):
            if arg:
                try:
                    spm = float(arg)
                    assert spm > 0
                except:
                    fx.printmsg('ERROR: samples per meter must be positive. defaulting to read from header')
                    spm = None
            else:
                fx.printmsg('WARNING: no samples per meter value given')
        if opt in ('-x', '--xscale'):
            if arg:
                if arg in ('temporal', 'time', 'seconds', 's'):
                    x = 'seconds'
                elif arg in ('spatial', 'distance', 'dist', 'length', 'meters', 'm'):
                    x = 'm'
                elif arg in ('centimeters', 'cm'):
                    x = 'cm'
                elif arg in ('kilometers', 'km'):
                    x = 'km'
                elif arg in ('traces', 'samples', 'pulses', 'columns'):
                    x = 'traces'
                else:
                    fx.printmsg('WARNING: invalid xscale type specified. defaulting to --xscale="seconds"')
                    x = 'seconds'
            else:
                fx.printmsg('WARNING: no xscale type specified. defaulting to --xscale="seconds"')
                x = 'seconds'
        if opt in ('-z', '--zscale'):
            if arg:
                if arg in ('temporal', 'time', 'nanoseconds', 'ns'):
                    z = 'nanoseconds'
                elif arg in ('spatial', 'distance', 'depth', 'length', 'meters', 'm'):
                    z = 'm'
                elif arg in ('centimeters', 'cm'):
                    z = 'cm'
                elif arg in ('millimeters', 'mm'):
                    z = 'mm'
                elif arg in ('samples', 'rows'):
                    z = 'samples'
                else:
                    fx.printmsg('WARNING: invalid zscale type specified. defaulting to --zscale="nanoseconds"')
                    z = 'nanoseconds'
            else:
                fx.printmsg('WARNING: no zscale type specified. defaulting to --zscale="nanoseconds"')
                z = 'nanoseconds'
        if opt in ('-E', '--epsr'):
            try:
                epsr = float(arg)
                if epsr <= 1:
                    raise Exception
            except:
                fx.printmsg('ERROR: invalid value for epsr (epsilon sub r "dielectric permittivity"). using DZT value instead.')
                epsr = None
        if opt in ('-m', '--histogram'):
            histogram = True
        if opt in ('-M', '--showmarks'):
            showmarks = True
        if opt in ('-c', '--colormap'):
            if arg:
                colormap = arg
        if opt in ('-b', '--colorbar'):
            colorbar = True
        if opt in ('-A', '--absval'):
            absval = True
        if opt in ('-g', '--gain'):
            if arg:
                try:
                    gain = abs(float(arg))
                except:
                    fx.printmsg('ERROR: gain must be positive. defaulting to gain=1.')
                    gain = 1
        if opt in ('-T', '--titleoff'):
            title = False
        if opt in ('-e', '--zoom'):
            if arg:
                if True:#try:
                    zoom = list(map(int, arg.split(',')))
                    if len(zoom) != 4:
                        fx.printmsg('ERROR: zoom must be a list of four numbers (zeros are accepted).')
                        fx.printmsg('       defaulting to full extents.')
                        zoom = [0,0,0,0]
                # except Exception as e:
                #     fx.printmsg('ERROR setting zoom values. zoom must be a list of four numbers (zeros are accepted).')
                #     fx.printmsg('       defaulting to full extents.')
                #     fx.printmsg('details: %s' % e)
        if opt in ('-D', '--dpi'):
            if arg:
                try:
                    dpi = abs(int(arg))
                    assert dpi > 0
                except:
                    fx.printmsg('WARNING: DPI could not be set. did you supply a positive integer?')

    # call the function with the values we just got
    if infile:
        if verbose:
            fx.printmsg(config.dist)
        readgssi(infile=infile, outfile=outfile, antfreq=antfreq, frmt=frmt, plotting=plotting, dpi=dpi,
                 figsize=figsize, stack=stack, verbose=verbose, histogram=histogram, x=x, z=z,
                 colormap=colormap, colorbar=colorbar, reverse=reverse, gain=gain, bgr=bgr, win=win,
                 zero=zero, normalize=normalize, dewow=dewow, noshow=noshow, freqmin=freqmin, freqmax=freqmax,
                 spm=spm, epsr=epsr, title=title, zoom=zoom, absval=absval, pausecorrect=pausecorrect,
                 showmarks=showmarks)
        if verbose:
            fx.printmsg('done with %s' % infile)
        print('')
    else:
        fx.printmsg('ERROR: no input file was specified')
        fx.printmsg(config.help_text)
        sys.exit(2)

if __name__ == "__main__":
    """
    directs the command line call to the main argument parsing function.
    """
    main()
