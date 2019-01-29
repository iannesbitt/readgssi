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
import struct
import numpy as np
import math
from decimal import Decimal
from datetime import datetime, timedelta
import pytz
import readgssi.functions as fx
import readgssi.plot as plot
from readgssi import translate
from readgssi import filtering
from readgssi import config
from readgssi.constants import *


def readtime(bytes):
    '''
    function to read dates
    have i mentioned yet that this is a colossally stupid way of storing dates
    
    date values will come in as a 32 bit binary string (01001010111110011010011100101111)
    or (seconds/2, min, hr, day, month, year-1980)
    structured as little endian u5u6u5u5u4u7
    '''
    dtbits = ''
    byte = (b for b in bytes)
    for bit in byte:                    # assemble the binary string
        for i in range(8):
            dtbits += str((bit >> i) & 1)
    dtbits = dtbits[::-1]               # flip the string
    sec2 = int(dtbits[27:32], 2) * 2
    mins = int(dtbits[21:27], 2)
    hr = int(dtbits[16:21], 2)
    day = int(dtbits[11:16], 2)
    mo = int(dtbits[7:11], 2)
    yr = int(dtbits[0:7], 2) + 1980
    return datetime(yr, mo, day, hr, mins, sec2, 0, tzinfo=pytz.UTC)


