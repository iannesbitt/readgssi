import struct
import math
import os
import numpy as np
from datetime import datetime
from itertools import takewhile
from readgssi.gps import readdzg
import readgssi.functions as fx
from readgssi.constants import *

'''
helper module for reading information from GSSI DZT files

the main function, readdzt(), returns header information in dictionary format
and the radar profile in a numpy array.

readdzt_gprpy() restructures output for use specifically with
Alain Plattner's GPRPy software (https://github.com/NSGeophysics/GPRPy).
'''

def readtime(bytes):
    '''
    function to read dates
    have i mentioned yet that this is not a great way of storing dates
    
    DZT rfDateBytes are 32 bits of binary (01001010111110011010011100101111)
    structured as little endian u5u6u5u5u4u7 where
    all numbers are unsigned int (uX) composed of X number of bits

    so we read (seconds/2, min, hr, day, month, year-1980)
    then do seconds*2 and year+1980 and return a datetime object
    '''
    dtbits = ''
    rfDateByte = (b for b in bytes)
    for byte in rfDateByte:                    # assemble the binary string
        for i in range(8):
            dtbits += str((byte >> i) & 1)
    dtbits = dtbits[::-1]               # flip the string
    sec2 = int(dtbits[27:32], 2) * 2
    mins = int(dtbits[21:27], 2)
    hr = int(dtbits[16:21], 2)
    day = int(dtbits[11:16], 2)
    mo = int(dtbits[7:11], 2)
    yr = int(dtbits[0:7], 2) + 1980
    return datetime(yr, mo, day, hr, mins, sec2, 0, tzinfo=pytz.UTC)

def readdzt(infile, gps=False, verbose=False):
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
    infile_gps = os.path.splitext(infile)[0] + ".DZG"
    infile = open(infile, 'rb')
    header = {}
    header['infile'] = infile.name
    header['known_ant'] = [None, None, None, None]
    header['rh_ant'] = [None, None, None, None]
    header['rh_antname'] = [None, None, None, None]
    header['antfreq'] = [None, None, None, None]

    # begin read

    header['rh_tag'] = struct.unpack('<h', infile.read(2))[0] # 0x00ff if header, 0xfnff if old file format
    header['rh_data'] = struct.unpack('<h', infile.read(2))[0] # offset to data from beginning of file
    header['rh_nsamp'] = struct.unpack('<h', infile.read(2))[0] # samples per scan
    header['rh_bits'] = struct.unpack('<h', infile.read(2))[0] # bits per data word
    header['rh_zero'] = struct.unpack('<h', infile.read(2))[0] # if sir-30 or utilityscan df, then repeats per sample; otherwise 0x80 for 8bit and 0x8000 for 16bit
    header['rhf_sps'] = struct.unpack('<f', infile.read(4))[0] # scans per second
    header['rhf_spm'] = struct.unpack('<f', infile.read(4))[0] # scans per meter
    header['rhf_mpm'] = struct.unpack('<f', infile.read(4))[0] # meters per mark
    header['rhf_position'] = struct.unpack('<f', infile.read(4))[0] # position (ns)
    header['rhf_range'] = struct.unpack('<f', infile.read(4))[0] # range (ns)
    header['rh_npass'] = struct.unpack('<h', infile.read(2))[0] # number of passes for 2-D files
    # bytes 32-36 and 36-40: creation and modification date and time in bits
    # structured as little endian u5u6u5u5u4u7
    infile.seek(32)
    try:
        header['rhb_cdt'] = readtime(infile.read(4))
    except:
        header['rhb_cdt'] = datetime(1980, 1, 1)
    try:
        header['rhb_mdt'] = readtime(infile.read(4))
    except:
        header['rhb_mdt'] = datetime(1980, 1, 1)
    header['rh_rgain'] = struct.unpack('<h', infile.read(2))[0] # offset to range gain function
    header['rh_nrgain'] = struct.unpack('<h', infile.read(2))[0] # size of range gain function
    header['rh_text'] = struct.unpack('<h', infile.read(2))[0] # offset to text
    header['rh_ntext'] = struct.unpack('<h', infile.read(2))[0] # size of text
    header['rh_proc'] = struct.unpack('<h', infile.read(2))[0] # offset to processing history
    header['rh_nproc'] = struct.unpack('<h', infile.read(2))[0] # size of processing history
    header['rh_nchan'] = struct.unpack('<h', infile.read(2))[0] # number of channels
    header['rhf_epsr'] = struct.unpack('<f', infile.read(4))[0] # average dilectric
    header['rhf_top'] = struct.unpack('<f', infile.read(4))[0] # position in meters (useless?)
    header['rhf_depth'] = struct.unpack('<f', infile.read(4))[0] # range in meters
    #rhf_coordx = struct.unpack('<ff', infile.read(8))[0] # this is definitely useless

    # read frequencies for multiple antennae
    for chan in list(range(header['rh_nchan'])):
        if chan == 0:
            infile.seek(98) # start of antenna section
        else:
            infile.seek(98 + (MINHEADSIZE*(chan))) # start of antenna bytes for channel n
        header['rh_ant'][chan] = infile.read(14).decode('utf-8').split('\x00')[0]
        header['rh_antname'][chan] = header['rh_ant'][chan].rsplit('x')[0]
        try:
            header['antfreq'][chan] = ANT[header['rh_antname'][chan]]
            header['known_ant'][chan] = True
        except KeyError:
            header['known_ant'][chan] = False
            header['antfreq'][chan] = int("".join(takewhile(str.isdigit, header['rh_ant'][chan].replace('D5','').replace('D6','')))) # hoping this works
            #header['antfreq'][chan] = int(header['rh_antname'][chan].replace('D5','').replace('D6',''))

    infile.seek(113) # skip to something that matters
    vsbyte = infile.read(1) # byte containing versioning bits
    header['rh_version'] = ord(vsbyte) >> 5 # whether or not the system is GPS-capable, 1=no 2=yes (does not mean GPS is in file)
    header['rh_system'] = ord(vsbyte) >> 3 # the system type (values in UNIT={...} dictionary above)

    infile.seek(header['rh_rgain'])
    try:
        header['rgain_bytes'] = infile.read(header['rh_nrgain'])
    except:
        pass

    if header['rh_data'] < MINHEADSIZE: # whether or not the header is normal or big-->determines offset to data array
        infile.seek(MINHEADSIZE * header['rh_data'])
        header['data_offset'] = MINHEADSIZE * header['rh_data']
    else:
        infile.seek(MINHEADSIZE * header['rh_nchan'])
        header['data_offset'] = MINHEADSIZE * header['rh_nchan']

    if header['rh_bits'] == 8:
        dtype = np.uint8 # 8-bit unsigned
    elif header['rh_bits'] == 16:
        dtype = np.uint16 # 16-bit unsigned
    else:
        dtype = np.int32 # 32-bit signed

    # read in and transpose data
    data = np.fromfile(infile, dtype).reshape(-1,(header['rh_nsamp']*header['rh_nchan'])).T

    header['cr'] = 1 / math.sqrt(Mu_0 * Eps_0 * header['rhf_epsr'])
    header['sec'] = data.shape[1]/float(header['rhf_sps'])
    header['traces'] = int(data.shape[1]/header['rh_nchan'])

    infile.close()

    if gps:
        try:
            if verbose:
                fx.printmsg('reading GPS file...')
            gps = readdzg(infile_gps, 'dzg', header, verbose=verbose)
        except IOError as e0:
            fx.printmsg('WARNING: no DZG file found')
            try:
                infile_gps = os.path.splitext(infile_gps)[0] + ".csv"
                gps = readdzg(infile_gps, 'csv', header, verbose=verbose)
            except Exception as e1:
                try:
                    infile_gps = os.path.splitext(infile_gps)[0] + ".CSV"
                    gps = readdzg(infile_gps, 'csv', header, verbose=verbose)
                except Exception as e2:
                    fx.printmsg('ERROR reading GPS. distance normalization will not be possible.')
                    fx.printmsg('   details: %s' % e0)
                    fx.printmsg('            %s' % e1)
                    fx.printmsg('            %s' % e2)
                    gps = []
    else:
        pass

    return [header, data, gps]

