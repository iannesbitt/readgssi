from datetime import datetime, timedelta
import pynmea2
import numpy as np
import readgssi.functions as fx

'''
contains functions for reading gps data from various formats
'''

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
                fx.printmsg("WARNING: GGA and RMC sentences are not recorded at the same rate! This could cause unforseen problems!")
                fx.printmsg('rmc records: %i' % rowrmc)
                fx.printmsg('gga records: %i' % rowgga)
            gpssps = 1 / td.total_seconds() # GPS samples per second
            if verbose:
                fx.printmsg('found %i GPS epochs at rate of %.1f Hz' % (rowrmc, gpssps))
            dt = [('tracenum', 'float32'), ('lat', 'float32'), ('lon', 'float32'), ('altitude', 'float32'), ('geoid_ht', 'float32'), ('qual', 'uint8'), ('num_sats', 'uint8'), ('hdop', 'float32'), ('gps_sec', 'float32'), ('timestamp', 'datetime64[us]')] # array columns
            arr = np.zeros((int(traces)+1000), dt) # numpy array with num rows = num gpr traces, and columns defined above
            if verbose:
                fx.printmsg('creating array of %i interpolated gps locations...' % (traces))
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
                            fx.printmsg("WARNING: Time jumps by more than an hour in this GPS dataset and there are no RMC sentences to anchor the datestamp!")
                            fx.printmsg("         This dataset may cross over the UTC midnight dateline!\nprevious timestamp: %s\ncurrent timestamp:  %s" % (prevtime, timestamp))
                            fx.printmsg("         trace number:       %s" % trace)
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
                            fx.printmsg('using %s and %s hemispheres' % (lonhem, lathem))
                    x0, y0, z0, sec0 = x1, y1, z1, sec1 # set xyzs0 for next loop
                    prevtime = timestamp # set t0 for next loop
                    prevtrace = trace
            if verbose:
                fx.printmsg('processed %i gps locations' % rownp)
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
                fx.printmsg('cut %i rows from beginning and %s from end of gps array, new size %s' % (shift, endshift, arr.shape[0]))
            # if there's no need to use pandas, we shouldn't (library load speed mostly, also this line is old):
            #array = pd.DataFrame({ 'ts' : arr['ts'], 'lat' : arr['lat'], 'lon' : arr['lon'] }, index=arr['tracenum'])
        elif frmt == 'csv':
            arr = ''
    return arr
