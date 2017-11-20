## readgssi.py
## intended to translate radar data from DZT to ASCII.
## DZT is a file format maintained by Geophysical Survey Systems Incorporated (GSSI).
## specifically, this script is intended for use with radar data recorded
## with GSSI SIR 4000 field units. Other field unit models may record DZT slightly
## differently, in which case this script will need to be modified.

# readgssi was originally written as matlab code by
# Gabe Lewis, Dartmouth College Department of Earth Sciences.
# matlab code was adapted for python with permission by
# Ian Nesbitt, University of Maine School of Earth and Climate Sciences.
# Copyright (c) 2017 Ian Nesbitt

# this code is freely available under the MIT License. if you did not receive
# a copy of the license upon obtaining this software, please visit
# (https://opensource.org/licenses/MIT) to obtain a copy.

import sys, getopt
import struct, bitstruct
import numpy as np
from datetime import datetime
import pytz

MINHEADSIZE = 1024
PAREASIZE = 128
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
GPS = {
    1: 'no',
    2: 'yes',
}
BPS = {
    8: '8 unsigned',
    16: '16 unsigned',
    32: '32 signed'
}

def readbit(bits, start, end):
    #try:
        if start == 0:
            return bitstruct.unpack('<u'+str(end+1), bits)[0]
        else:
            return bitstruct.unpack('<p'+str(start)+'u'+str(end-start), bits)[0]
    #except:
        #print('error reading bits')

def readtime(bits):
    if bits == '\x00\x00\x00\x00':
        return datetime(1980,1,1,0,0,0,0,tzinfo=pytz.UTC)
    else:
        try:
            sec2, mins, hr, day, mo, yr = bitstruct.unpack('<u5u6u5u5u4u7<', bits)
            #print("year: "+str(1980+yr))
            #print("month: "+str(mo))
            #print("day: "+str(day))
            #print("hour: "+str(hr))
            #print("min: "+str(mins))
            #print("sec: "+str(sec2*2))
            return datetime(yr+1980, mo, day, hr, mins, sec2*2, 0, tzinfo=pytz.UTC)
        except:
            return datetime(1980,1,1,0,0,0,0,tzinfo=pytz.UTC)

def readgssi(argv=None):
    # headerstruct = '<5h 5f h 4s 4s 7h 3I d I 3c x 3h d 2x 2c s s 14s s s 12s h 816s 76s'
    # readsize = (2,2,2,2,2,4,4,4,4,4,2,4,4,4,2,2,2,2,2,4,4,4,8,4,3,1,2,2,2,8,1,1,14,1,1,12,2)
    # dztstruct = Struct(headerstruct)
    # print('Calculated structure size: '+str(calcsize(headerstruct)))
    # packed_size = 0
    # for i in range(len(readsize)): packed_size = packed_size+readsize[i]
    # print('Calculated header size: '+str(packed_size)+'\n')
    infile = ''
    #outfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:",["input=","output="])
    except getopt.GetoptError:
        print 'readgssi.py -i <input file>'#' -o <output file>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'readgssi.py -i <input file>'# -o <output file>'
            sys.exit()
        elif opt in ("-i", "--input"):
            infile = arg
        #elif opt in ("-o", "--output"):
            #outfile = arg

    with open(infile, 'rb') as f:
        rh_tag = struct.unpack('<h', f.read(2))[0]
        rh_data = struct.unpack('<h', f.read(2))[0]
        rh_nsamp = struct.unpack('<h', f.read(2))[0]
        rh_bits = struct.unpack('<h', f.read(2))[0]
        rh_zero = struct.unpack('<h', f.read(2))[0]
        rhf_sps = struct.unpack('<f', f.read(4))[0]
        rhf_spm = struct.unpack('<f', f.read(4))[0]
        rhf_mpm = struct.unpack('<f', f.read(4))[0]
        rhf_position = struct.unpack('<f', f.read(4))[0]
        rhf_range = struct.unpack('<f', f.read(4))[0]
        rh_npass = struct.unpack('<h', f.read(2))[0]
        rhb_cdt = readtime(f.read(4))
        rhb_mdt = readtime(f.read(4))
        f.seek(44)
        rh_text = struct.unpack('<h', f.read(2))[0]
        rh_ntext = struct.unpack('<h', f.read(2))[0]
        rh_proc = struct.unpack('<h', f.read(2))[0]
        rh_nproc = struct.unpack('<h', f.read(2))[0]
        rh_nchan = struct.unpack('<h', f.read(2))[0]
        rhf_epsr = struct.unpack('<f', f.read(4))[0]
        rhf_top = struct.unpack('<f', f.read(4))[0]
        rhf_depth = struct.unpack('<f', f.read(4))[0]
        #rhf_coordx = struct.unpack('<ff', f.read(8))[0]
        f.seek(113)
        vsbyte = f.read(1)
        rh_version = readbit(vsbyte, 0, 2)
        rh_system = readbit(vsbyte, 3, 7)
        del vsbyte

        print('input file:         ' + infile)
        print('system:             ' + UNIT[rh_system])
        print('gps-enabled file:   ' + GPS[rh_version])
        print('number of channels: ' + str(rh_nchan))
        print('samples per trace:  ' + str(rh_nsamp))
        print('bits per sample:    ' + BPS[rh_bits])
        print('traces per second:  ' + str(rhf_sps))
        print('traces per meter:   ' + str(rhf_spm))
        print('dilectric:          ' + str(rhf_epsr))

        if rh_data < MINHEADSIZE:
            f.seek(MINHEADSIZE * rh_data)
        else:
            f.seek(MINHEADSIZE * rh_nchan)
        if rh_bits == 8:
            data = np.fromfile(f, np.uint8).reshape(-1,rh_nsamp).T
        elif rh_bits == 16:
            data = np.fromfile(f, np.uint16).reshape(-1,rh_nsamp).T
        else:
            data = np.fromfile(f, np.int32).reshape(-1,rh_nsamp).T

        print('traces:             ' + str(data.shape[1]))
        print('seconds:            ' + str(data.shape[1]/rhf_sps))

        #print('output file:        ' + outfile)

if __name__ == "__main__":
    readgssi(argv=sys.argv[1:])