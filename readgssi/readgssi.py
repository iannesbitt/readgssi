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


def readgssi(infile, outfile=None, antfreq=None, frmt=None, plotting=False, figsize=10,
             stack=1, verbose=False, histogram=False, colormap='Greys', colorbar=False,
             zero=0, gain=1, freqmin=None, freqmax=None, reverse=False, bgr=False, dewow=False,
             normalize=False, specgram=False, noshow=False):
    '''
    primary radar processing function

    includes calls to reading, filtering, translation, and plotting functions
    '''

    if infile:
        # read the file
        try:
            if verbose:
                fx.printmsg('reading...')
                fx.printmsg('input file:         %s' % (infile))
            r = readdzt(infile, gps=normalize, verbose=verbose)
            if verbose:
                fx.printmsg('success. header values:')
                header_info(r[0], r[1])
        except IOError as e: # the user has selected an inaccessible or nonexistent file
            fx.printmsg("ERROR: DZT file is inaccessable or does not exist at %s" % (os.path.abspath(infile)))
            raise IOError(e)
        infile_ext = os.path.splitext(infile)[1]
        infile_basename = os.path.splitext(infile)[0]
    else:
        raise IOError('ERROR: no input file specified')

    rhf_sps = r[0]['rhf_sps']
    rhf_spm = r[0]['rhf_spm']
    line_dur = r[0]['sec']
    for chan in list(range(r[0]['rh_nchan'])):
        try:
            ANT[r[0]['rh_antname'][chan]]
        except KeyError as e:
            print('--------------------WARNING - PLEASE READ---------------------')
            fx.printmsg('WARNING: could not read frequency for antenna name %s' % e)
            if antfreq:
                fx.printmsg('using user-specified antenna frequency.')
                r[0]['antfreq'] = antfreq
            else:
                fx.printmsg('WARNING: trying to use frequency of %s MHz (estimated)...' % (r[0]['antfreq'][chan]))
            fx.printmsg('more info: rh_ant=%s' % (r[0]['rh_ant']))
            fx.printmsg('           known_ant=%s' % (r[0]['known_ant']))
            fx.printmsg("please submit a bug report with this warning, the antenna name and frequency")
            fx.printmsg('at https://github.com/iannesbitt/readgssi/issues/new')
            fx.printmsg('or send via email to ian (dot) nesbitt (at) gmail (dot) com.')
            fx.printmsg('if possible, please attach a ZIP file with the offending DZT inside.')
            print('--------------------------------------------------------------')


    # create a list of n arrays, where n is the number of channels
    arr = r[1].astype(np.int32)
    chans = list(range(r[0]['rh_nchan']))
    timezero = 0
    #timezero = abs(round(float(r[0]['rh_nsamp'])/float(r[0]['rhf_range'])*float(r[0]['rhf_position'])))
    img_arr = arr[timezero:r[0]['rh_nchan']*r[0]['rh_nsamp']]
    new_arr = {}
    for ar in chans:
        a = []
        a = img_arr[(ar)*r[0]['rh_nsamp']:(ar+1)*r[0]['rh_nsamp']]
        new_arr[ar] = a[zero:,:int(img_arr.shape[1])]
            
    img_arr = new_arr
    del arr, new_arr

    for ar in img_arr:
        '''
        filter and construct an output file or plot from the current channel's array
        '''
        if verbose:
            fx.printmsg('beginning processing for channel %s (antenna %s)' % (ar, r[0]['rh_antname'][ar]))
        # execute filtering functions if necessary
        if normalize:
            r[0], img_arr[ar], r[2] = arrayops.distance_normalize(header=r[0], ar=img_arr[ar], gps=r[2],
                                                                  verbose=verbose)
        if stack != 1:
            # horizontal stacking
            img_arr[ar], stack = arrayops.stack(ar=img_arr[ar], stack=stack, verbose=verbose)
        else:
            stack = 1
        if reverse:
            img_arr[ar] = arrayops.flip(img_arr[ar], verbose=verbose)
        if bgr:
            # background removal
            img_arr[ar] = filtering.bgr(ar=img_arr[ar], verbose=verbose)
        if dewow:
            # dewow
            img_arr[ar] = filtering.dewow(ar=img_arr[ar], verbose=verbose)
        if freqmin and freqmax:
            # vertical bandpass
            img_arr[ar] = filtering.bp(ar=img_arr[ar], header=r[0], freqmin=freqmin, freqmax=freqmax,
                                       verbose=verbose)

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
            '''
            ~~~ The Seth Campbell Honorary Naming Scheme ~~~
            '''
            outfile = '%sc%s' % (os.path.join(infile_basename), ar)
            if normalize:
                outfile = '%sDn' % (outfile)
            if zero and (zero > 0):
                outfile = '%sTz%s' % (outfile, zero)
            if stack > 1:
                outfile = '%sS%s' % (outfile, stack)
            if reverse:
                outfile = '%sRv' % (outfile)
            if bgr:
                outfile = '%sBgr' % (outfile)
            if dewow:
                outfile = '%sDw' % (outfile)
            if freqmin and freqmax:
                outfile = '%sB%s-%s' % (outfile, freqmin, freqmax)
            if plotting:
                outfile = '%sG%s' % (outfile, int(gain))

        if frmt != None:
            if verbose:
                fx.printmsg('outputting to %s...' % frmt)
            for ar in img_arr:
                # is there an output filepath given?
                outfile_abspath = os.path.abspath(outfile) # set output to given location

                # what is the output format
                if frmt in 'csv':
                    translate.csv(ar=img_arr[ar], outfile_abspath=outfile_abspath,
                                  header=r[0], verbose=verbose)
                elif frmt in 'h5':
                    translate.h5(ar=img_arr[ar], infile_basename=infile_basename,
                                 outfile_abspath=outfile_abspath, verbose=verbose)
                elif frmt in 'segy':
                    translate.segy(ar=img_arr[ar], outfile_abspath=outfile_abspath,
                                   verbose=verbose)
                elif frmt in 'numpy':
                    translate.numpy(ar=img_arr[ar], outfile_abspath=outfile_abspath,
                                    verbose=verbose)
                elif frmt in 'gprpy':
                    translate.gprpy(ar=img_arr[ar], outfile_abspath=outfile_abspath,
                                    header=r[0], verbose=verbose)

        if plotting:
            plot.radargram(ar=img_arr[ar], header=r[0], freq=r[0]['antfreq'][ar], verbose=verbose, figsize=figsize, stack=stack,
                           gain=gain, colormap=colormap, colorbar=colorbar, noshow=noshow, outfile=outfile)

        if histogram:
            plot.histogram(ar=img_arr[ar], verbose=verbose)

        if specgram:
            plot.spectrogram(ar=img_arr[ar], header=header, freq=r[0]['antfreq'][ar], verbose=verbose)

    
