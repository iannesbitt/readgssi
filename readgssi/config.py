from datetime import datetime
from readgssi.__init__ import __version__, name
import pkg_resources

"""
This module contains some things readgssi needs to operate, both command line and python-related.
"""

dist = pkg_resources.get_distribution(name)
year = datetime.now().year
author = 'Ian Nesbitt'
affil = 'School of Earth and Climate Sciences, University of Maine'

help_text = u'''Help text:
############################################################
 readgssi version %s

 Copyleft %s %s 2017-%s
 %s
############################################################

usage:
readgssi -i input.DZT [OPTIONS]

required flags:
     OPTION     |      ARGUMENT       |       FUNCTIONALITY
-i, --input     | file:  /dir/f.DZT   |  input DZT file

optional flags:
     OPTION     |      ARGUMENT       |       FUNCTIONALITY
-o, --output    | file:  /dir/f.ext   |  output file. if not set, will be named similar to input
-f, --format    | string, eg. "csv"   |  output format (CSV and DZT are the only working formats currently available from the command line)
-p, --plot      | +integer or "auto"  |  plot size. will be x inches high or "auto". default: 10. see also -D to set DPI
-D, --dpi       | positive integer    |  set the plot DPI for figure making. defaults to 150
-T, --titleoff  |                     |  turn the plot title off (useful for figure making)
-x, --xscale    | string, eg. "dist"  |  x units. will attempt to convert the x-axis to distance, time, or trace units based on header values
-z, --zscale    | string, eg. "time"  |  z units. attempt to convert the x-axis to depth, time, or sample units based on header values
-e, --zoom      | list of +int [LRUD] |  set a zoom to automatically jump to. list order is [left,right,up,down] and units are the same as axis
-n, --noshow    |                     |  suppress matplotlib popup window and simply save a figure (useful for multi-file processing)
-c, --colormap  | string, eg. "Greys" |  specify the colormap (https://matplotlib.org/users/colormaps.html#grayscale-conversion)
-g, --gain      | positive float      |  gain constant (higher=greater contrast, default: 1)
-A, --absval    |                     |  Displays the absolute value of the vertical gradient of the array when plotting. Good for displaying faint array features.
-r, --bgr       | +integer or zero    |  horizontal background removal (useful to remove ringing). zero=full width; positive=window size (after stacking)
-R, --reverse   |                     |  reverse (flip array horizontally)
-w, --dewow     |                     |  trinomial dewow algorithm
-t, --bandpass  | +int-+int (MHz)     |  triangular FIR bandpass filter applied vertically (positive integer range in megahertz; ex. 70-130)
-b, --colorbar  |                     |  add a colorbar to the radar figure
-a, --antfreq   | positive integer    |  set antenna frequency. overrides header value
-s, --stack     | +integer or "auto"  |  set trace stacking value or "auto" to autostack to ~2.5:1 x:y axis ratio
-N, --normalize |                     |  distance normalize; reads .DZG NMEA data file if it exists; otherwise tries to read CSV with lat, lon, and time fields
-d, --spm       | positive float      |  specify the samples per meter (spm). overrides header value
-m, --histogram |                     |  produce a histogram of data values
-E, --epsr      | float > 1.0         |  user-defined epsilon sub r (sometimes referred to as "dielectric") if set, ignores value in DZT header
-Z, --zero      | +int or list of int |  timezero: skip samples before direct wave. samples are removed from the top of the trace. use list for multi-channel

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
''' % (__version__, u'\U0001F12F', author, year, affil)

version_text = '%s %s' % (name, __version__)