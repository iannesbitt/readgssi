import h5py
import pandas as pd
import numpy as np
import json
import struct
from readgssi.gps import readdzg
import readgssi.functions as fx
from datetime import datetime

"""
contains translations to common formats
"""

def json_header(header, outfile_abspath, verbose=False):
    """
    Save header values as a .json so another script can take what it needs. This is used to export to `GPRPy <https://github.com/NSGeophysics/gprpy>`_.

    :param dict header: The file header dictionary
    :param str outfile_abspath: Output file path
    :param bool verbose: Verbose, defaults to False
    """
    with open('%s.json' % (outfile_abspath), 'w') as f:
        if verbose:
            fx.printmsg('serializing header as %s' % (f.name))
        json.dump(obj=header, fp=f, indent=4, sort_keys=True, default=str)

def csv(ar, outfile_abspath, header=None, verbose=False):
    """
    Output to csv. Data is read into a :py:class:`pandas.DataFrame`, then written using :py:func:`pandas.DataFrame.to_csv`.

    :param numpy.ndarray ar: Radar array
    :param str outfile_abspath: Output file path
    :param dict header: File header dictionary to write, if desired. Defaults to None.
    :param bool verbose: Verbose, defaults to False
    """
    if verbose:
        t = ''
        if header:
            t = ' with json header'
        fx.printmsg('output format is csv%s. writing data to: %s.csv' % (t, outfile_abspath))
    data = pd.DataFrame(ar) # using pandas to output csv
    data.to_csv('%s.csv' % (outfile_abspath)) # write
    if header:
        json_header(header=header, outfile_abspath=outfile_abspath, verbose=verbose)

def numpy(ar, outfile_abspath, header=None, verbose=False):
    """
    Output to binary numpy binary file (.npy) with the option of writing the header to .json as well.

    :param numpy.ndarray ar: Radar array
    :param str outfile_abspath: Output file path
    :param dict header: File header dictionary to write, if desired. Defaults to None.
    :param bool verbose: Verbose, defaults to False
    """
    if verbose:
        t = ''
        if header:
            t = ' with json header (compatible with GPRPy)'
        fx.printmsg('output format is numpy binary%s' % t)
        fx.printmsg('writing data to %s.npy' % outfile_abspath)
    np.save('%s.npy' % outfile_abspath, ar, allow_pickle=False)
    if header:
        json_header(header=header, outfile_abspath=outfile_abspath, verbose=verbose)

def gprpy(ar, header, outfile_abspath, verbose=False):
    """
    Save in a format `GPRPy <https://github.com/NSGeophysics/gprpy>`_ can open (numpy binary .npy and a .json formatted header file).
    
    .. note:: GPRPy support for this feature is forthcoming (https://github.com/NSGeophysics/GPRPy/issues/3#issuecomment-460462612).

    :param numpy.ndarray ar: Radar array
    :param str outfile_abspath: Output file path
    :param dict header: File header dictionary to write, if desired. Defaults to None.
    :param bool verbose: Verbose, defaults to False
    """
    numpy(ar=ar, header=header, outfile_abspath=outfile_abspath, verbose=verbose)

def segy(ar, outfile_abspath, header, verbose=False):
    """
    .. warning:: SEGY output is not yet available.

    In the future, this function will output to SEGY format.

    :param numpy.ndarray ar: Radar array
    :param str outfile_abspath: Output file path
    :param dict header: File header dictionary to write, if desired. Defaults to None.
    :param bool verbose: Verbose, defaults to False
    """
    fx.printmsg('ERROR: SEG-Y is not yet supported, please choose another format.')
    raise NotImplementedError('SEG-Y is not yet supported.')