def main():
    '''
    gathers and parses arguments to create function calls
    '''

    verbose = True
    stack = 1
    infile, outfile, antfreq, frmt, plotting, figsize, histogram, colorbar, dewow, bgr, noshow = None, None, None, None, None, None, None, None, None, None, None
    reverse, freqmin, freqmax, specgram, zero, normalize = None, None, None, None, None, None
    colormap = 'Greys'
    gain = 1

# some of this needs to be tweaked to formulate a command call to one of the main body functions
# variables that can be passed to a body function: (infile, outfile, antfreq=None, frmt, plotting=False, stack=1)
    try:
        opts, args = getopt.getopt(sys.argv[1:],'hqdi:a:o:f:p:s:rRNwnmc:bg:z:t:',
            ['help','quiet','dmi','input=','antfreq=','output=','format=','plot=','stack=','bgr',
            'reverse', 'normalize','dewow','noshow','histogram','colormap=','colorbar','gain=',
            'zero=','bandpass='])
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
        if opt in ('-a', '--freq'):
            try:
                antfreq = round(float(abs(arg)),1)
                fx.printmsg('user specified frequency value of %s MHz will be overwritten if DZT header has valid antenna information.' % antfreq)
            except:
                fx.printmsg('ERROR: %s is not a valid decimal or integer frequency value.' % arg)
                fx.printmsg(config.help_text)
                sys.exit(2)
        if opt in ('-f', '--format'): # the format string
            # check whether the string is a supported format
            if arg:
                arg = arg.lower()
                if arg in ('csv', '.csv'):
                    frmt = 'csv'
                elif arg in ('sgy', 'segy', 'seg-y', '.sgy', '.segy', '.seg-y'):
                    frmt = 'segy'
                elif arg in ('h5', 'hdf5', '.h5', '.hdf5'):
                    frmt = 'h5'
                elif arg in ('numpy', 'npy', '.npy'):
                    frmt = 'numpy'
                elif arg in ('gprpy'):
                    frmt = 'gprpy'
                elif arg in ('plot'):
                    plotting = True
                else:
                    # else the user has given an invalid format
                    fx.printmsg(config.help_text)
                    sys.exit(2)
            else:
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
        if opt in ('-w', '--dewow'):
            dewow = True
        if opt in ('-R', '--reverse'):
            reverse = True
        if opt in ('-N', '--normalize'):
            normalize = True
        if opt in ('-z', '--zero'):
            if arg:
                try:
                    zero = int(arg)
                except:
                    fx.printmsg('ERROR: zero correction must be an integer')
            else:
                fx.printmsg('WARNING: no zero correction argument supplied')
                zero = None
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
        if opt in ('-d', '--dmi'):
            #dmi = True
            fx.printmsg('ERROR: DMI devices are not supported at the moment.')
            pass # not doing anything with this at the moment
        if opt in ('-m', '--histogram'):
            histogram = True
        if opt in ('-c', '--colormap'):
            if arg:
                colormap = arg
        if opt in ('-b', '--colorbar'):
            colorbar = True
        if opt in ('-g', '--gain'):
            if arg:
                try:
                    gain = abs(float(arg))
                except:
                    fx.printmsg('ERROR: gain must be positive. defaulting to gain=1.')
                    gain = 1


    # call the function with the values we just got
    if infile:
        if verbose:
            fx.printmsg(config.dist)
        readgssi(infile=infile, outfile=outfile, antfreq=antfreq, frmt=frmt, plotting=plotting,
                 figsize=figsize, stack=stack, verbose=verbose, histogram=histogram,
                 colormap=colormap, colorbar=colorbar, reverse=reverse, gain=gain, bgr=bgr, zero=zero,
                 normalize=normalize, dewow=dewow, noshow=noshow, freqmin=freqmin, freqmax=freqmax)
        if verbose:
            fx.printmsg('done with %s' % infile)
        print('')
    else:
        fx.printmsg('ERROR: no input file was specified')
        fx.printmsg(config.help_text)
        sys.exit(2)

if __name__ == "__main__":
    '''
    directs the command line call to the main argument parsing function.
    '''
    main()