def readdzt_gprpy(infile):
    r = readdzt(infile)
    data = r[1]
    header = {
        'sptrace': r[0]['rh_nsamp'],
        'scpsec': r[0]['rhf_sps'],
        'scpmeter': r[0]['rhf_spm'],
        'startposition': r[0]['rhf_position'],
        'nanosecptrace': r[0]['rhf_range'],
        'scansppass': r[0]['rh_npass'],
    }
    return data, header

def header_info(header, data):
    '''
    function to print relevant header data
    '''
    fx.printmsg('system:             %s' % UNIT[header['rh_system']])
    fx.printmsg('antennas:           %s' % header['rh_antname'])

    for i in range(header['rh_nchan']):
        if header['known_ant'][i] == True:
            fx.printmsg('ant %s frequency:    %s MHz' % (i, ANT[header['rh_antname'][i]]))
        else:
            fx.printmsg('ant %s frequency:    %s MHz (antenna name %s not in current dictionary)'
                        % (i, header['antfreq'][i], header['rh_antname'][i]))

    fx.printmsg('date created:       %s' % header['rhb_cdt'])
    if header['rhb_mdt'] == datetime(1980, 1, 1):
        fx.printmsg('date modified:      (never modified)')
    else:
        fx.printmsg('date modified:      %s' % header['rhb_mdt'])
    try:
        fx.printmsg('gps-enabled file:   %s' % GPS[header['rh_version']])
    except (TypeError, KeyError) as e:
        fx.printmsg('gps-enabled file:   unknown')
    fx.printmsg('number of channels: %i' % header['rh_nchan'])
    fx.printmsg('samples per trace:  %i' % header['rh_nsamp'])
    fx.printmsg('bits per sample:    %s' % BPS[header['rh_bits']])
    fx.printmsg('traces per second:  %.1f' % header['rhf_sps'])
    fx.printmsg('traces per meter:   %.1f' % header['rhf_spm'])
    fx.printmsg('dilectric:          %.1f' % header['rhf_epsr'])
    fx.printmsg('speed of light:     %.2E m/sec (%.2f%% of vacuum)' % (header['cr'], header['cr'] / C * 100))
    fx.printmsg('sampling depth:     %.1f m' % header['rhf_depth'])
    fx.printmsg('offset to data:     %i bytes' % header['data_offset'])
    if data.shape[1] == int(data.shape[1]):
        fx.printmsg('traces:             %i' % int(data.shape[1]/header['rh_nchan']))
    else:
        fx.printmsg('traces:             %f' % int(data.shape[1]/header['rh_nchan']))
    fx.printmsg('seconds:            %.8f' % (header['sec']))
    fx.printmsg('samp/m:             %.2f (zero unless DMI present)' % (float(header['rhf_spm']))) # I think...
    fx.printmsg('array dimensions:   %i x %i' % (data.shape[0], data.shape[1]))
