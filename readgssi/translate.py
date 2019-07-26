import h5py
import pandas as pd
import numpy as np
import json
from readgssi.gps import readdzg
import readgssi.functions as fx

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