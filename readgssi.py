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
# Copyright (c) 2017 Ian Nesbitt

# this code is freely available under the MIT License. if you did not receive
# a copy of the license upon obtaining this software, please visit
# (https://opensource.org/licenses/MIT) to obtain a copy.

import sys, getopt, os
import struct, bitstruct
import numpy as np
import pandas as pd
from datetime import datetime
import pytz

NAME = 'readgssi'
VERSION = '0.0.3-dev'
AUTHOR = 'Ian Nesbitt'
AFFIL = 'School of Earth and Climate Sciences, University of Maine'

MINHEADSIZE = 1024 # absolute minimum total header size
PAREASIZE = 128 # fixed info header size

# the GSSI field unit used
UNIT = {
    0: 'could not read system type',
    2: 'SIR 2000',
    3: 'SIR 3000',
    4: 'TerraVision',
    6: 'SIR 20',
    7: 'StructureScan Mini',
    8: 'SIR 4000',
    9: 'SIR 30',
    12: 'UtilityScan DF',
    13: 'HS',
    14: 'StructureScan Mini XT',
}

# whether or not the file is GPS-enabled (does not guarantee presence of GPS data in file)
GPS = {
    1: 'no',
    2: 'yes',
}

# bits per data word in radar array
BPS = {
    8: '8 unsigned',
    16: '16 unsigned',
    32: '32 signed'
}


def readbit(bits, start, end):
    '''
    function to read variables bitwise, where applicable
    '''
    try:
        if start == 0:
            return bitstruct.unpack('<u'+str(end+1), bits)[0]
        else:
            return bitstruct.unpack('<p'+str(start)+'u'+str(end-start), bits)[0]
    except:
        print('error reading bits')

def readtime(bits):
    '''
    function to read dates bitwise.
    this is a colossally stupid way of storing dates. I have no idea if I'm unpacking them correctly.
    (and every indication that I'm not.)
    '''
    if bits == '\x00\x00\x00\x00':
        return datetime(1980,1,1,0,0,0,0,tzinfo=pytz.UTC) # if there is no date information, return arbitrary datetime
    else:
        try:
            sec2, mins, hr, day, mo, yr = bitstruct.unpack('<u5u6u5u5u4u7', bits) # if there is date info, try to unpack
            # year+1980 should equal real year
            # sec2 * 2 should equal real seconds
            return datetime(yr+1980, mo, day, hr, mins, sec2*2, 0, tzinfo=pytz.UTC)
        except:
            return datetime(1980,1,1,0,0,0,0,tzinfo=pytz.UTC) # most of the time the info returned is garbage, so we return arbitrary datetime again

