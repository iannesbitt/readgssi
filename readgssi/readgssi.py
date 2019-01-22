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
from obspy.signal.filter import bandpass
from obspy.imaging.spectrogram import spectrogram
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as colors
#from mpl_toolkits.basemap import Basemap
import pandas as pd
import math
from decimal import Decimal
from datetime import datetime, timedelta
import pytz
import h5py
import pynmea2

NAME = 'readgssi'
VERSION = '0.0.7'
YEAR = 2019
AUTHOR = 'Ian Nesbitt'
AFFIL = 'School of Earth and Climate Sciences, University of Maine'

HELP_TEXT = '''usage:
python readgssi.py -i input.DZT [OPTIONS]

optional flags:
     OPTION     |      ARGUMENT       |       FUNCTIONALITY
-v, --verbose   |                     |  verbosity
-o, --output    | file:  /dir/f.ext   |  specify an output file
-f, --format    | string, eg. "csv"   |  specify output format (csv is the only working format currently)
-p, --plot      | +integer or "auto"  |  plot will be x inches high (dpi=150), or "auto". default: 10
-n, --noshow    |                     |  suppress matplotlib popup window and simply save a figure (useful for multiple file processing)
-c, --colormap  | string, eg. "Greys" |  specify the colormap (https://matplotlib.org/users/colormaps.html#grayscale-conversion)
-g, --gain      | positive (+)integer |  gain value (higher=greater contrast, default: 1)
-r, --bgr       |                     |  horizontal background removal algorithm (useful to remove ringing)
-w, --dewow     |                     |  trinomial dewow algorithm
-t, --bandpass  | +int-+int (MHz)     |  butterworth bandpass filter (positive integer range in megahertz; ex. 100-145)
-b, --colorbar  |                     |  add a colorbar to the radar figure
-a, --antfreq   | positive integer    |  specify antenna frequency (read automatically if not given)
-s, --stack     | +integer or "auto"  |  specify trace stacking value or "auto" to autostack to ~2.5:1 x:y axis ratio
-m, --histogram |                     |  produce a histogram of data values
-z, --zero      | positive integer    |  skip this many samples from the top of the trace downward (useful for removing transceiver delay)
'''

#optional flag: -d, denoting radar pulses triggered with a distance-measuring instrument (DMI) like a survey wheel' # help text string


MINHEADSIZE = 1024 # absolute minimum total header size
PAREASIZE = 128 # fixed info header size

TZ = pytz.timezone('UTC')

# some physical constants for Maxwell's equation for speed of light in a dilectric
C = 299792458                   # speed of light in a vacuum
Eps_0 = 8.8541878 * 10**(-12)   # epsilon naught (vacuum permittivity)
Mu_0 = 1.257 * 10**(-6)         # mu naught (vacuum permeability)


# the GSSI field unit used
UNIT = {
    0: 'unknown system type',
    1: 'unknown system type',
    2: 'SIR 2000',
    3: 'SIR 3000',
    4: 'TerraVision',
    6: 'SIR 20',
    7: 'StructureScan Mini',
    8: 'SIR 4000',
    9: 'SIR 30',
    10: 'SIR 30', # 10 is undefined in documentation but SIR 30 according to Lynn's DZX
    11: 'unknown system type',
    12: 'UtilityScan DF',
    13: 'HS',
    14: 'StructureScan Mini XT',
}