def readdzt(infile):
    '''
    function to unpack and return things we need from the header, and the data itself
    currently unused but potentially useful lines:
    # headerstruct = '<5h 5f h 4s 4s 7h 3I d I 3c x 3h d 2x 2c s s 14s s s 12s h 816s 76s' # the structure of the bytewise header and "gps data" as I understand it - 1024 bytes
    # readsize = (2,2,2,2,2,4,4,4,4,4,2,4,4,4,2,2,2,2,2,4,4,4,8,4,3,1,2,2,2,8,1,1,14,1,1,12,2) # the variable size of bytes in the header (most of the time) - 128 bytes
    # fx.printmsg('total header structure size: '+str(calcsize(headerstruct)))
    # packed_size = 0
    # for i in range(len(readsize)): packed_size = packed_size+readsize[i]
    # fx.printmsg('fixed header size: '+str(packed_size)+'\n')
    '''
    rh_antname = ''

    rh_tag = struct.unpack('<h', infile.read(2))[0] # 0x00ff if header, 0xfnff if old file format
    rh_data = struct.unpack('<h', infile.read(2))[0] # offset to data from beginning of file
    rh_nsamp = struct.unpack('<h', infile.read(2))[0] # samples per scan
    rh_bits = struct.unpack('<h', infile.read(2))[0] # bits per data word
    rh_zero = struct.unpack('<h', infile.read(2))[0] # if sir-30 or utilityscan df, then repeats per sample; otherwise 0x80 for 8bit and 0x8000 for 16bit
    rhf_sps = struct.unpack('<f', infile.read(4))[0] # scans per second
    rhf_spm = struct.unpack('<f', infile.read(4))[0] # scans per meter
    rhf_mpm = struct.unpack('<f', infile.read(4))[0] # meters per mark
    rhf_position = struct.unpack('<f', infile.read(4))[0] # position (ns)
    rhf_range = struct.unpack('<f', infile.read(4))[0] # range (ns)
    rh_npass = struct.unpack('<h', infile.read(2))[0] # number of passes for 2-D files
    # bytes 32-36 and 36-40: creation and modification date and time in bits, structured as little endian u5u6u5u5u4u7
    infile.seek(32)
    try:
        rhb_cdt = readtime(infile.read(4))
    except:
        rhb_cdt = datetime(1980, 1, 1)
    try:
        rhb_mdt = readtime(infile.read(4))
    except:
        rhb_mdt = datetime(1980, 1, 1)
    rh_rgain = struct.unpack('<h', infile.read(2))[0] # offset to range gain function
    rh_nrgain = struct.unpack('<h', infile.read(2))[0] # size of range gain function
    rh_text = struct.unpack('<h', infile.read(2))[0] # offset to text
    rh_ntext = struct.unpack('<h', infile.read(2))[0] # size of text
    rh_proc = struct.unpack('<h', infile.read(2))[0] # offset to processing history
    rh_nproc = struct.unpack('<h', infile.read(2))[0] # size of processing history
    rh_nchan = struct.unpack('<h', infile.read(2))[0] # number of channels
    rhf_epsr = struct.unpack('<f', infile.read(4))[0] # average dilectric
    rhf_top = struct.unpack('<f', infile.read(4))[0] # position in meters (useless?)
    rhf_depth = struct.unpack('<f', infile.read(4))[0] # range in meters
    #rhf_coordx = struct.unpack('<ff', infile.read(8))[0] # this is definitely useless
    infile.seek(98) # start of antenna bit
    rh_ant = infile.read(14).decode('utf-8').split('\x00')[0]
    rh_antname = rh_ant.rsplit('x')[0]
    infile.seek(113) # skip to something that matters
    vsbyte = infile.read(1) # byte containing versioning bits
    rh_version = ord(vsbyte) >> 5 # whether or not the system is GPS-capable, 1=no 2=yes (does not mean GPS is in file)
    rh_system = ord(vsbyte) >> 3 # the system type (values in UNIT={...} dictionary above)

    infile.seek(rh_rgain)
    try:
        rgain_bytes = infile.read(rh_nrgain)
    except:
        pass

    if rh_data < MINHEADSIZE: # whether or not the header is normal or big-->determines offset to data array
        infile.seek(MINHEADSIZE * rh_data)
    else:
        infile.seek(MINHEADSIZE * rh_nchan)

    if rh_bits == 8:
        data = np.fromfile(infile, np.uint8).reshape(-1,(rh_nsamp*rh_nchan)).T # 8-bit
    elif rh_bits == 16:
        data = np.fromfile(infile, np.uint16).reshape(-1,(rh_nsamp*rh_nchan)).T # 16-bit
    else:
        data = np.fromfile(infile, np.int32).reshape(-1,(rh_nsamp*rh_nchan)).T # 32-bit

    cr = 1 / math.sqrt(Mu_0 * Eps_0 * rhf_epsr)

    sec = data.shape[1]/float(rhf_sps)

    # create dictionary
    header = {
        # commonly used vars
        'rh_antname': rh_antname,
        'rh_system': rh_system,
        'rh_version': rh_version,
        'rh_nchan': rh_nchan,
        'rh_nsamp': rh_nsamp,
        'rhf_range': rhf_range,
        'rh_bits': rh_bits,
        'rhf_sps': rhf_sps,
        'rhf_spm': rhf_spm,
        'rhf_epsr': rhf_epsr,
        'cr': cr,
        'rhb_cdt': rhb_cdt,
        'rhb_mdt': rhb_mdt,
        'rhf_depth': rhf_depth,
        'rhf_position': rhf_position,
        'sec': sec,
        # less frequently used vars
        'rh_tag': rh_tag,
        'rh_data': rh_data,
        'rh_zero': rh_zero,
        'rhf_mpm': rhf_mpm,
        'rh_data': rh_data,
        'rh_npass': rh_npass,
        'rhb_cdt': rhb_cdt,
        'rh_ntext': rh_ntext,
        'rh_proc': rh_proc,
        'rh_nproc': rh_nproc,
        'rhf_top': rhf_top,
        'rh_proc': rh_proc,
        'rh_ant': rh_ant,
        'rh_rgain': rh_rgain,
        'rh_nrgain': rh_nrgain,
        # passed vars
        'infile': infile.name,
    }

    return [header, data]