def h5(ar, infile_basename, outfile_abspath, header, verbose=False):
    """
    .. warning:: HDF5 output is not yet available.

    In the future, this function will output to HDF5 format.

    :param numpy.ndarray ar: Radar array
    :param str infile_basename: Input file basename
    :param str outfile_abspath: Output file path
    :param dict header: File header dictionary to write, if desired. Defaults to None.
    :param bool verbose: Verbose, defaults to False
    """

    '''
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

    if verbose:
        fx.printmsg('output format is IceRadar HDF5. writing file to: %s' % outfile_abspath)

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

    if os.path.exists(infile_basename + '.DZG'):
        gps = readdzg(infile_basename + '.DZG', 'dzg', header['rhf_sps'], ar.shape[1], verbose)
    else:
        gps = '' # if there's no DZG file...need a way to parse another gps source if possible

    # make data structure
    n = 0 # line number, iteratively increased
    f = h5py.File('%s.h5' % (outfile_abspath), 'w') # overwrite existing file
    if verbose:
        fx.printmsg('exporting to %s.h5' % outfile_abspath)

    try:
        li = f.create_group('line_0') # create line zero
    except ValueError: # the line already exists in the file
        li = f['line_0']
    for sample in ar.T:
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
        eg = dc.create_dataset('echogram_0', (ar.shape[0],), data=sample)
        eg.attrs.create(svts, svts_str) # store pcsavetimestamp attribute
        eg.attrs.create(gpsx, gpsx_str) # store gpscluster attribute
        eg.attrs.create(dimx, dimx_str) # store digitizer attribute
        eg.attrs.create(gutx, gutx_str) # store utm gpscluster attribute
        n += 1
    f.close()

def writetime(d):
    '''
    Function to write dates to :code:`rfDateByte` binary objects in DZT headers.
    An inverse of the :py:func:`readgssi.dzt.readtime` function.

    DZT :code:`rfDateByte` objects are 32 bits of binary (01001010111110011010011100101111),
    structured as little endian u5u6u5u5u4u7 where all numbers are base 2 unsigned int (uX)
    composed of X number of bits. Four bytes is an unnecessarily high level of compression
    for a single date object in a filetype that often contains tens or hundreds of megabytes
    of array information anyway.

    So this function reads a datetime object and outputs
    (seconds/2, min, hr, day, month, year-1980).

    For more information on :code:`rfDateByte`, see page 55 of
    `GSSI's SIR 3000 manual <https://support.geophysical.com/gssiSupport/Products/Documents/Control%20Unit%20Manuals/GSSI%20-%20SIR-3000%20Operation%20Manual.pdf>`_.

    :param datetime d: the :py:class:`datetime.datetime` to be encoded
    :rtype: bytes
    '''
    # get binary values
    sec2 = int(bin(int(d.second / 2))[2:])
    mins = int(bin(d.minute)[2:])
    hr = int(bin(d.hour)[2:])
    day = int(bin(d.day)[2:])
    mo = int(bin(d.month)[2:])
    yr = int(bin(d.year - 1980)[2:])
    # create binary string with proper padding
    dtbits = '%07d%04d%05d%05d%06d%05d' % (yr, mo, day, hr, mins, sec2)
    # create four bytes that make up rfDateByte
    byt0 = int(dtbits[24:], 2)
    byt1 = int(dtbits[16:24], 2)
    byt2 = int(dtbits[8:16], 2)
    byt3 = int(dtbits[0:8], 2)
    # return a byte array
    return bytes([byt0, byt1, byt2, byt3])

def dzt(ar, outfile_abspath, header, verbose=False):
    """
    .. warning:: DZT output is only currently compatible with single-channel files.

    This function will output a RADAN-compatible DZT file after processing.
    This is useful to circumvent RADAN's distance-normalization bug
    when the desired outcome is array migration.

    Users can set DZT output via the command line by setting the
    :code:`-f dzt` flag, or in Python by doing the following: ::

        from readgssi.dzt import readdzt
        from readgssi import translate
        from readgssi.arrayops import stack, distance_normalize

        # first, read a data file
        header, data, gps = readdzt('FILE__001.DZT')

        # do some stuff
        # (distance normalization must be done before stacking)
        for a in data:
            header, data[a], gps = distance_normalize(header=header, ar=data[a], gps=gps)
            header, data[a], stack = stack(header=header, ar=data[a], stack=10)

        # output as modified DZT
        translate.dzt(ar=data, outfile_abspath='FILE__001-DnS10.DZT', header=header)

    This will output :code:`FILE__001-DnS10.DZT` as a distance-normalized DZT.

    :param numpy.ndarray ar: Radar array
    :param str infile_basename: Input file basename
    :param str outfile_abspath: Output file path
    :param dict header: File header dictionary to write, if desired. Defaults to None.
    :param bool verbose: Verbose, defaults to False
    """

    '''
    Assumptions:
    - constant velocity or distance between marks (may be possible to add a check)
    '''
    if len(ar) > 1:
        outfile_abspath = outfile_abspath.replace('c1', '')
    if not outfile_abspath.endswith(('.DZT', '.dzt')):
        outfile_abspath = outfile_abspath + '.DZT'
    
    outfile = open(outfile_abspath, 'wb')
    fx.printmsg('writing to: %s' % outfile.name)

    for i in range(header['rh_nchan']):
        fx.printmsg('writing DZT header for channel %s' % (i))
        # header should read all values per-channel no matter what
        outfile.write(struct.pack('<h', header['rh_tag']))
        outfile.write(struct.pack('<h', header['rh_data']))
        outfile.write(struct.pack('<h', header['rh_nsamp']))
        outfile.write(struct.pack('<h', 32)) # rhf_bits - for simplicity, just hard-coding 32 bit
        outfile.write(struct.pack('<h', header['rh_zero']))
        # byte 10
        outfile.write(struct.pack('<f', header['rhf_sps']))
        outfile.write(struct.pack('<f', header['rhf_spm'])) # dzt.py ln 94-97
        outfile.write(struct.pack('<f', header['rhf_mpm']))
        outfile.write(struct.pack('<f', header['rhf_position']))
        outfile.write(struct.pack('<f', header['rhf_range']))
        outfile.write(struct.pack('<h', header['rh_npass']))
        # byte 32
        outfile.write(writetime(header['rhb_cdt']))
        outfile.write(writetime(datetime.now())) # modification date/time
        # byte 40
        outfile.write(struct.pack('<h', header['rh_rgain']))
        outfile.write(struct.pack('<h', header['rh_nrgain']))
        outfile.write(struct.pack('<h', header['rh_text']))
        outfile.write(struct.pack('<h', header['rh_ntext']))
        outfile.write(struct.pack('<h', header['rh_proc']))
        outfile.write(struct.pack('<h', header['rh_nproc']))
        outfile.write(struct.pack('<h', header['rh_nchan']))
        outfile.write(struct.pack('<f', header['rhf_epsr'])) # dzt.py ln 121-126
        outfile.write(struct.pack('<f', header['rhf_top']))
        outfile.write(struct.pack('<f', header['rhf_depth']))
        # byte 66
        outfile.write(struct.pack('<f', header['rh_xstart'])) # part of rh_coordx
        outfile.write(struct.pack('<f', header['rh_xend'])) # part of rh_coordx
        outfile.write(struct.pack('<f', header['rhf_servo_level']))
        outfile.write(bytes(3)) # "reserved"
        outfile.write(struct.pack('B', header['rh_accomp']))
        outfile.write(struct.pack('<h', header['rh_sconfig']))
        outfile.write(struct.pack('<h', header['rh_spp']))
        outfile.write(struct.pack('<h', header['rh_linenum']))
        # byte 88
        outfile.write(struct.pack('<f', header['rh_ystart'])) # part of rh_coordy
        outfile.write(struct.pack('<f', header['rh_yend'])) # part of rh_coordy
        outfile.write(header['rh_96'])
        outfile.write(struct.pack('c', header['rh_dtype']))
        outfile.write(header['dzt_ant'][i])
        outfile.write(header['rh_112'])
        # byte 113
        outfile.write(header['vsbyte'])
        outfile.write(header['rh_name'])
        outfile.write(header['rh_chksum'])
        # byte 128
        outfile.write(header['INFOAREA'])
        outfile.write(header['rh_RGPS0'])
        outfile.write(header['rh_RGPS1'])
        i += 1

    outfile.write(header['header_extra'])

    stack = []
    i = 0
    for i in range(header['rh_nchan']):
        # replace zeroed rows
        stack.append(np.zeros((header['timezero'][i], ar[i].shape[1]),
                                    dtype=np.int32))
        stack.append(ar[i])
        i += 1

    writestack = np.vstack(tuple(stack))
    sh = writestack.shape
    writestack = writestack.T.reshape(-1)
    fx.printmsg('writing %s data samples for %s channels (%s x %s)'
          % (writestack.shape[0],
             int(len(stack)/2),
             sh[0], sh[1]))

    # hard coded to write 32 bit signed ints to keep lossiness to a minimum
    outfile.write(writestack.round().astype(np.int32, casting='unsafe').tobytes(order='C'))

    outfile.close()