# a dictionary of standard gssi antennas and frequencies
# unsure of what they all look like in code, however
ANT = {
    '3200': ('adjustable'),
    '3200MLF': ('adjustable'),
    '500MHz': (500,),
    '3207': (100,),
    '3207AP': (100,),
    '5106': (200,),
    '5106A': (200,),
    '50300': (300,),
    '350': (350,),
    '350HS': (350,),
    '50270': (270,),
    '50270S': (270,),
    '50400': (400,),
    '50400S': (400,),
    '800': (800,),
    '3101': (900,),
    '3101A': (900,),
    '51600': (1600,),
    '51600S': (1600,),
    '62000': (2000,),
    '62000-003': (2000,),
    '62300': (2300,),
    '62300XT': (2300,),
    '52600': (2600,),
    '52600S': (2600,),
    'D50800': (800,300,),
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

def readtime(bits):
    '''
    function to read dates bitwise.
    this is a colossally stupid way of storing dates.
    I know I'm not unpacking them correctly, a fix is in the development queue
    '''
    garbagedate = datetime(1980,1,1,0,0,0,0,tzinfo=pytz.UTC)
    if bits == '\x00\x00\x00\x00':
        return garbagedate # if there is no date information, return arbitrary datetime
    else:
        try:
            sec2, mins, hr, day, mo, yr = bitstruct.unpack('<u5u6u5u5u4u7', bits) # if there is date info, try to unpack
            # year+1980 should equal real year
            # sec2 * 2 should equal real seconds
            return datetime(yr+1980, mo, day, hr, mins, sec2*2, 0, tzinfo=pytz.UTC)
        except:
            return garbagedate # most of the time the info returned is garbage, so we return arbitrary datetime again

def readdzg(fi, frmt, spu, traces, verbose=False):
    '''
    a parser to extract gps data from DZG file format
    DZG contains raw NMEA sentences, which should include RMC and GGA
    fi = file containing gps information
    frmt = format ('dzg' = DZG file containing gps sentence strings (see below); 'csv' = comma separated file with)
    spu = samples per unit (second or meter)
    traces = the number of traces in the file
    Reading DZG
    We need to relate gpstime to scan number then interpolate for each scan
    between gps measurements.
    NMEA GGA sentence string format:
    $GPGGA,UTC hhmmss.s,lat DDmm.sss,lon DDDmm.sss,fix qual,numsats,hdop,mamsl,wgs84 geoid ht,fix age,dgps sta.,checksum *xx
    if we want the date, we have to read RMC sentences as well:
    $GPRMC,UTC hhmmss,status,lat DDmm.sss,lon DDDmm.sss,SOG,COG,date ddmmyy,checksum *xx
    RMC strings may also be useful for SOG and COG,
    ...but let's keep it simple for now.
    '''
    trace = 0 # the elapsed number of traces iterated through
    tracenum = 0 # the sequential increase in trace number
    rownp = 0 # array row number
    rowrmc = 0 # rmc record iterated through (gps file)
    rowgga = 0 # gga record
    timestamp = False
    prevtime = False
    td = False
    prevtrace = False
    rmc = False
    antname = False
    lathem = 'north'
    lonhem = 'east'
    x0, x1, y0, y1, z0, z1 = False, False, False, False, False, False # coordinates
    with open(fi, 'r') as gf:
        if frmt == 'dzg': # if we're working with DZG format
            for ln in gf: # loop through the first few sentences, check for RMC
                if ln.startswith('$GPRMC'): # check to see if RMC sentence (should occur before GGA)
                    rmc = True
                    if rowrmc == 10: # we'll assume that 10 samples is a safe distance into the file to measure frequency
                        msg = pynmea2.parse(ln.rstrip()) # convert gps sentence to pynmea2 named tuple
                        ts0 = datetime.combine(msg.datestamp, msg.timestamp) # row 0's timestamp
                    if rowrmc == 11:
                        msg = pynmea2.parse(ln.rstrip())
                        ts1 = datetime.combine(msg.datestamp, msg.timestamp) # row 1's timestamp
                        td = ts1 - ts0 # timedelta = datetime1 - datetime0
                    rowrmc += 1
                if ln.startswith('$GPGGA'):
                    if rowgga == 10:
                        msg = pynmea2.parse(ln.rstrip()) # convert gps sentence to pynmea2 named tuple
                        ts0 = datetime.combine(datetime(1980, 1, 1), msg.timestamp) # row 0's timestamp (not ideal)
                    if rowgga == 11:
                        msg = pynmea2.parse(ln.rstrip())
                        ts1 = datetime.combine(datetime(1980, 1, 1), msg.timestamp) # row 1's timestamp (not ideal)
                        td = ts1 - ts0 # timedelta = datetime1 - datetime0
                    rowgga += 1
            if rowgga != rowrmc:
                print("WARNING: GGA and RMC sentences are not recorded at the same rate! This could cause unforseen problems!")
                print('rmc records: %i' % rowrmc)
                print('gga records: %i' % rowgga)
            gpssps = 1 / td.total_seconds() # GPS samples per second
            if verbose:
                print('found %i GPS epochs at rate of %.1f Hz' % (rowrmc, gpssps))
            dt = [('tracenum', 'float32'), ('lat', 'float32'), ('lon', 'float32'), ('altitude', 'float32'), ('geoid_ht', 'float32'), ('qual', 'uint8'), ('num_sats', 'uint8'), ('hdop', 'float32'), ('gps_sec', 'float32'), ('timestamp', 'datetime64[us]')] # array columns
            arr = np.zeros((int(traces)+1000), dt) # numpy array with num rows = num gpr traces, and columns defined above
            if verbose:
                print('creating array of %i interpolated gps locations...' % (traces))
            gf.seek(0) # back to beginning of file
            for ln in gf: # loop over file line by line
                if rmc == True: # if there is RMC, we can use the full datestamp
                    if ln.startswith('$GPRMC'):
                        msg = pynmea2.parse(ln.rstrip())
                        timestamp = TZ.localize(datetime.combine(msg.datestamp, msg.timestamp)) # set t1 for this loop
                else: # if no RMC, we best hope there is no UTC 0:00:00 in the file.........
                    if ln.startswith('$GPGGA'):
                        msg = pynmea2.parse(ln.rstrip())
                        timestamp = TZ.localize(msg.timestamp) # set t1 for this loop
                if ln.startswith('$GPGGA'):
                    sec1 = float(ln.split(',')[1])
                    msg = pynmea2.parse(ln.rstrip())
                    x1, y1, z1, gh, q, sats, dil = float(msg.lon), float(msg.lat), float(msg.altitude), float(msg.geo_sep), int(msg.gps_qual), int(msg.num_sats), float(msg.horizontal_dil)
                    if msg.lon_dir in 'W':
                        lonhem = 'west'
                        x1 = -x1
                    if msg.lat_dir in 'S':
                        lathem = 'south'
                        y1 = -y1
                    if prevtime: # if this is our second or more GPS epoch, calculate delta trace and current trace
                        elapsedelta = timestamp - prevtime # t1 - t0 in timedelta format
                        elapsed = float((elapsedelta).total_seconds()) # seconds elapsed
                        if elapsed > 3600.0:
                            print("WARNING: Time jumps by more than an hour in this GPS dataset and there are no RMC sentences to anchor the datestamp!")
                            print("This dataset may cross over the UTC midnight dateline!\nprevious timestamp: %s\ncurrent timestamp:  %s" % (prevtime, timestamp))
                            print("trace number:       %s" % trace)
                        tracenum = round(elapsed * spu, 8) # calculate the increase in trace number, rounded to 5 decimals to eliminate machine error
                        trace += tracenum # increment to reflect current trace
                        resamp = np.arange(math.ceil(prevtrace), math.ceil(trace), 1) # make an array of integer values between t0 and t1
                        for t in resamp:
                            x = (x1 - x0) / (elapsed) * (t - prevtrace) + x0 # interpolate latitude
                            y = (y1 - y0) / (elapsed) * (t - prevtrace) + y0 # interpolate longitude
                            z = (z1 - z0) / (elapsed) * (t - prevtrace) + z0 # interpolate altitude
                            sec = (sec1 - sec0) / (elapsed) * (t - prevtrace) + sec0 # interpolate gps seconds
                            tracetime = prevtime + timedelta(seconds=elapsedelta.total_seconds() * (t - prevtrace))
                            tup = (t, x, y, z, gh, q, sats, dil, sec, tracetime)
                            arr[rownp] = tup
                            rownp += 1
                    else: # we're on the very first row
                        if verbose:
                            print('using %s and %s hemispheres' % (lonhem, lathem))
                    x0, y0, z0, sec0 = x1, y1, z1, sec1 # set xyzs0 for next loop
                    prevtime = timestamp # set t0 for next loop
                    prevtrace = trace
            if verbose:
                print('processed %i gps locations' % rownp)
            diff = rownp - traces
            shift, endshift = 0, 0
            if diff > 0:
                shift = diff / 2
                if diff / 2 == diff / 2.:
                    endshift = shift
                else:
                    endshift = shift - 1
            arrend = traces + endshift
            arr = arr[shift:arrend:1]
            if verbose:
                print('cut %i rows from beginning and %s from end of gps array, new size %s' % (shift, endshift, arr.shape[0]))
            # if there's no need to use pandas, we shouldn't (library load speed mostly, also this line is old):
            #array = pd.DataFrame({ 'ts' : arr['ts'], 'lat' : arr['lat'], 'lon' : arr['lon'] }, index=arr['tracenum'])
        elif frmt == 'csv':
            arr = ''
    return arr

def readdzt(infile):
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
    infile.seek(31) # ensure correct read position for rfdatebyte
    rhb_cdt = readtime(infile.read(4)) # creation date and time in bits, structured as little endian u5u6u5u5u4u7
    rhb_mdt = readtime(infile.read(4)) # modification date and time in bits, structured as little endian u5u6u5u5u4u7
    infile.seek(44) # skip across some proprietary stuff
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
    
    rh_antname = rh_ant
    
    infile.seek(113) # skip to something that matters
    vsbyte = infile.read(1) # byte containing versioning bits
    rh_version = ord(vsbyte) >> 5 # whether or not the system is GPS-capable, 1=no 2=yes (does not mean GPS is in file)
    rh_system = ord(vsbyte) >> 3 # the system type (values in UNIT={...} dictionary above)
    del vsbyte
    
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

    # create dictionary
    header = {
        'rh_antname': rh_antname.rsplit('x')[0],
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
    }

    return [header, data]

def header_info(header, data):
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
    print('input file:         %s' % header['infile'])
    print('system:             %s' % UNIT[header['rh_system']])
    print('antenna:            %s' % header['rh_antname'])
    if header['rh_nchan'] > 1:
        i = 1
        for ar in ANT[header['rh_antname']]:
            print('ant %s frequency:   %s MHz' % (ar))
    else:
        print('antenna frequency:  %s MHz' % ANT[header['rh_antname']])
    print('date created:       %s' % header['rhb_cdt'])
    print('date modified:      %s' % header['rhb_mdt'])
    try:
        print('gps-enabled file:   %s' % GPS[header['rh_version']])
    except (TypeError, KeyError) as e:
        print('gps-enabled file:   %s' % 'unknown')
    print('number of channels: %i' % header['rh_nchan'])
    print('samples per trace:  %i' % header['rh_nsamp'])
    print('bits per sample:    %s' % BPS[header['rh_bits']])
    print('traces per second:  %.1f' % header['rhf_sps'])
    print('traces per meter:   %.1f' % header['rhf_spm'])
    print('dilectric:          %.1f' % header['rhf_epsr'])
    print('speed of light:     %.2E m/sec (%.2f%% of vacuum)' % (header['cr'], header['cr'] / C * 100))
    print('sampling depth:     %.1f m' % header['rhf_depth'])
    if data.shape[1] == int(data.shape[1]):
        print('traces:             %i' % int(data.shape[1]/header['rh_nchan']))
    else:
        print('traces:             %f' % int(data.shape[1]/header['rh_nchan']))
    print('seconds:            %.8f' % line_dur)
    print('samp/m:             %.2f' % (float(rhf_spm)))


def readgssi(infile, outfile=None, antfreq=None, frmt=None, plot=False, figsize=10,
             stack=1, verbose=False, histogram=False, colormap='Greys', colorbar=False,
             zero=1, gain=1, freqmin=None, freqmax=None, bgr=False, dewow=False,
             specgram=False, noshow=False):
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

    if infile:
        # read the file
        if verbose:
            print('reading header information...')
        try:
            with open(infile, 'rb') as f:
                # open the binary, attempt reading chunks
                r = readdzt(f)
        except IOError as e: # the user has selected an inaccessible or nonexistent file
            print("i/o error: DZT file is inaccessable or does not exist")
            print('detail: ' + str(e) + '\n')
            print(HELP_TEXT)
            sys.exit(2)
    else:
        print('error: no input file was specified')
        print(HELP_TEXT)
        sys.exit(2)

    try:
        rhf_sps = r[0]['rhf_sps']
        rhf_spm = r[0]['rhf_spm']
        line_dur = r[1].shape[1]/rhf_sps
        if antfreq != None:
            freq = antfreq
            print('user specified antenna frequency: %s' % antfreq)
        elif r[0]['rh_antname']:
            try:
                freq = ANT[r[0]['rh_antname']]
            except ValueError as e:
                print('WARNING: could not read frequency for given antenna name.\nerror info: %s' % e)
                print(HELP_TEXT)
                sys.exit(2)
        else:
            print('no frequency information could be read from the header.\nplease specify the frequency of the antenna in MHz using the -a flag.')
            print(HELP_TEXT)
            sys.exit(2)
    # an except should go here

        if frmt != None:
            print('outputting to %s . . .' % frmt)

            fnoext = os.path.splitext(infile)[0]
            # is there an output filepath given?
            if outfile: # if output is given
                of = os.path.abspath(outfile) # set output to given location
            else: # if no output is given
                # set output to the same dir as input file
                of = os.path.abspath(fnoext + '.' + frmt)

            # what is the output format
            if frmt in 'csv':
                data = pd.DataFrame(r[1]) # using pandas to output csv
                print('writing file to:    %s' % of)
                data.to_csv(of) # write
            elif frmt in 'h5':
                '''
                Now we gather gps data.
                Full GPS data are in .DZG files of same name if they exist (see below).
                If .DZG does not exist, then locations are determined from correlating
                waypoint marks with scan numbers (end of .DZX files).
                In this case we must have some way of relating location to mark or
                directly to scan number so best option may be .csv with:
                mark name, lat, lon
                CSV file is then read to np array and matched with mark nums in .DZX
                and number of scans between marks calculated. Then we can
                interpolate lat and lon in np array for all scans between marks
                with gps. Problems will arise in cases where marks on GPS and SIR
                do not total the same number, so care must be taken to cull or add
                points where necessary.
                Assumptions:
                - constant velocity between marks (may be possible to add a check)
                - marks are made at same time on GPS and SIR
                - gps and gpr are in same location when mark is made
                - good quality horizontal solution
                single-channel IceRadar h5 structure is
                /line_x/location_n/datacapture_0/echogram_0 (/group/group/group/dataset)
                each dataset has an 'attributes' item attached, formatted in 'collections.defaultdict' style:
                [('PCSavetimestamp', str), ('GPS Cluster- MetaData_xml', str), ('Digitizer-MetaData_xml', str), ('GPS Cluster_UTM-MetaData_xml', str)]
                '''

                # setup formattable strings
                svts = 'PCSavetimestamp'
                gpsx = 'GPS Cluster- MetaData_xml'
                # main gps string. 8 formattable values: gps_sec, lat, lon, qual, num_sats, hdop, altitude, geoid_ht
                gpsclstr = '<Cluster>\r\n<Name>GPS Cluster</Name>\r\n<NumElts>10</NumElts>\r\n<String>\r\n<Name>GPS_timestamp_UTC</Name>\r\n<Val>%.2f</Val>\r\n</String>\r\n<String>\r\n<Name>Lat_N</Name>\r\n<Val>%.4f</Val>\r\n</String>\r\n<String>\r\n<Name>Long_ W</Name>\r\n<Val>%.4f</Val>\r\n</String>\r\n<String>\r\n<Name>Fix_Quality</Name>\r\n<Val>%i</Val>\r\n</String>\r\n<String>\r\n<Name>Num _Sat</Name>\r\n<Val>%i</Val>\r\n</String>\r\n<String>\r\n<Name>Dilution</Name>\r\n<Val>%.2f</Val>\r\n</String>\r\n<String>\r\n<Name>Alt_asl_m</Name>\r\n<Val>%.2f</Val>\r\n</String>\r\n<String>\r\n<Name>Geoid_Heigh_m</Name>\r\n<Val>%.2f</Val>\r\n</String>\r\n<Boolean>\r\n<Name>GPS Fix valid</Name>\r\n<Val>1</Val>\r\n</Boolean>\r\n<Boolean>\r\n<Name>GPS Message ok</Name>\r\n<Val>1</Val>\r\n</Boolean>\r\n</Cluster>\r\n'
                dimx = 'Digitizer-MetaData_xml'
                # digitizer string. 3 formattable values: rhf_depth, rh_nsamp, stack
                dimxstr = '<Cluster>\r\n<Name>Digitizer MetaData</Name>\r\n<NumElts>3</NumElts>\r\n<Cluster>\r\n<Name>Digitizer settings</Name>\r\n<NumElts>5</NumElts>\r\n<Cluster>\r\n<Name>Vertical</Name>\r\n<NumElts>3</NumElts>\r\n<DBL>\r\n<Name>vertical range</Name>\r\n<Val>%f</Val>\r\n</DBL>\r\n<DBL>\r\n<Name>Vertical Offset</Name>\r\n<Val>0.00000000000000</Val>\r\n</DBL>\r\n<I32>\r\n<Name>vertical coupling</Name>\r\n<Val>1</Val>\r\n</I32>\r\n</Cluster>\r\n<Cluster>\r\n<Name>Channel</Name>\r\n<NumElts>1</NumElts>\r\n<DBL>\r\n<Name>maximum input frequency</Name>\r\n<Val>%f</Val>\r\n</DBL>\r\n</Cluster>\r\n<Cluster>\r\n<Name>Horizontal</Name>\r\n<NumElts>2</NumElts>\r\n<DBL>\r\n<Name> Sample Rate</Name>\r\n<Val>250000000.00000000000000</Val>\r\n</DBL>\r\n<I32>\r\n<Name>Record Length</Name>\r\n<Val>%i</Val>\r\n</I32>\r\n</Cluster>\r\n<Cluster>\r\n<Name>Trigger</Name>\r\n<NumElts>12</NumElts>\r\n<U16>\r\n<Name>trigger type</Name>\r\n<Val>0</Val>\r\n</U16>\r\n<DBL>\r\n<Name>trigger delay</Name>\r\n<Val>0.00000000000000</Val>\r\n</DBL>\r\n<DBL>\r\n<Name>reference position</Name>\r\n<Val>10.00000000000000</Val>\r\n</DBL>\r\n<DBL>\r\n<Name>trigger level</Name>\r\n<Val>2.00000000000000E-2</Val>\r\n</DBL>\r\n<DBL>\r\n<Name>hysteresis</Name>\r\n<Val>0.00000000000000</Val>\r\n</DBL>\r\n<DBL>\r\n<Name>low level</Name>\r\n<Val>0.00000000000000</Val>\r\n</DBL>\r\n<DBL>\r\n<Name>high level</Name>\r\n<Val>0.00000000000000</Val>\r\n</DBL>\r\n<U16>\r\n<Name>trigger coupling</Name>\r\n<Val>1</Val>\r\n</U16>\r\n<I32>\r\n<Name>trigger window mode</Name>\r\n<Val>0</Val>\r\n</I32>\r\n<I32>\r\n<Name>trigger slope</Name>\r\n<Val>0</Val>\r\n</I32>\r\n<String>\r\n<Name>trigger source</Name>\r\n<Val>0</Val>\r\n</String>\r\n<I32>\r\n<Name>Trigger Modifier</Name>\r\n<Val>2</Val>\r\n</I32>\r\n</Cluster>\r\n<String>\r\n<Name>channel name</Name>\r\n<Val>0</Val>\r\n</String>\r\n</Cluster>\r\n<U16>\r\n<Name>Stacking</Name>\r\n<Val>%i</Val>\r\n</U16>\r\n<Cluster>\r\n<Name>Radargram extra info</Name>\r\n<NumElts>2</NumElts>\r\n<DBL>\r\n<Name>relativeInitialX</Name>\r\n<Val>-1.51999998365682E-7</Val>\r\n</DBL>\r\n<DBL>\r\n<Name>xIncrement</Name>\r\n<Val>3.99999988687227E-9</Val>\r\n</DBL>\r\n</Cluster>\r\n</Cluster>\r\n'
                gutx = 'GPS Cluster_UTM-MetaData_xml'
                # gps UTM string. 1 formattable value: num_sats
                gpsutmstr = '<Cluster>\r\n<Name>GPS_UTM Cluster</Name>\r\n<NumElts>10</NumElts>\r\n<String>\r\n<Name>Datum</Name>\r\n<Val>NaN</Val>\r\n</String>\r\n<String>\r\n<Name>Easting_m</Name>\r\n<Val></Val>\r\n</String>\r\n<String>\r\n<Name>Northing_m</Name>\r\n<Val>NaN</Val>\r\n</String>\r\n<String>\r\n<Name>Elevation</Name>\r\n<Val>NaN</Val>\r\n</String>\r\n<String>\r\n<Name>Zone</Name>\r\n<Val>NaN</Val>\r\n</String>\r\n<String>\r\n<Name>Satellites (dup)</Name>\r\n<Val>%i</Val>\r\n</String>\r\n<Boolean>\r\n<Name>GPS Fix Valid (dup)</Name>\r\n<Val>1</Val>\r\n</Boolean>\r\n<Boolean>\r\n<Name>GPS Message ok (dup)</Name>\r\n<Val>1</Val>\r\n</Boolean>\r\n<Boolean>\r\n<Name>Flag_1</Name>\r\n<Val>0</Val>\r\n</Boolean>\r\n<Boolean>\r\n<Name>Flag_2</Name>\r\n<Val>0</Val>\r\n</Boolean>\r\n</Cluster>\r\n'

                if os.path.exists(fnoext + '.DZG'):
                    gps = readdzg(fnoext + '.DZG', 'dzg', rhf_sps, r[1].shape[1], verbose)
                else:
                    gps = '' # fix

                # make data structure
                n = 0 # line number, iteratively increased
                f = h5py.File(of, 'w') # overwrite existing file
                print('exporting to %s' % of)

                try:
                    li = f.create_group('line_0') # create line zero
                except ValueError: # the line already exists in the file
                    li = f['line_0']
                for sample in r[1].T:
                    # create strings

                    # pcsavetimestamp
                    # formatting: m/d/yyyy_h:m:ss PM
                    svts_str = gps[n]['timestamp'].astype(datetime).strftime('%m/%d/%Y_%H:%M:%S %p')

                    # gpscluster
                    # order we need: (len(list), tracetime, y, x, q, sats, dil, z, gh, 1, 1)
                    # rows in gps: tracenum, lat, lon, altitude, geoid_ht, qual, num_sats, hdop, timestamp
                    gpsx_str = gpsclstr % (gps[n]['gps_sec'], gps[n]['lat'], gps[n]['lon'], gps[n]['qual'], gps[n]['num_sats'], gps[n]['hdop'], gps[n]['altitude'], gps[n]['geoid_ht'])

                    # digitizer
                    dimx_str = dimxstr % (r[0]['rhf_depth'], freq, r[0]['rh_nsamp'], r[0]['stack'])

                    # utm gpscluster
                    gutx_str = gpsutmstr % (gps[n]['num_sats'])

                    lo = li.create_group('location_' + str(n)) # create a location for each trace
                    dc = lo.create_group('datacapture_0')
                    eg = dc.create_dataset('echogram_0', (r[1].shape[0],), data=sample)
                    eg.attrs.create(svts, svts_str) # store pcsavetimestamp attribute
                    eg.attrs.create(gpsx, gpsx_str) # store gpscluster attribute
                    eg.attrs.create(dimx, dimx_str) # store digitizer attribute
                    eg.attrs.create(gutx, gutx_str) # store utm gpscluster attribute
                    n += 1
                f.close()
            elif frmt in 'segy':
                '''
                segy output is not yet available
                '''
                print('SEG-Y is not yet supported, please choose another format.')
                print(help_text)
                sys.exit(2)
            print('done exporting.')
        if plot:
            '''
            let's do some matplotlib
            '''
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
            del new_arr

            fi = 0
            for ar in img_arr:
                j = stack
                if outfile:
                    outname = os.path.split(outfile)[-1].split('.')[:-1][0]
                else:
                    outname = os.path.split(infile)[-1].split('.')[:-1][0]

                if str(j).lower() in 'auto':
                    print('attempting automatic stacking method...')
                    ratio = (img_arr[ar].shape[1]/img_arr[ar].shape[0])/(7500/3000)
                    if ratio > 1:
                        j = int(ratio)
                    else:
                        j = 1
                else:
                    try:
                        j = int(j)
                    except ValueError:
                        print('error: stacking must be indicated with an integer greater than 1, "auto", or None.')
                        print('a stacking value of 1 equates to None. "auto" will attempt to stack to about a 2.5:1 x to y axis ratio.')
                        print('the result will not be stacked.')
                        j = 1
                if j > 1:
                    print('stacking %sx' % j)
                    i = list(range(j))
                    l = list(range(int(img_arr[ar].shape[1]/j)))
                    stack = np.copy(img_arr[ar][:,::j])
                    for s in l:
                        stack[:,s] = stack[:,s] + img_arr[ar][:,s*j+1:s*j+j].sum(axis=1)
                    img_arr[ar] = stack
                    del stack
                else:
                    if str(j).lower() in 'auto':
                        pass
                    else:
                        print('no stacking applied. be warned: this can result in very large and awkwardly-shaped figures.')

                mean = np.mean(img_arr[ar])
                
                if specgram:
                    tr = int(img_arr[ar].shape[1] / 2)
                    print('making spectrogram of trace %s' % (tr))
                    fq = 1 / (r[0]['rhf_depth'] / r[0]['cr'] / r[0]['rh_nsamp'])
                    trace = img_arr[ar].T[tr]
                    spectrogram(trace, fq, wlen=fq/1000, per_lap = 0.99, dbscale=True,
                        title='Trace %s Spectrogram - Antenna Frequency: %.2E Hz - Sampling Frequency: %.2E Hz' % (tr, r[0]['rh_antname'][fi], fq))
                
                if bgr:
                    # Average Background Removal
                    print('removing horizontal background...')
                    i = 0
                    for row in img_arr[ar]:          # each row
                        mean = np.mean(row)
                        img_arr[ar][i] = row - mean
                        i += 1
                
                if dewow:
                    # Dewow filter
                    print('dewowing data...')
                    signal = list(zip(*img_arr[ar]))[10]
                    model = np.polyfit(range(len(signal)), signal, 3)
                    predicted = list(np.polyval(model, range(len(signal))))
                    i = 0
                    for column in img_arr[ar].T:      # each column
                        img_arr[ar].T[i] = column + predicted
                        i += 1

                if freqmin and freqmax:
                    # Vertical FIR filter
                    print('vertical FIR filtering...')
                    fq = 1 / (r[0]['rhf_depth'] / r[0]['cr'] / r[0]['rh_nsamp'])
                    freqmin = freqmin * 10 ** 6
                    freqmax = freqmax * 10 ** 6
                    
                    print('Sampling frequency:       %.2E Hz' % fq)
                    print('Minimum filter frequency: %.2E Hz' % freqmin)
                    print('Maximum filter frequency: %.2E Hz' % freqmax)
                    
                    i = 0
                    for t in img_arr[ar].T:
                        f = bandpass(data=t, freqmin=freqmin, freqmax=freqmax, df=fq, corners=2, zerophase=False)
                        img_arr[ar][:,i] = f
                        i += 1

                std = np.std(img_arr[ar])
                print('std:  %s' % std)
                ll = -std * 3 # lower color limit (1/10 of a standard deviation works well for 100MHz in a lake)
                ul = std * 3 # upper color limit (1/10 of a standard deviation works well for 100MHz in a lake)
                print('lower color limit: %s' % ll)
                print('upper color limit: %s' % ul)

                # having lots of trouble with this line not being friendly with figsize tuple (integer coercion-related errors)
                # so we will force everything to be integers explicitly

                if figsize != 'auto':
                    figx, figy = int(int(figsize)*int(int(img_arr[ar].shape[1])/int(img_arr[ar].shape[0]))), int(figsize) # force to integer instead of coerce
                    print('plotting %sx%sin image with gain=%s...' % (figx, figy, gain))
                    fig = plt.figure(figsize=(figx, figy-1), dpi=150)
                else:
                    print('plotting with gain=%s...' % gain)
                    fig = plt.figure()
                
                try:
                    img = plt.imshow(img_arr[ar], cmap=colormap, clim=(ll, ul),
                                 norm=colors.SymLogNorm(linthresh=float(std)/float(gain), linscale=1,
                                                        vmin=ll, vmax=ul),)
                except:
                    print('matplotlib did not accept colormap "%s", using viridis instead' % colormap)
                    print('see examples here: https://matplotlib.org/users/colormaps.html#grayscale-conversion')
                    img = plt.imshow(img_arr[ar], cmap='viridis', clim=(ll, ul),
                                 norm=colors.SymLogNorm(linthresh=float(std)/float(gain), linscale=1,
                                                        vmin=ll, vmax=ul),)

                if colorbar:
                    fig.colorbar(img)
                plt.title('%s - %s MHz - stacking: %s - gain: %s' % (os.path.split(infile)[-1], ANT[r[0]['rh_antname']][fi], j, gain))
                plt.tight_layout(pad=figsize/2.)
                if outfile:
                    if len(img_arr) > 1:
                        print('saving figure as %s_%sMHz.png' % (os.path.splitext(outfile)[0], ANT[r[0]['rh_antname']][fi]))
                        plt.savefig(os.path.join(os.path.splitext(outfile)[0] + '_' + str(ANT[r[0]['rh_antname']][fi]) + 'MHz.png'))
                    else:
                        print('saving figure as %s.png' % (os.path.splitext(outfile)[0]))
                        plt.savefig(os.path.join(os.path.splitext(outfile)[0] + '.png'))
                else:
                    print('saving figure as %s_%sMHz.png' % (os.path.splitext(infile)[0], ANT[r[0]['rh_antname']][fi]))
                    plt.savefig(os.path.join(os.path.splitext(infile)[0] + '_' + str(ANT[r[0]['rh_antname']][fi]) + 'MHz.png'))
                if noshow:
                    print('not showing matplotlib')
                    plt.close()
                else:
                    print('showing matplotlib figure...')
                    plt.show()
                
                if histogram:
                    print('drawing histogram...')
                    fig = plt.figure()
                    hst = plt.hist(img_arr[ar].ravel(), bins=256, range=(ll, ul), fc='k', ec='k')
                    plt.show()
                fi += 1

    except TypeError as e: # shows up when the user selects an input file that doesn't exist
        print(e)
        sys.exit(2)
    
def main():
    '''
    gathers and parses arguments to create function calls
    '''
    print(NAME + ' ' + VERSION)

    verbose = False
    stack = 1
    infile, outfile, antfreq, frmt, plot, figsize, histogram, colorbar, dewow, bgr, noshow = None, None, None, None, None, None, None, None, None, None, None
    freqmin, freqmax, specgram, zero = None, None, None, None
    colormap = 'Greys'
    gain = 1

# some of this needs to be tweaked to formulate a command call to one of the main body functions
# variables that can be passed to a body function: (infile, outfile, antfreq=None, frmt, plot=False, stack=1)
    try:
        opts, args = getopt.getopt(sys.argv[1:],'hvdi:a:o:f:p:s:rwnmc:bg:z:t:',
            ['help','verbose','dmi','input=','antfreq=','output=','format=','plot=','stack=','bgr',
            'dewow','noshow','histogram','colormap=','colorbar','gain=','zero=','bandpass='])
    # the 'no option supplied' error
    except getopt.GetoptError as e:
        print('error: invalid argument(s) supplied')
        print('error text: %s' % e)
        print(HELP_TEXT)
        sys.exit(2)
    for opt, arg in opts: 
        if opt in ('-h', '--help'): # the help case
            print(u'Copyleft %s %s %s' % (u'\U0001F12F', AUTHOR, YEAR))
            print(AFFIL + '\n')
            print(HELP_TEXT)
            sys.exit()
        if opt in ('-v', '--verbose'):
            verbose = True
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
            except:
                print('error: %s is not a valid decimal or integer frequency value.' % arg)
                print(HELP_TEXT)
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
                    plot = True
                else:
                    # else the user has given an invalid format
                    print(HELP_TEXT)
                    sys.exit(2)
            else:
                print(HELP_TEXT)
                sys.exit(2)
        if opt in ('-s', '--stack'):
            if arg:
                if 'auto' in str(arg).lower():
                    stack = 'auto'
                else:
                    try:
                        stack = abs(int(arg))
                    except ValueError:
                        print('error: stacking argument must be a positive integer or "auto".')
                        print(HELP_TEXT)
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
                    print('error: zero correction must be an integer')
            else:
                print('warning: no zero correction argument supplied')
                zero = None
        if opt in ('-t', '--bandpass'):
            if arg:
                freqmin, freqmax = arg.split('-')
                try:
                    freqmin = int(freqmin)
                    freqmax = int(freqmax)
                except:
                    print('error: filter frequency must be integers separated by a dash (-)')
                    freqmin, freqmax = None, None
            else:
                print('warning: no filter frequency argument supplied')
        if opt in ('-n', '--noshow'):
            noshow = True
        if opt in ('-p', '--plot'):
            plot = True
            if arg:
                if 'auto' in arg.lower():
                    figsize = str(arg).lower()
                else:
                    try:
                        figsize = abs(int(arg))
                    except ValueError:
                        print('error: plot size argument must be a positive integer or "auto".')
                        print(HELP_TEXT)
                        sys.exit(2)
        if opt in ('-d', '--dmi'):
            #dmi = True
            print('DMI devices are not supported at the moment.')
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
                    print('gain must be positive. defaulting to gain=1.')
                    gain = 1


    # call the function with the values we just got
    if infile:
        if outfile:
            pass
        else:
            verbose = True
        readgssi(infile=infile, outfile=outfile, antfreq=antfreq, frmt=frmt, plot=plot,
                 figsize=figsize, stack=stack, verbose=verbose, histogram=histogram,
                 colormap=colormap, colorbar=colorbar, gain=gain, bgr=bgr, zero=zero,
                 dewow=dewow, noshow=noshow, freqmin=freqmin, freqmax=freqmax)
    else:
        print(HELP_TEXT)

if __name__ == "__main__":
    '''
    this is the command line call use case. can't directly put code of main here.
    '''
    main()

elif __name__ == '__version__':
    print(VERSION)

else:
    '''
    this is the module/import use case
    '''
    pass