def header_info(header, data):
    '''
    function to print relevant header data
    '''
    fx.printmsg('system:             %s' % UNIT[header['rh_system']])
    fx.printmsg('antenna:            %s' % header['rh_antname'])
    if header['rh_nchan'] > 1:
        i = 1
        for ar in ANT[header['rh_antname']]:
            fx.printmsg('ant %s frequency:   %s MHz' % (ar))
    else:
        fx.printmsg('antenna frequency:  %s MHz' % ANT[header['rh_antname']])
    fx.printmsg('date created:       %s' % header['rhb_cdt'])
    if header['rhb_mdt'] == datetime(1980, 1, 1):
        fx.printmsg('date modified:      (never modified)')
    else:
        fx.printmsg('date modified:      %s' % header['rhb_mdt'])
    try:
        fx.printmsg('gps-enabled file:   %s' % GPS[header['rh_version']])
    except (TypeError, KeyError) as e:
        fx.printmsg('gps-enabled file:   %s' % 'unknown')
    fx.printmsg('number of channels: %i' % header['rh_nchan'])
    fx.printmsg('samples per trace:  %i' % header['rh_nsamp'])
    fx.printmsg('bits per sample:    %s' % BPS[header['rh_bits']])
    fx.printmsg('traces per second:  %.1f' % header['rhf_sps'])
    fx.printmsg('traces per meter:   %.1f' % header['rhf_spm'])
    fx.printmsg('dilectric:          %.1f' % header['rhf_epsr'])
    fx.printmsg('speed of light:     %.2E m/sec (%.2f%% of vacuum)' % (header['cr'], header['cr'] / C * 100))
    fx.printmsg('sampling depth:     %.1f m' % header['rhf_depth'])
    if data.shape[1] == int(data.shape[1]):
        fx.printmsg('traces:             %i' % int(data.shape[1]/header['rh_nchan']))
    else:
        fx.printmsg('traces:             %f' % int(data.shape[1]/header['rh_nchan']))
    fx.printmsg('seconds:            %.8f' % (header['sec']))
    fx.printmsg('samp/m:             %.2f (zero unless DMI present)' % (float(header['rhf_spm']))) # I think...
    fx.printmsg('array dimensions:   %i x %i' % (data.shape[0], data.shape[1]))



