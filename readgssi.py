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
import matplotlib.image as mpi
import matplotlib.pyplot as plt
#import pandas as pd
import math
from datetime import datetime
import pytz
import h5py
import pynmea2

NAME = 'readgssi'
VERSION = '0.0.3-dev'
AUTHOR = 'Ian Nesbitt'
AFFIL = 'School of Earth and Climate Sciences, University of Maine'

MINHEADSIZE = 1024 # absolute minimum total header size
PAREASIZE = 128 # fixed info header size

TZ = pytz.timezone('UTC')

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

ANT = {
    '3200': None,
    '3207': 100,
    '5106': 200,
    '50300': 300,
    '350': 350,
    '50270': 270,
    '50400': 400,
    '800': 800,
    '3101': 900,
    '51600': 1600,
    '62000': 2000,
    '62300': 2300,
    '52600': 2600,
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
    this is a colossally stupid way of storing dates.
    I have no idea if I'm unpacking them correctly, and every indication that I'm not
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

def readdzg(fi, frmt, spu, traces):
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
    tracenum = 0 # the increase in trace number
    rownp = 0 # row number iterated through (numpy array)
    rowrmc = 0 # row number iterated through (gps file)
    rowgga = 0
    timestamp = False
    prevtime = False
    td = False
    prevtrace = False
    rmc = False
    antname = False
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
                print('rmc records: ' + rowrmc)
                print('gga records: ' + rowgga)
            gpssps = 1 / td.total_seconds() # GPS samples per second
            print('found ' + str(rowrmc) + ' GPS epochs at rate of ' + str(gpssps) + 'Hz')
            shift = (rowrmc/gpssps - traces/spu) / 2 # number of GPS samples to cut from each end of file
            print('cutting ' + str(shift) + ' records from the beginning and end of the file')
            dt = [('tracenum', 'float32'), ('lat', 'float32'), ('lon', 'float32'), ('altitude', 'float32'), ('geoid_ht', 'float32'), ('qual', 'uint8'), ('num_sats', 'uint8'), ('hdop', 'float32'), ('timestamp', 'datetime64[us]')] # array columns
            arr = np.zeros(traces+100, dt) # numpy array with num rows = num gpr traces, and columns defined above
            print('creating array of ' + str(traces) + ' interpolated locations...')
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
                    msg = pynmea2.parse(ln.rstrip())
                    x1, y1, z1, gh, q, sats, dil = float(msg.lon), float(msg.lat), float(msg.altitude), float(msg.geo_sep), int(msg.gps_qual), int(msg.num_sats), float(msg.horizontal_dil)
                    if msg.lon_dir in 'W':
                        x1 = -x1
                    if msg.lat_dir in 'S':
                        y1 = -y1
                    if prevtime: # if this is our second or more GPS epoch, calculate delta trace and current trace
                        elapsedelta = timestamp - prevtime # t1 - t0 in timedelta format
                        elapsed = float((elapsedelta).total_seconds()) # seconds elapsed
                        if elapsed > 3600.0:
                            print("WARNING: Time jumps by more than an hour in this GPS dataset and there are no RMC sentences to anchor the datestamp!")
                            print("This dataset may cross over the UTC midnight dateline!\nprevious timestamp: " + prevtime + "\ncurrent timestamp:  " + timestamp)
                            print("trace number:       " + trace)
                        tracenum = round(elapsed * spu, 5) # calculate the increase in trace number, rounded to 5 decimals to eliminate machine error
                        trace += tracenum # increment to reflect current trace
                        resamp = numpy.arange(math.ceil(prevtrace), math.ceil(trace), 1) # make an array of integer values between t0 and t1
                        for t in resamp:
                            x = (x1 - x0) / (elapsed) * (t - prevtrace) + x0 # interpolate latitude
                            y = (y1 - y0) / (elapsed) * (t - prevtrace) + y0 # interpolate longitude
                            z = (z1 - z0) / (elapsed) * (t - prevtrace) + z0 # interpolate altitude
                            tracetime = prevtime + timedelta(seconds=elapsedelta.total_seconds() * (t - prevtrace))
                            tup = (t, x, y, z, gh, q, sats, dil, sec, tracetime)
                            arr[rownp] = tup
                            rownp += 1
                    else: # we're on the very first row
                        pass # we don't do anything here :)
                    x0, y0, z0 = x1, y1, z1 # set xyz0 for next loop
                    prevtime = timestamp # set t0 for next loop
                    prevtrace = trace
            print('processed ' + str(rownp) + ' rows')
            # if there's no need to use pandas, we shouldn't (library load speed mostly, also this line is old):
            #array = pd.DataFrame({ 'ts' : arr['ts'], 'lat' : arr['lat'], 'lon' : arr['lon'] }, index=arr['tracenum'])
        elif frmt == 'csv':
            arr = ''
    return arr


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
    plot = False
    dmi = False
    antfreq = False
    rh_antname = ''
    help_text = 'usage:\nreadgssi.py -i <input file> -a <antenna frequency> -o <output file> -f <format: (csv|h5|segy)>\n'#optional flag: -d, denoting radar pulses triggered with a distance-measuring instrument (DMI) like a survey wheel' # help text string

    # parse passed command line arguments. this may get moved somewhere else, but for now:
    try:
        opts, args = getopt.getopt(argv,'hpdi:a:o:f:',['help','plot','dmi','input=','antfreq=','output=','format='])
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
        if opt in ('-a', '--freq'):
            try:
                antfreq = round(float(arg),1)
            except:
                print('%s is not a valid decimal or integer frequency value.' % arg)
                print(help_text)
                sys.exit(2)
        if opt in ('-f', '--format'): # the format string
            # check whether the string is a supported format
            if arg:
                if arg in ('csv', 'CSV'):
                    frmt = 'csv'
                elif arg in ('sgy', 'segy', 'seg-y', 'SGY', 'SEGY', 'SEG-Y'):
                    frmt = 'segy'
                elif arg in ('h5', 'hdf5', 'H5', 'HDF5'):
                    frmt = 'h5'
                elif arg in ('plot'):
                    plot = True
                else:
                    # else the user has given an invalid format
                    print(help_text)
                    sys.exit(2)
            else:
                print(help_text)
                sys.exit(2)
        if opt in ('-p', '--plot'):
            plot = True
        if opt in ('-d', '--dmi'):
            #dmi = True
            pass # not doing anything with this at the moment

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
                f.seek(32) # ensure correct read position for rfdatebyte
                rhb_cdt = readtime(f.read(4)) # creation date and time in bits, structured as little endian u5u6u5u5u4u7
                f.seek(36)
                rhb_mdt = readtime(f.read(4)) # modification date and time in bits, structured as little endian u5u6u5u5u4u7
                f.seek(44) # skip across some proprietary BS
                rh_text = struct.unpack('<h', f.read(2))[0] # offset to text
                rh_ntext = struct.unpack('<h', f.read(2))[0] # size of text
                rh_proc = struct.unpack('<h', f.read(2))[0] # offset to processing history
                rh_nproc = struct.unpack('<h', f.read(2))[0] # size of processing history
                rh_nchan = struct.unpack('<h', f.read(2))[0] # number of channels
                rhf_epsr = struct.unpack('<f', f.read(4))[0] # average dilectric
                rhf_top = struct.unpack('<f', f.read(4))[0] # position in meters (useless?)
                rhf_depth = struct.unpack('<f', f.read(4))[0] # range in meters
                #rhf_coordx = struct.unpack('<ff', f.read(8))[0] # this is definitely useless
                f.seek(98) # start of antenna bit
                rh_ant = struct.unpack('<14c', f.read(14))
                i = 0
                while i < 14:
                    if rh_ant[i] != '\x00':
                        rh_antname += rh_ant[i]
                    i += 1
                f.seek(113) # skip to something that matters
                vsbyte = f.read(1) # byte containing versioning bits
                rh_version = readbit(vsbyte, 0, 2) # whether or not the system is GPS-capable, 1=no 2=yes (does not mean GPS is in file)
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

                # create return dictionary
                returns = {
                    'infile': infile,
                    'outfile': outfile,
                    'frmt': frmt,
                    'plot': plot,
                    'antfreq': antfreq,
                    'rh_antname': rh_antname.rsplit('x')[0],
                    'rh_system': rh_system,
                    'rh_version': rh_version,
                    'rh_nchan': rh_nchan,
                    'rh_nsamp': rh_nsamp,
                    'rh_bits': rh_bits,
                    'rhf_sps': rhf_sps,
                    'rhf_spm': rhf_spm,
                    'rhf_epsr': rhf_epsr,
                    'rhb_cdt': rhb_cdt,
                    'rhb_mdt': rhb_mdt,
                    'rhf_depth': rhf_depth,
                }

                return returns, data
        except IOError as e: # the user has selected an inaccessible or nonexistent file
            print("i/o error: DZT file is inaccessable or does not exist")
            print('detail: ' + str(e) + '\n')
            print(help_text)
        

if __name__ == "__main__":
    '''
    this is the direct command line call use case
    '''
    print(NAME + ' ' + VERSION)
    try:
        r = readgssi(argv=sys.argv[1:])
        rhf_sps = r[0]['rhf_sps']
        rhf_spm = r[0]['rhf_spm']
        line_dur = r[1].shape[1]/rhf_sps
        # print some useful things to command line users from returned dictionary
        print('input file:         %s' % r[0]['infile'])
        print('system:             %s' % UNIT[r[0]['rh_system']])
        print('antenna:            %s' % r[0]['rh_antname'])
        if antfreq:
            print('user ant frequency: %.1f' % r[0]['antfreq'])
        elif r[0]['rh_antname']:
            try:
                print('antenna frequency:  %.1f' % ANT[r[0]['rh_antname']])
            except ValueError as e:
                print('WARNING: could not read frequency for given antenna name.\nerror info: %s' % e)
                print(help_text)
                sys.exit(2)
        else:
            print('no frequency information could be read from the header. please specify the frequency of the antenna using the -a flag')
            print(help_text)
            sys.exit(2)
        print('date created:       %s' % r[0]['rhb_cdt'])
        print('date modified:      %s' % r[0]['rhb_mdt'])
        print('gps-enabled file:   %s' % GPS[r[0]['rh_version']])
        print('number of channels: %i' % r[0]['rh_nchan'])
        print('samples per trace:  %i' % r[0]['rh_nsamp'])
        print('bits per sample:    %s' % BPS[r[0]['rh_bits']])
        print('traces per second:  %.1f' % rhf_sps)
        print('traces per meter:   %.1f' % rhf_spm)
        print('dilectric:          %.1f' % r[0]['rhf_epsr'])
        print('sampling depth:     %.1f' % r[0]['rhf_depth'])
        if r[1].shape[1] == int(r[1].shape[1]):
            print('traces:             %i' % r[1].shape[1])
        else:
            print('traces:             %f' % r[1].shape[1])
        if rhf_spm == 0:
            print('seconds:            %.8f' % line_dur)
        else:
            print('meters:             %.2f' % r[1].shape[1]/rhf_spm)
        if r[0]['frmt']:
            print('outputting to ' + r[0]['frmt'] + " . . .")

            fnoext = os.path.splitext(r[0]['infile'])[0]
            # is there an output filepath given?
            if r[0]['outfile']: # if output is given
                of = os.path.abspath(r[0]['outfile']) # set output to given location
            else: # if no output is given
                # set output to the same dir as input file
                of = os.path.abspath(fnoext + '.' + r[0]['frmt'])

            # what is the output format
            if r[0]['frmt'] in 'csv':
                import pandas as pd
                data = pd.DataFrame(r[1]) # using pandas to output csv
                print('writing file to:    %s' % of)
                data.to_csv(of) # write
                del data
            elif r[0]['frmt'] in 'h5':
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
                '''
                if os.path.exists(fnoext + '.DZG'):
                    gps = readdzg(fnoext + '.DZG', 'dzg', rhf_sps, r[1].shape[1])
                else:
                    gps = '' # fix

                # make data structure
                n = 0 # line number, iteratively increased
                f = h5py.File(of, 'a') # open or create a file

                '''
                single-channel IceRadar h5 structure is
                /line_x/location_n/datacapture_0/echogram_0 (/group/group/group/dataset)
                each dataset has an 'attributes' item attached, formatted in 'collections.defaultdict' style:
                [('PCSavetimestamp', str), ('GPS Cluster- MetaData_xml', str), ('Digitizer-MetaData_xml', str), ('GPS Cluster_UTM-MetaData_xml', str)]
                '''

                svts = 'PCSavetimestamp'
                gpsx = 'GPS Cluster- MetaData_xml'
                gpsclstr = '<Cluster>\r\n<Name>GPS Cluster</Name>\r\n<NumElts>%i</NumElts>\r\n<String>\r\n<Name>GPS_timestamp_UTC</Name>\r\n<Val>%.2f</Val>\r\n</String>\r\n<String>\r\n<Name>Lat_N</Name>\r\n<Val>%.4f</Val>\r\n</String>\r\n<String>\r\n<Name>Long_ W</Name>\r\n<Val>%.4f</Val>\r\n</String>\r\n<String>\r\n<Name>Fix_Quality</Name>\r\n<Val>%i</Val>\r\n</String>\r\n<String>\r\n<Name>Num _Sat</Name>\r\n<Val>%i</Val>\r\n</String>\r\n<String>\r\n<Name>Dilution</Name>\r\n<Val>%.2f</Val>\r\n</String>\r\n<String>\r\n<Name>Alt_asl_m</Name>\r\n<Val>%.2f</Val>\r\n</String>\r\n<String>\r\n<Name>Geoid_Heigh_m</Name>\r\n<Val>%.2f</Val>\r\n</String>\r\n<Boolean>\r\n<Name>GPS Fix valid</Name>\r\n<Val>%i</Val>\r\n</Boolean>\r\n<Boolean>\r\n<Name>GPS Message ok</Name>\r\n<Val>%i</Val>\r\n</Boolean>\r\n</Cluster>\r\n'
                dimx = 'Digitizer-MetaData_xml'
                dimxstr = ''
                gutx = 'GPS Cluster_UTM-MetaData_xml'
                gpsutmstr = '<Cluster>\r\n<Name>GPS_UTM Cluster</Name>\r\n<NumElts>10</NumElts>\r\n<String>\r\n<Name>Datum</Name>\r\n<Val>NaN</Val>\r\n</String>\r\n<String>\r\n<Name>Easting_m</Name>\r\n<Val></Val>\r\n</String>\r\n<String>\r\n<Name>Northing_m</Name>\r\n<Val>NaN</Val>\r\n</String>\r\n<String>\r\n<Name>Elevation</Name>\r\n<Val>NaN</Val>\r\n</String>\r\n<String>\r\n<Name>Zone</Name>\r\n<Val>NaN</Val>\r\n</String>\r\n<String>\r\n<Name>Satellites (dup)</Name>\r\n<Val>%i</Val>\r\n</String>\r\n<Boolean>\r\n<Name>GPS Fix Valid (dup)</Name>\r\n<Val>1</Val>\r\n</Boolean>\r\n<Boolean>\r\n<Name>GPS Message ok (dup)</Name>\r\n<Val>1</Val>\r\n</Boolean>\r\n<Boolean>\r\n<Name>Flag_1</Name>\r\n<Val>0</Val>\r\n</Boolean>\r\n<Boolean>\r\n<Name>Flag_2</Name>\r\n<Val>0</Val>\r\n</Boolean>\r\n</Cluster>\r\n'

                li = f.create_group('line_0') # create line zero
                for column in r[1].T:
                    # create strings

                    # pcsavetimestamp
                    # formatting: m/d/yyyy_h:m:ss PM
                    svts_str = gps[n]['timestamp'].strftime('%m/%d/%Y_%H:%M:%S %p')

                    # gpscluster
                    # order we need: (len(list), tracetime, y, x, q, sats, dil, z, gh, 1, 1)
                    # rows in gps: tracenum, lat, lon, altitude, geoid_ht, qual, num_sats, hdop, timestamp
                    gpsx_str = gpsclstr % (10, gps[n]['gps_sec'], gps[n]['lat'], gps[n]['lon'], gps[n]['qual'], gps[n]['num_sats'], gps[n]['hdop'], gps[n]['altitude'], gps[n]['geoid_ht'], 1, 1)

                    # digitizer
                    dimx_str = dimxstr

                	# utm gpscluster
                    gutx_str = gpsutmstr % gps[n]['num_sats']

                    lo = li.create_group('location_' + str(n)) # create a location for each trace
                    dc = lo.create_group('datacapture_0')
                    eg = dc.create_dataset('echogram_0', (r[1].shape[0],), data=column)
                    eg.attrs.create(svts, svts_str) # store pcsavetimestamp attribute
                    eg.attrs.create(gpsx, gpsx_str) # store gpscluster attribute
                    eg.attrs.create(dimx, dimx_str) # store digitizer attribute
                    eg.attrs.create(gutx, gutx_str) # store utm gpscluster attribute
                    n += 1
                f.close()
            elif r[0]['frmt'] in 'segy':
            	'''
            	segy output is not yet available
            	'''
                print('SEG-Y is not yet supported, please choose another format.')
            print('done exporting.')
        if r[0]['plot']:
            '''
            let's do some matplotlib....later
            '''
            #print('plotting...')
            #img = mpi.imread(r[1].astype(np.float32))
            #imgplot = plt.imshow(img)
            print('plotting is not yet supported, please choose another format.')

    except TypeError as e: # shows up when the user selects an input file that doesn't exist
        print(e)
        sys.exit(2)

else:
    '''
    this is the module/import use case
    '''
    pass