def readgssi(argv=None, call=None):
    '''
    function to unpack and return things we need from the header, and the data itself

    currently unused but potentially useful lines:
    # headerstruct = '<5h 5f h 4s 4s 7h 3I d I 3c x 3h d 2x 2c s s 14s s s 12s h 816s 76s' # the structure of the bytewise header and "gps data" as I understand it - 1024 bytes
    # readsize = (2,2,2,2,2,4,4,4,4,4,2,4,4,4,2,2,2,2,2,4,4,4,8,4,3,1,2,2,2,8,1,1,14,1,1,12,2) # the variable size of bytes in the header (most of the time) - 128 bytes
    # print('total header structure size: '+str(calcsize(headerstruct)))
    # packed_size = 0
    # for i in range(len(readsize)): packed_size = packed_size+readsize[i]
    # print('fixed header size: '+str(packed_size)+'\n')
    '''
    infile = ''
    outfile = ''
    frmt = ''
    help_text = 'usage:\nreadgssi.py -i <input file> -o <output file> -f <format: (csv|h5|segy)>\n' # help text string

    # parse passed command line arguments. this may get moved somewhere else, but for now:
    try:
        opts, args = getopt.getopt(argv,'hi:o:f:',['help','input=','output=','format='])
    # the 'no option supplied' error
    except getopt.GetoptError:
        print('invalid argument(s) supplied')
        print(help_text)
        sys.exit(2)
    for opt, arg in opts: 
        if opt in ('-h', '--help'): # the help case
            print(AUTHOR)
            print(AFFIL + '\n')
            print(help_text)
            sys.exit()
        if opt in ('-i', '--input'): # the input file
            if arg:
                infile = arg
                if '~' in infile:
                    infile = os.path.expanduser(infile) # if using --input=~/... tilde needs to be expanded 
        if opt in ('-o', '--output'): # the output file
            if arg:
                outfile = arg
                if '~' in outfile:
                    outfile = os.path.expanduser(infile) # expand tilde, see above
        if opt in ('-f', '--format'): # the format string
            # check whether the string is a supported format
            if arg:
                if arg in ('csv', 'CSV'):
                    frmt = 'csv'
                elif arg in ('sgy', 'segy', 'seg-y', 'SGY', 'SEGY', 'SEG-Y'):
                    frmt = 'segy'
                elif arg in ('h5', 'hdf5', 'H5', 'HDF5'):
                    frmt = 'h5'
                else:
                    # else the user has given an invalid format
                    print(help_text)
                    sys.exit(2)
            else:
                print(help_text)
                sys.exit(2)

    if infile:
        try:
            with open(infile, 'rb') as f:
                # open the binary, start reading chunks
                rh_tag = struct.unpack('<h', f.read(2))[0] # 0x00ff if header, 0xfnff if old file format
                rh_data = struct.unpack('<h', f.read(2))[0] # offset to data from beginning of file
                rh_nsamp = struct.unpack('<h', f.read(2))[0] # samples per scan
                rh_bits = struct.unpack('<h', f.read(2))[0] # bits per data word
                rh_zero = struct.unpack('<h', f.read(2))[0] # if sir-30 or utilityscan df, then repeats per sample; otherwise 0x80 for 8bit and 0x8000 for 16bit
                rhf_sps = struct.unpack('<f', f.read(4))[0] # scans per second
                rhf_spm = struct.unpack('<f', f.read(4))[0] # scans per meter
                rhf_mpm = struct.unpack('<f', f.read(4))[0] # meters per mark
                rhf_position = struct.unpack('<f', f.read(4))[0] # position (ns)
                rhf_range = struct.unpack('<f', f.read(4))[0] # range (ns)
                rh_npass = struct.unpack('<h', f.read(2))[0] # number of passes for 2-D files
                rhb_cdt = readtime(f.read(4)) # creation date and time in bits, structured as little endian u5u6u5u5u4u7
                rhb_mdt = readtime(f.read(4)) # modification date and time in bits, structured as little endian u5u6u5u5u4u7
                f.seek(44) # skip across some proprietary BS
                rh_text = struct.unpack('<h', f.read(2))[0] # offset to text
                rh_ntext = struct.unpack('<h', f.read(2))[0] # size of text
                rh_proc = struct.unpack('<h', f.read(2))[0] # offset to processing history
                rh_nproc = struct.unpack('<h', f.read(2))[0] # size of processing history
                rh_nchan = struct.unpack('<h', f.read(2))[0] # number of channels
                rhf_epsr = struct.unpack('<f', f.read(4))[0] # average dilectric
                rhf_top = struct.unpack('<f', f.read(4))[0] # position in meters (useless?)
                rhf_depth = struct.unpack('<f', f.read(4))[0] # range in meters (again-useless?)
                #rhf_coordx = struct.unpack('<ff', f.read(8))[0] # this is definitely useless
                f.seek(113) # skip to something that matters
                vsbyte = f.read(1) # byte containing versioning bits
                rh_version = readbit(vsbyte, 0, 2) # whether or not the system is GPS-capable (probably does not mean GPS is in file)
                rh_system = readbit(vsbyte, 3, 7) # the system type (values in UNIT={...} dictionary above)
                del vsbyte


                if rh_data < MINHEADSIZE: # whether or not the header is normal or big-->determines offset to data array
                    f.seek(MINHEADSIZE * rh_data)
                else:
                    f.seek(MINHEADSIZE * rh_nchan)

                if rh_bits == 8:
                    data = np.fromfile(f, np.uint8).reshape(-1,rh_nsamp).T # 8-bit
                elif rh_bits == 16:
                    data = np.fromfile(f, np.uint16).reshape(-1,rh_nsamp).T # 16-bit
                else:
                    data = np.fromfile(f, np.int32).reshape(-1,rh_nsamp).T # 32-bit

                # create returns dictionary
                returns = {
                    'infile': infile,
                    'outfile': outfile,
                    'frmt': frmt,
                    'rh_system': rh_system,
                    'rh_version': rh_version,
                    'rh_nchan': rh_nchan,
                    'rh_nsamp': rh_nsamp,
                    'rh_bits': rh_bits,
                    'rhf_sps': rhf_sps,
                    'rhf_spm': rhf_spm,
                    'rhf_epsr': rhf_epsr,
                }

                return returns, data
        except IOError as e: # when the user selects an inaccessible or nonexistent file
            print("i/o error: DZT file is inaccessable or does not exist")
            print('detail: ' + str(e) + '\n')
            print(help_text)
        

if __name__ == "__main__":
    '''
    this is the command line use case
    '''
    print(NAME + ' ' + VERSION)
    try:
        r = readgssi(argv=sys.argv[1:])
        rhf_sps = r[0]['rhf_sps']
        rhf_spm = r[0]['rhf_spm']
        # print some useful things to command line users from returned dictionary
        print('input file:         ' + r[0]['infile'])
        print('system:             ' + UNIT[r[0]['rh_system']])
        print('gps-enabled file:   ' + GPS[r[0]['rh_version']])
        print('number of channels: ' + str(r[0]['rh_nchan']))
        print('samples per trace:  ' + str(r[0]['rh_nsamp']))
        print('bits per sample:    ' + BPS[r[0]['rh_bits']])
        print('traces per second:  ' + str(rhf_sps))
        print('traces per meter:   ' + str(rhf_spm))
        print('dilectric:          ' + str(r[0]['rhf_epsr']))
        print('traces:             ' + str(r[1].shape[1]))
        if rhf_spm == 0:
            print('seconds:            ' + str(r[1].shape[1]/rhf_sps))
        else:
            print('meters:             ' + str(r[1].shape[1]/rhf_spm))
        if r[0]['frmt']:
            print('outputting to ' + r[0]['frmt'] + " . . .")
            data = pd.DataFrame(r[1]) # using pandas to output csv
            if r[0]['frmt'] in 'csv':
                if r[0]['outfile']: # if output is given
                    of = os.path.abspath(r[0]['outfile']) # set output to given location
                else: # if no output is given
                    # set output to the same dir as input file
                    of = os.path.abspath(os.path.splitext(r[0]['infile'])[0] + '.' + r[0]['frmt'])
                print('writing file to:    ' + of)
                data.to_csv(of) 
            elif r[0]['frmt'] in 'h5':
                print('hdf5 is not yet supported, please choose another format.')
            elif r[0]['frmt'] in 'segy':
                print('SEG-Y is not yet supported, please choose another format.')
            print('done.')
        

    except TypeError as e: # shows up when the user selects an input file that doesn't exist
        print('')
        sys.exit(2)
