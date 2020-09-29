import math
from datetime import datetime
from readgssi.constants import *
import os

def printmsg(msg):
    """
    Prints with date/timestamp.

    :param str msg: Message to print
    """
    print('%s - %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))

def genericerror(filetype='file'):
    """Prints a standard message for a generic error using the `gpx2dzg.functions.printmsg()` function.
    This is called from functions in `gpx2dzg.io`.

    Parameters
    ----------
    filetype : str
        The type of file this message is about. Used to format error string.
    """
    printmsg('please attach this %s to a new github issue (https://github.com/iannesbitt/readgssi/issues/new)' % filetype)
    printmsg('        or send it to ian.nesbitt@gmail.com in order to have the format assessed. please also')
    printmsg('        include the output of the program (i.e. copy and paste this text and the text above in')
    printmsg('        the message) as this will drastically speed up my ability to help you! thanks!')
    printmsg('  ~!~>  I am happy to help but please note that I am not responsible for the content of your')
    printmsg('  ~!~>  files, only the working-ness of this software. I appreciate your understanding!')

def dzxerror(e=''):
    """Prints an error message then calls `gpx2dzg.functions.genericerror()` and passes `filetype='DZX'`.

    Parameters
    ----------
    e : str
        The error message to print.
    """
    printmsg('ERROR TEXT: %s' % e)
    genericerror('DZX')

def dzterror(e=''):
    """Prints an error message then calls `gpx2dzg.functions.genericerror()` and passes `filetype='DZT'`.

    Parameters
    ----------
    e : str
        The error message to print.
    """
    printmsg('ERROR TEXT: %s' % e)
    genericerror('DZT')

def naming(outfile=None, infile_basename=None, chans=[1], chan=0, normalize=False, zero=None, stack=1, reverse=False,
           bgr=False, win=None, gain=None, dewow=None, freqmin=None, freqmax=None, plotting=None, zoom=None,
           absval=False):
    """
    The Dr. Seth W. Campbell Honorary Naming Scheme

    Descriptive naming, used to indicate the processing steps done on each file, if a specific output filename is not given. The theory behind this naming scheme is simple: it can be tough to remember how you made that plot!

    Named for my graduate advisor, whom I love and cherish, who introduced me to this way of naming outputs.

    .. code-block:: None

        naming scheme for exports:
          CHARACTERS    |      MEANING
            Ch0         |  Profile from channel 0 (can range from 0 - 3)
            Dn          |  Distance normalization
            Tz233       |  Time zero at 233 samples
            S8          |  Stacked 8 times
            Rv          |  Profile read in reverse (flipped horizontally)
            Bgr75       |  Background removal filter with window size of 75
            Dw          |  Dewow filter
            Bp70-130    |  triangular FIR filter applied from 70 to 130 MHz
            G30         |  30x contrast gain
            Abs         |  Color scale represents absolute value of vertical gradient
            Z10.20.7.5  |  zoom from 10-20 axis units on the x-axis and 5-7 on the z-axis

    :param str outfile: The base output filename. If None, a new :code:`outfile` will be generated from the input file basename. If it already exists, subsequent arguments will be appended. Defaults to None.
    :param str infile_basename: The input file basename (without file extension). Defaults to None.
    :param list[int,int,int,int] chans: A list of channels, which is converted to the number of channels using :py:func:`len`. Defaults to [1].
    :param int chan: The current channel number. Defaults to 0.
    :param bool normalize: Whether or not the array is distance-normalized. Defaults to False.
    :param int zero: The zero point for this particular channel. Defaults to None.
    :param int stack: The number of times the array was stacked. Defaults to 1.
    :param bool reverse: Whether or not the file was reversed. Defaults to False.
    :param bool bgr: Whether or not BGR was applied. Defaults to False.
    :param int win: The BGR window size if applicable. 0 is full-width BGR, greater than 0 is window size. Defaults to None.
    :param float gain: The gain value applied to the plot. Defaults to None.
    :param bool dewow: Whether or not dewow was applied. Defaults to None.
    :param int freqmin: The lower corner of the bandpass filter if applicable. Defaults to None.
    :param int freqmax: The upper corner of the bandpass filter if applicable. Defaults to None.
    :param int plotting: Stand-in for whether or not a plot was generated. The integer represents the plot height. Defaults to None.
    :param list[int,int,int,int] zoom: The zoom extents applied to the image. Defaults to None.
    :param bool absval: Whether or not the plot is displayed with absolute value of gradient. Defaults to False.
    """
    if outfile == None:
        outfile = '%s' % (os.path.join(infile_basename))

    if len(chans) > 1:
        outfile = '%sCh%s' % (outfile, chan)
    if zero and (zero > 0):
        outfile = '%sTz%s' % (outfile, zero)
    if normalize:
        outfile = '%sDn' % (outfile)
    if freqmin and freqmax:
        outfile = '%sB%s-%s' % (outfile, freqmin, freqmax)
    if dewow:
        outfile = '%sDw' % (outfile)
    if stack > 1:
        outfile = '%sS%s' % (outfile, stack)
    if bgr:
        outfile = '%sBgr%s' % (outfile, win)
    if reverse:
        outfile = '%sRv' % (outfile)
    if plotting:
        outfile = '%sG%s' % (outfile, int(gain))
    if absval:
        outfile = '%sAbs' % (outfile)
    if zoom:
        outfile = '%sZ' % (outfile)
        for ex in zoom:
            outfile = '%s.%s' % (outfile, ex)


    return outfile


def zoom(zoom, extent, x, z, verbose=False):
    """
    Logic to figure out how to set zoom extents. If specified limits are out of bounds, they are set back to boundary extents. If limits of a specified axis are equal, they are expanded to the full extent of that axis.

    :param list[int,int,int,int] zoom: Zoom extents to set programmatically for matplotlib plots. Must pass a list of four integers: :py:data:`[left, right, up, down]`. Since the z-axis begins at the top, the "up" value is actually the one that displays lower on the page. All four values are axis units, so if you are working in nanoseconds, 10 will set a limit 10 nanoseconds down. If your x-axis is in seconds, 6 will set a limit 6 seconds from the start of the survey. It may be helpful to display the matplotlib interactive window at full extents first, to determine appropriate extents to set for this parameter. If extents are set outside the boundaries of the image, they will be set back to the boundaries. If two extents on the same axis are the same, the program will default to plotting full extents for that axis.
    :param list[int,int,int,int] extent: Full extent boundaries of the image, in the style :py:data:`[left, right, up, down]`.
    :param str x: X axis units
    :param str z: Z axis units
    :param bool verbose: Verbose, defaults to False
    """

    for i in range(4):
        if zoom[i] < 0:
            zoom[i] = 0
            if verbose:
                printmsg('WARNING: %s zoom limit was negative, now set to zero' % ['left','right','up','down'][i])
    if (zoom[0] > 0) or (zoom[1] > 0): # if a LR value has been set
        if zoom[0] > extent[1]: # if L zoom is beyond extents, set back to extent limit
            zoom[0] = extent[1]
            if verbose:
                printmsg('WARNING: left zoom limit out of bounds (limit is %s %s)' % (extent[1], x))
        if zoom[1] > extent[1]: # if R zoom is beyond extents, set back to extent limit
            zoom[1] = extent[1]
            if verbose:
                printmsg('WARNING: right zoom limit out of bounds (limit is %s %s)' % (extent[1], x))
        if zoom[0] == zoom[1]: # if LR extents are impossible,
            zoom[0] = extent[0] # set both to full extents
            zoom[1] = extent[1]
            if verbose:
                printmsg('WARNING: left and right zoom values were equal or both out of bounds, now set to full extent')
    else:
        zoom[0] = extent[0]
        zoom[1] = extent[1]
    if (zoom[2] > 0) or (zoom[3] > 0): # if a UD value has been set
        if zoom[2] > extent[2]: # if upper zoom is beyond extents, set back to extent limit
            zoom[2] = extent[2]
            if verbose:
                printmsg('WARNING: upper zoom limit out of bounds (limit is %s %s)' % (extent[3], z))
        if zoom[3] > extent[2]: # if lower zoom is beyond extents, set back to extent limit
            zoom[3] = extent[2]
            if verbose:
                printmsg('WARNING: lower zoom limit out of bounds (limit is %s %s)' % (extent[3], z))
        if zoom[2] == zoom[3]: # if UD extents are impossible,
            zoom[2] = extent[2] # set both to full extents
            zoom[3] = extent[3]
            if verbose:
                printmsg('WARNING: top and bottom zoom values were equal or both out of bounds, now set to full extent')
    else:
        zoom[2] = extent[2]
        zoom[3] = extent[3]
    return zoom