def readgssi(infile, outfile=None, antfreq=None, frmt=None, plotting=False, figsize=10,
             stack=1, verbose=False, histogram=False, colormap='Greys', colorbar=False,
             zero=1, gain=1, freqmin=None, freqmax=None, bgr=False, dewow=False,
             specgram=False, noshow=False):
    '''
    primary radar processing function

    includes calls to reading, filtering, translation, and plotting functions
    '''

    if infile:
        # read the file
        try:
            with open(infile, 'rb') as f:
                # open the binary, attempt reading chunks
                if verbose:
                    fx.printmsg('reading...')
                    fx.printmsg('input file:         %s' % (infile))
                r = readdzt(f)
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
        if r[0]['rh_antname']:
            try:
                freq = ANT[r[0]['rh_antname']]
            except ValueError as e:
                fx.printmsg('WARNING: could not read frequency for given antenna name.\nerror info: %s' % e)
                if antfreq:
                    fx.printmsg('using user-specified antenna frequency.')
                    freq = antfreq
                else:
                    fx.printmsg('ERROR: no frequency information could be read from the header.')
                    raise AttributeError('no valid frequency information is available in the header. please specify the frequency of the antenna in MHz using the -a flag.')
            finally:
                if e:
                    fx.printmsg('error details: %s' % (e))
                    fx.printmsg('more info: rh_ant=%s, rh_antname=%s' % (r[0]['rh_ant'], r[0]['rh_antname']))
                    fx.printmsg("please submit a bug report with this error, the antenna name and frequency you're using, and if possible the offending DZT file at https://github.com/iannesbitt/readgssi/issues/new")
                    fx.pringmst('or send via email to ian (dot) nesbitt (at) gmail (dot) com.')

    # create a list of n arrays, where n is the number of channels
    arr = r[1].astype(np.int32)
    chans = list(range(r[0]['rh_nchan']))
    timezero = 1
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

        # execute filtering functions if necessary
        if stack > 1:
            # horizontal stacking
            img_arr[ar], stack = filtering.stack(ar=img_arr[ar], stack=stack, verbose=verbose)
        else:
            stack = 1
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
        if outfile and (len(chans) > 1):
            outfile_ext = os.path.splitext(outfile)[1]
            outfile_basename = '%sMHz' % (os.path.join(os.path.splitext(outfile)[0] + '_' + str(ANT[r[0]['rh_antname']][ar])))
            plot_outfile = outfile_basename
        elif outfile and (len(chans) == 1):
            outfile_ext = os.path.splitext(outfile)[1]
            outfile_basename = '%s' % (os.path.join(os.path.splitext(outfile)[0]))
            plot_outfile = outfile_basename
        else:
            '''
            ~~~ The Seth Campbell Honorary Naming Scheme ~~~
            '''
            outfile = '%sMHz' % (os.path.join(infile_basename + '_' + str(ANT[r[0]['rh_antname']][ar])))
            if zero and (zero > 1):
                outfile = '%sTZ' % (outfile)
            if stack > 1:
                outfile = '%sS%s' % (outfile, stack)
            if bgr:
                outfile = '%sBGR' % (outfile)
            if dewow:
                outfile = '%sDW' % (outfile)
            if freqmin and freqmax:
                outfile = '%sBP%s-%s' % (outfile, freqmin, freqmax)
            if plotting:
                plot_outfile = '%sG%s' % (outfile, int(gain))

        if frmt != None:
            if verbose:
                fx.printmsg('outputting to %s . . .' % frmt)
            for ar in img_arr:
                # is there an output filepath given?
                outfile_abspath = os.path.abspath(outfile_basename) # set output to given location

                # what is the output format
                if frmt in 'csv':
                    translate.csv(ar=img_arr[ar], outfile_abspath=outfile_abspath, verbose=verbose)

                elif frmt in 'h5':
                    translate.h5(ar=img_arr[ar], infile_basename=infile_basename,
                              outfile_abspath=outfile_abspath, verbose=verbose)

                elif frmt in 'segy':
                    translate.segy(ar=img_arr[ar], outfile_abspath=outfile_abspath, verbose=verbose)

        if plotting:
            plot.radargram(ar=img_arr[ar], header=r[0], freq=ANT[r[0]['rh_antname']][ar], verbose=verbose, figsize=figsize, stack=stack,
                           gain=gain, colormap=colormap, colorbar=colorbar, noshow=noshow, outfile=plot_outfile)

        if histogram:
            plot.histogram(ar=img_arr[ar], verbose=verbose)

        if specgram:
            plot.spectrogram(ar=img_arr[ar], header=header, freq=ANT[r[0]['rh_antname']][ar], verbose=verbose)

    
def main():
    '''
    gathers and parses arguments to create function calls
    '''

    verbose = True
    stack = 1
    infile, outfile, antfreq, frmt, plotting, figsize, histogram, colorbar, dewow, bgr, noshow = None, None, None, None, None, None, None, None, None, None, None
    freqmin, freqmax, specgram, zero = None, None, None, None
    colormap = 'Greys'
    gain = 1

# some of this needs to be tweaked to formulate a command call to one of the main body functions
# variables that can be passed to a body function: (infile, outfile, antfreq=None, frmt, plotting=False, stack=1)
    try:
        opts, args = getopt.getopt(sys.argv[1:],'hqdi:a:o:f:p:s:rwnmc:bg:z:t:',
            ['help','quiet','dmi','input=','antfreq=','output=','format=','plot=','stack=','bgr',
            'dewow','noshow','histogram','colormap=','colorbar','gain=','zero=','bandpass='])
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
                 colormap=colormap, colorbar=colorbar, gain=gain, bgr=bgr, zero=zero,
                 dewow=dewow, noshow=noshow, freqmin=freqmin, freqmax=freqmax)
        if verbose:
            fx.printmsg('done with %s' % infile)
        print('')
    else:
        fx.printmsg('ERROR: no input file was specified')
        fx.printmsg(config.help_text)
        sys.exit(2)

if __name__ == "__main__":
    '''
    this is the command line call use case. can't directly put code of main here.
    '''
    main()
