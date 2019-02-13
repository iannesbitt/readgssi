from datetime import datetime, timedelta
import pynmea2
import math
import numpy as np
import pandas as pd
from geopy.distance import geodesic
import readgssi.functions as fx
from readgssi.constants import TZ
from math import sin, cos, sqrt, atan2, radians

'''
contains functions for reading gps data from various formats
'''

def readdzg(fi, frmt, header, verbose=False):
    '''
    a parser to extract gps data from DZG file format
    DZG contains raw NMEA sentences, which should include RMC and GGA
    fi = file containing gps information
    frmt = format ('dzg' = DZG file containing gps sentence strings (see below); 'csv' = comma separated file with: lat,lon,elev,time)
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
    traces = header['traces']
    if header['rhf_spm'] == 0:
        spu = header['rhf_sps']
    else:
        spu = header['rhf_spm']
    array = pd.DataFrame(columns=['datetimeutc', 'trace', 'longitude', 'latitude', # our dataframe
                                  'altitude', 'velocity', 'sec_elapsed', 'meters'])

    trace = 0 # the elapsed number of traces iterated through
    tracenum = 0 # the sequential increase in trace number
    rownp = 0 # array row number
    rowrmc = 0 # rmc record iterated through (gps file)
    rowgga = 0 # gga record
    sec_elapsed = 0 # number of seconds since the start of the line
    m = 0 # meters traveled over entire line
    m0, m1 = 0, 0 # meters traveled as of last, current loop
    u = 0 # velocity
    u0 = 0 # velocity on last loop
    timestamp = False
    prevtime = False
    init_time = False
    td = False
    prevtrace = False
    rmc = False
    lathem = 'north'
    lonhem = 'east'
    x0, x1, y0, y1, z0, z1 = False, False, False, False, False, False # coordinates
    x2, y2, z2, sec2 = 0, 0, 0, 0
    with open(fi, 'r') as gf:
        if verbose:
            fx.printmsg('using gps file:     %s' % (fi))
        if frmt == 'dzg': # if we're working with DZG format
            for ln in gf: # loop through the first few sentences, check for RMC
                if ln.startswith('$GPRMC'): # check to see if RMC sentence (should occur before GGA)
                    rmc = True
                    rowrmc += 1
                if ln.startswith('$GPGGA'):
                    if rowgga == 0:
                        msg = pynmea2.parse(ln.rstrip()) # convert gps sentence to pynmea2 named tuple
                        ts0 = TZ.localize(datetime.combine(datetime(1980, 1, 1), msg.timestamp)) # row 0's timestamp (not ideal)
                    if rowgga == 1:
                        msg = pynmea2.parse(ln.rstrip())
                        ts1 = TZ.localize(datetime.combine(datetime(1980, 1, 1), msg.timestamp)) # row 1's timestamp (not ideal)
                        td = ts1 - ts0 # timedelta = datetime1 - datetime0
                    rowgga += 1
            gpssps = 1 / td.total_seconds() # GPS samples per second
            if rowgga != rowrmc:
                fx.printmsg("WARNING: GGA and RMC sentences are not recorded at the same rate! This could cause unforseen problems!")
                fx.printmsg('    rmc: %i records' % rowrmc)
                fx.printmsg('    gga: %i records' % rowgga)
            if verbose:
                fx.printmsg('found %i GPS epochs at rate of ~%.1f Hz' % (rowrmc, gpssps))
            dt = [('tracenum', 'float32'), ('lon', 'float32'), ('lat', 'float32'), ('altitude', 'float32'), ('velocity', 'float32'), ('timestamp', 'datetime64[us]'), ('sec_elapsed', 'float32'), ('meters', 'float32')] # array columns
            arr = np.zeros((int(traces)+1000), dt) # numpy array with num rows = num gpr traces, and columns defined above
            if verbose:
                fx.printmsg('reading gps locations to array...')
            gf.seek(0) # back to beginning of file
            rowgga = 0
            for ln in gf: # loop over file line by line
                if ln.startswith('$GSSIS'):
                    trace = int(ln.split(',')[1])
                if rmc == True: # if there is RMC, we can use the full datestamp
                    if ln.startswith('$GPRMC'):
                        msg = pynmea2.parse(ln.rstrip())
                        timestamp = TZ.localize(datetime.combine(msg.datestamp, msg.timestamp)) # set t1 for this loop
                        u = msg.spd_over_grnd * 0.514444444 # convert from knots to m/s
                else: # if no RMC, we hope there is no UTC 00:00:00 in the file.........
                    fx.printmsg('WARNING: no RMC sentences found in GPS records. this could become an issue if your file goes through 00:00:00.')
                    fx.printmsg("         if you get a time jump error please open a github issue at https://github.com/iannesbitt/readgssi/issues")
                    fx.printmsg("         and attach the verbose output of this script plus a zip of the DZT and DZG files you're working with.")

                    if ln.startswith('$GPGGA'):
                        msg = pynmea2.parse(ln.rstrip())
                        timestamp = TZ.localize(msg.timestamp) # set t1 for this loop
                if ln.startswith('$GPGGA'):
                    sec1 = timestamp.timestamp()
                    msg = pynmea2.parse(ln.rstrip())
                    x1, y1, z1 = float(msg.longitude), float(msg.latitude), float(msg.altitude)
                    if msg.lon_dir in 'W':
                        lonhem = 'west'
                    if msg.lat_dir in 'S':
                        lathem = 'south'
                    if rowgga != 0:
                        m += geodesic((y1, x1, z1), (y0, x0, z0)).meters
                        if rmc == False:
                            u = float((m - m0) / (sec1 - sec0))
                        elapsedelta = timestamp - prevtime # t1 - t0 in timedelta format
                        elapsed = float((timestamp-init_time).total_seconds()) # seconds elapsed
                        if elapsed > 3600.0:
                            fx.printmsg("WARNING: Time jumps by more than an hour in this GPS dataset and there are no RMC sentences to anchor the datestamp!")
                            fx.printmsg("         This dataset may cross over the UTC midnight dateline!\nprevious timestamp: %s\ncurrent timestamp:  %s" % (prevtime, timestamp))
                            fx.printmsg("         trace number:       %s" % trace)
                    else:
                        u = 0
                        m = 0
                        elapsed = 0
                        if verbose:
                            fx.printmsg('record starts in %s and %s hemispheres' % (lonhem, lathem))
                    x0, y0, z0, sec0, m0 = x1, y1, z1, sec1, m # set xyzs0 for next loop
                    prevtime = timestamp # set t0 for next loop
                    if rowgga == 0:
                        init_time = timestamp
                    prevtrace = trace
                    array = array.append({'datetimeutc':timestamp.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                                          'trace':trace, 'longitude':x1, 'latitude':y1, 'altitude':z1,
                                          'velocity':u, 'sec_elapsed':elapsed, 'meters':m}, ignore_index=True)
                    rowgga += 1

            if verbose:
                fx.printmsg('processed %i gps epochs' % (rowgga))
        elif frmt == 'csv':
            with open(fi, 'r') as f:
                gps = np.fromfile(f)
    array['datetimeutc'] = pd.to_datetime(array['datetimeutc'], format='%Y-%m-%d %H:%M:%S.%f +0000', utc=True)
    array.set_index('datetimeutc', inplace=True)
    ## testing purposes
    # if True:
    #     if verbose:
    #         fx.printmsg('writing GPS to %s-gps.csv' % (fi))
    #     array.to_csv('%s-gps.csv' % (fi))
    return array
