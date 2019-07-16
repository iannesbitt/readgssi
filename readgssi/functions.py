import math
from datetime import datetime
from readgssi.constants import *
import os

def printmsg(msg):
    """
    Prints with date/timestamp.
    """
    print('%s - %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))

def naming(outfile=None, infile_basename=None, chans=[1], chan=0, normalize=None, zero=None, stack=1, reverse=None,
           bgr=None, win=None, gain=None, dewow=None, freqmin=None, freqmax=None, plotting=None, zoom=None):
    """
    The Dr. Seth W. Campbell Honorary Naming Scheme

    Descriptive naming, used to indicate the processing steps done on each file. It can be tough to remember how you made that plot!

    Named for my graduate advisor, whom I love and cherish, who introduced me to this way of naming outputs.
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
    if zoom:
        outfile = '%sZ' % (outfile)
        for ex in zoom:
            outfile = '%s.%s' % (outfile, ex)


    return outfile


def zoom(zoom, extent, x, z):
    """
    Logic to figure out how to set zoom extents.
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