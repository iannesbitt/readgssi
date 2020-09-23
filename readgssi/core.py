from obspy.core.util import AttribDict
import warnings
from future.utils import native_str
from obspy.core.utcdatetime import UTCDateTime


class Header(AttribDict):
    '''
    Container for header information of a Channel object.
    Based heavily on the :py:class:`obspy.core.trace.Stats` class.

    '''
    # set of read only attrs
    readonly = [
        'MINHEADSIZE', 'PARAREASIZE', 'rhb_cdt',
        'endtime', 'rh_nsamp', 'sec',
        'traces',
        ]
    # default values
    defaults = {
        'MINHEADSIZE': 1024,
        'PARAREASIZE': 128,
        'GPSAREASIZE': 0,           # 2x size of RGPS
        'INFOAREASIZE': 1024-128,   # (MINHEADSIZE-PARAREASIZE-GPSAREASIZE)
        'rh_tag': None,
        'rh_data': None,
        'rh_nsamp': None,
        'rh_bits': None,
        'rh_zero': None,
        'rhf_sps': 1,
        'rhf_spm': None,
        'rhf_mpm': None,
        'rhf_position': None,
        'rhf_range': None,
        'rh_npass': None,
        'rhb_cdt': UTCDateTime(0),
        'rhb_mdt': UTCDateTime(0),
        'rh_rgain': None,
        'rh_nrgain': None,
        'rh_text': None,
        'rh_ntext': None,
        'rh_proc': None,
        'rh_nproc': None,
        'rh_nchan': None,
        'rhf_epsr': None,
        'rhf_top': None,
        'rhf_depth': None,
        'rh_xstart': None,
        'rh_xend': None,
        'rhf_servo_level': None,
        'rh_accomp': None,
        'rh_sconfig': None,
        'rh_spp': None,
        'rh_linenum': None,
        'rh_ystart': None,
        'rh_yend': None,
        'rh_96': None,
        'rh_dtype': None,
        'dzt_ant': None,
        'rh_pass0TX': None,
        'rh_pass1TX': None,
        'rh_version': None,
        'rh_system': None,
        'rh_name': None,
        'rh_chksum': None,
        'rh_RGPS': None,
        'RGPS0': None,
        'RGPS1': None,
        'starttime': UTCDateTime(0),
        'endtime': UTCDateTime(0),
        'delta': 1,
        'zdelta': 1e-9,
        'timezero': 0,
        'antfreq': 200,
        'sec': 1,
        'traces': 0,
        'depth': 0,
        'infile': None,
        'known_ant' = None,
        'dzt_ant' = None,
        'rh_ant' = None,
        'rh_antname' = None,
        'antfreq' = None,
        'system' = None,
    }
    # keys which need to refresh derived values
    _refresh_keys = {
        'delta', 'rhf_sps', 'starttime', 'rhf_depth', 'rhf_epsr', 'rhf_top',
        }
    # dict of required types for certain attrs
    _types = {
    }

    def __init__(self, header={}):
        """
        """
        super(Header, self).__init__(header)

    def __setitem__(self, key, value):
        """
        """
        if key in self._refresh_keys:
            # ensure correct data type
            if key == 'delta':
                key = 'rhf_sps'
                try:
                    value = 1.0 / float(value)
                except ZeroDivisionError:
                    value = 0.0
            elif key == 'rhf_sps':
                value = float(value)
            elif key == 'starttime':
                value = UTCDateTime(value)
            elif key == 'traces':
                if not isinstance(value, int):
                    value = int(value)
            elif key == 'rhf_depth':
                value = float(value)
            elif key == 'rhf_top':
                value = float(value)
            elif key == 'rhf_epsr':
                value = float(value)
            # set current key
            super(Header, self).__setitem__(key, value)
            # set derived value: delta
            try:
                delta = 1.0 / float(self.rhf_sps)
            except ZeroDivisionError:
                delta = 0
            self.__dict__['delta'] = delta
            # set derived value: endtime
            if self.traces == 0:
                timediff = 0
            else:
                timediff = float(self.traces - 1) * delta # could also be traces/sps
            self.__dict__['endtime'] = self.starttime + timediff
            self.__dict__['sec'] = timediff
            return
        # all other keys
        if isinstance(value, dict):
            super(Header, self).__setitem__(key, AttribDict(value))
        else:
            super(Header, self).__setitem__(key, value)

    __setattr__ = __setitem__

   def __getitem__(self, key, default=None):
        """
        """
        if key == 'component':
            return super(Header, self).__getitem__('channel', default)[-1:]
        else:
            return super(Header, self).__getitem__(key, default)

    def __str__(self):
        """
        Return better readable string representation of Header object.
        """
        priorized_keys = []
        return self._pretty_str(priorized_keys)

    def _repr_pretty_(self, p, cycle):
        p.text(str(self))

@decorator
def _add_processing_info(func, *args, **kwargs):
    """
    This is a decorator that attaches information about a processing call as a
    string to the Channel.header.processing list.
    """
    callargs = inspect.getcallargs(func, *args, **kwargs)
    callargs.pop("self")
    kwargs_ = callargs.pop("kwargs", {})
    from readgssi import __version__
    info = "readgssi {version}: {function}(%s)".format(
        version=__version__,
        function=func.__name__)
    arguments = []
    arguments += \
        ["%s=%s" % (k, repr(v)) if not isinstance(v, native_str) else
         "%s='%s'" % (k, v) for k, v in callargs.items()]
    arguments += \
        ["%s=%s" % (k, repr(v)) if not isinstance(v, native_str) else
         "%s='%s'" % (k, v) for k, v in kwargs_.items()]
    arguments.sort()
    info = info % "::".join(arguments)
    self = args[0]
    result = func(*args, **kwargs)
    # Attach after executing the function to avoid having it attached
    # while the operation failed.
    self._internal_add_processing_info(info)
    return result

class Channel(object):
    '''
    An object containing data of a continuous series, such as a radar survey channel.

    '''
    def __init__(self, data=np.array([]), header=None):
        # make sure Channel gets initialized with suitable ndarray as self.data
        # otherwise we could end up with e.g. a list object in self.data
        _data_sanity_checks(data)
        # set some defaults if not set yet
        if header is None:
            header = {}
        header = deepcopy(header)
        header.setdefault('npts', len(data))
        self.header = Header(header)
        # set data without changing npts in header object (for headonly option)
        super(Channel, self).__setattr__('data', data)

    @property
    def meta(self):
        return self.header

    @meta.setter
    def meta(self, value):
        self.header = value

    def __eq__(self, other):
        """
        Implements rich comparison of Channel objects for "==" operator.

        Channels are the same, if both their data and header are the same.
        """
        # check if other object is a Channel
        if not isinstance(other, Channel):
            return False
        # comparison of Header objects is supported by underlying AttribDict
        if not self.header == other.header:
            return False
        # comparison of ndarrays is supported by NumPy
        if not np.array_equal(self.data, other.data):
            return False

        return True

    def __ne__(self, other):
        """
        Implements rich comparison of Channel objects for "!=" operator.

        Calls __eq__() and returns the opposite.
        """
        return not self.__eq__(other)

    def __lt__(self, other):
        """
        Too ambiguous, throw an Error.
        """
        raise NotImplementedError("Too ambiguous, therefore not implemented.")

    def __le__(self, other):
        """
        Too ambiguous, throw an Error.
        """
        raise NotImplementedError("Too ambiguous, therefore not implemented.")

    def __gt__(self, other):
        """
        Too ambiguous, throw an Error.
        """
        raise NotImplementedError("Too ambiguous, therefore not implemented.")

    def __ge__(self, other):
        """
        Too ambiguous, throw an Error.
        """
        raise NotImplementedError("Too ambiguous, therefore not implemented.")

    def __nonzero__(self):
        """
        No data means no shots.
        """
        return bool(len(self.data))

    def __str__(self, id_length=None):
        """
        Return short summary string of the current channel.

        :rtype: str
        :return: Short summary string of the current channel containing the SEED
            identifier, start time, end time, sampling rate and number of
            points of the current channel.

        .. rubric:: Example

        >>> tr = Channel(header={'station':'FUR', 'network':'GR'})
        >>> str(tr)  # doctest: +ELLIPSIS
        'GR.FUR.. | 1970-01-01T00:00:00.000000Z - ... | 1.0 Hz, 0 samples'
        """
        # set fixed id width
        if id_length:
            out = "%%-%ds" % (id_length)
            trace_id = out % self.id
        else:
            trace_id = "%s" % self.id
        out = ''
        # output depending on delta or sampling rate bigger than one
        if self.header.sampling_rate < 0.1:
            if hasattr(self.header, 'preview') and self.header.preview:
                out = out + ' | '\
                    "%(starttime)s - %(endtime)s | " + \
                    "%(delta).1f s, %(npts)d samples [preview]"
            else:
                out = out + ' | '\
                    "%(starttime)s - %(endtime)s | " + \
                    "%(delta).1f s, %(npts)d samples"
        else:
            if hasattr(self.header, 'preview') and self.header.preview:
                out = out + ' | '\
                    "%(starttime)s - %(endtime)s | " + \
                    "%(sampling_rate).1f Hz, %(npts)d samples [preview]"
            else:
                out = out + ' | '\
                    "%(starttime)s - %(endtime)s | " + \
                    "%(sampling_rate).1f Hz, %(npts)d samples"
        # check for masked array
        if np.ma.count_masked(self.data):
            out += ' (masked)'
        return trace_id + out % (self.header)

    def _repr_pretty_(self, p, cycle):
        p.text(str(self))

    def __len__(self):
        """
        Return the number of data traces that make up the current channel.

        :rtype: int
        :return: Number of traces (in x direction).

        .. rubric:: Example

        >>> cha = Channel(data=np.array([1, 2, 3, 4]))
        >>> cha.count()
        4
        >>> len(cha)
        4
        """
        return self.data.shape[1]

    count = __len__
    lenx = __len__

    def lenz(self):
        '''
        Return the number of samples deep the channel is.

        :rtype: int
        :return: Number of samples (in z direction).

        .. rubric:: Example:

        >>> cha = Channel(data=np.array([1, 2], [3, 4]))
        >>> cha.lenz()
        2
        '''

        return self.data.shape[0]

    def shape(self):
        '''
        Return the shape of the array comprising the channel.

        :rtype: int
        :return: Number of samples (in x and z directions).

        .. rubric:: Example:

        >>> cha = Channel(data=np.array([1, 2, 3, 4], [5, 6, 7, 8]))
        >>> cha.shape()
        [2, 4]

        '''
        return self.data.shape

    def __setattr__(self, key, value):
        """
        __setattr__ method of Channel object.
        """
        # any change in Channel.data will dynamically set Channel.stats.npts
        if key == 'data':
            _data_sanity_checks(value)
            if self._always_contiguous:
                value = np.require(value, requirements=['C_CONTIGUOUS'])
            self.stats.npts = len(value)
        return super(Channel, self).__setattr__(key, value)

    def __getitem__(self, index):
        """
        __getitem__ method of Channel object.

        :rtype: list
        :return: List of data points
        """
        return self.data[index]

    def __mul__(self):
        """
        Create a new Stream containing num copies of this channel.

        :type num: int
        :param num: Number of copies.
        :returns: New ObsPy Stream object.

        .. rubric:: Example

        >>> from obspy import read
        >>> tr = read()[0]
        >>> st = tr * 5
        >>> len(st)
        5
        """
        raise NotImplementedError("Not yet implemented.")
        '''
        if not isinstance(num, int):
            raise TypeError("Integer expected")
        from obspy import Stream
        st = Stream()
        for _i in range(num):
            st += self.copy()
        return st
        '''

    def __div__(self, num):
        """
        Split Trace into new Stream containing num Traces of the same size.

        :type num: int
        :param num: Number of traces in returned Stream. Last trace may contain
            lesser samples.
        :returns: New ObsPy Stream object.

        .. rubric:: Example

        >>> from obspy import read
        >>> tr = read()[0]
        >>> print(tr)  # doctest: +ELLIPSIS
        BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z ... | 100.0 Hz, 3000 samples
        >>> st = tr / 7
        >>> print(st)  # doctest: +ELLIPSIS
        7 Trace(s) in Stream:
        BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z ... | 100.0 Hz, 429 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:07.290000Z ... | 100.0 Hz, 429 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:11.580000Z ... | 100.0 Hz, 429 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:15.870000Z ... | 100.0 Hz, 429 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:20.160000Z ... | 100.0 Hz, 429 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:24.450000Z ... | 100.0 Hz, 429 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:28.740000Z ... | 100.0 Hz, 426 samples
        """
        raise NotImplementedError("Not yet implemented.")
        '''
        if not isinstance(num, int):
            raise TypeError("Integer expected")
        from obspy import Stream
        total_length = np.size(self.data)
        rest_length = total_length % num
        if rest_length:
            packet_length = (total_length // num)
        else:
            packet_length = (total_length // num) - 1
        tstart = self.stats.starttime
        tend = tstart + (self.stats.delta * packet_length)
        st = Stream()
        for _i in range(num):
            st.append(self.slice(tstart, tend).copy())
            tstart = tend + self.stats.delta
            tend = tstart + (self.stats.delta * packet_length)
        return st
        '''
    # Py3k: '/' does not map to __div__ anymore in Python 3

    __truediv__ = __div__

    def __mod__(self, num):
        """
        Split Trace into new Stream containing Traces with num samples.

        :type num: int
        :param num: Number of samples in each trace in returned Stream. Last
            trace may contain lesser samples.
        :returns: New ObsPy Stream object.

        .. rubric:: Example

        >>> from obspy import read
        >>> tr = read()[0]
        >>> print(tr)  # doctest: +ELLIPSIS
        BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z ... | 100.0 Hz, 3000 samples
        >>> st = tr % 800
        >>> print(st)  # doctest: +ELLIPSIS
        4 Trace(s) in Stream:
        BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z ... | 100.0 Hz, 800 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:11.000000Z ... | 100.0 Hz, 800 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:19.000000Z ... | 100.0 Hz, 800 samples
        BW.RJOB..EHZ | 2009-08-24T00:20:27.000000Z ... | 100.0 Hz, 600 samples
        """
        raise NotImplementedError("Not yet implemented.")
        '''
        if not isinstance(num, int):
            raise TypeError("Integer expected")
        elif num <= 0:
            raise ValueError("Positive Integer expected")
        from obspy import Stream
        st = Stream()
        total_length = np.size(self.data)
        if num >= total_length:
            st.append(self.copy())
            return st
        tstart = self.stats.starttime
        tend = tstart + (self.stats.delta * (num - 1))
        while True:
            st.append(self.slice(tstart, tend).copy())
            tstart = tend + self.stats.delta
            tend = tstart + (self.stats.delta * (num - 1))
            if tstart > self.stats.endtime:
                break
        return st
        '''

    def __add__(self, trace, method=0, interpolation_samples=0,
                fill_value=None, sanity_checks=True):
        """
        Add another Trace object to current trace.

        :type method: int, optional
        :param method: Method to handle overlaps of traces. Defaults to ``0``.
            See the `Handling Overlaps`_ section below for further details.
        :type fill_value: int, float, str or ``None``, optional
        :param fill_value: Fill value for gaps. Defaults to ``None``. Traces
            will be converted to NumPy masked arrays if no value is given and
            gaps are present. If the keyword ``'latest'`` is provided it will
            use the latest value before the gap. If keyword ``'interpolate'``
            is provided, missing values are linearly interpolated (not
            changing the data type e.g. of integer valued traces).
            See the `Handling Gaps`_ section below for further details.
        :type interpolation_samples: int, optional
        :param interpolation_samples: Used only for ``method=1``. It specifies
            the number of samples which are used to interpolate between
            overlapping traces. Defaults to ``0``. If set to ``-1`` all
            overlapping samples are interpolated.
        :type sanity_checks: bool, optional
        :param sanity_checks: Enables some sanity checks before merging traces.
            Defaults to ``True``.

        Trace data will be converted into a NumPy masked array data type if
        any gaps are present. This behavior may be prevented by setting the
        ``fill_value`` parameter. The ``method`` argument controls the
        handling of overlapping data values.

        Sampling rate, data type and trace.id of both traces must match.

        .. rubric:: _`Handling Overlaps`

        ======  ===============================================================
        Method  Description
        ======  ===============================================================
        0       Discard overlapping data. Overlaps are essentially treated the
                same way as gaps::

                    Trace 1: AAAAAAAA
                    Trace 2:     FFFFFFFF
                    1 + 2  : AAAA----FFFF

                Contained traces with differing data will be marked as gap::

                    Trace 1: AAAAAAAAAAAA
                    Trace 2:     FF
                    1 + 2  : AAAA--AAAAAA

                Missing data can be merged in from a different trace::

                    Trace 1: AAAA--AAAAAA (contained trace, missing samples)
                    Trace 2:     FF
                    1 + 2  : AAAAFFAAAAAA
        1       Discard data of the previous trace assuming the following trace
                contains data with a more correct time value. The parameter
                ``interpolation_samples`` specifies the number of samples used
                to linearly interpolate between the two traces in order to
                prevent steps. Note that if there are gaps inside, the
                returned array is still a masked array, only if ``fill_value``
                is set, the returned array is a normal array and gaps are
                filled with fill value.

                No interpolation (``interpolation_samples=0``)::

                    Trace 1: AAAAAAAA
                    Trace 2:     FFFFFFFF
                    1 + 2  : AAAAFFFFFFFF

                Interpolate first two samples (``interpolation_samples=2``)::

                    Trace 1: AAAAAAAA
                    Trace 2:     FFFFFFFF
                    1 + 2  : AAAACDFFFFFF (interpolation_samples=2)

                Interpolate all samples (``interpolation_samples=-1``)::

                    Trace 1: AAAAAAAA
                    Trace 2:     FFFFFFFF
                    1 + 2  : AAAABCDEFFFF

                Any contained traces with different data will be discarded::

                    Trace 1: AAAAAAAAAAAA (contained trace)
                    Trace 2:     FF
                    1 + 2  : AAAAAAAAAAAA

                Missing data can be merged in from a different trace::

                    Trace 1: AAAA--AAAAAA (contained trace, missing samples)
                    Trace 2:     FF
                    1 + 2  : AAAAFFAAAAAA
        ======  ===============================================================

        .. rubric:: _`Handling gaps`

        1. Traces with gaps and ``fill_value=None`` (default)::

            Trace 1: AAAA
            Trace 2:         FFFF
            1 + 2  : AAAA----FFFF

        2. Traces with gaps and given ``fill_value=0``::

            Trace 1: AAAA
            Trace 2:         FFFF
            1 + 2  : AAAA0000FFFF

        3. Traces with gaps and given ``fill_value='latest'``::

            Trace 1: ABCD
            Trace 2:         FFFF
            1 + 2  : ABCDDDDDFFFF

        4. Traces with gaps and given ``fill_value='interpolate'``::

            Trace 1: AAAA
            Trace 2:         FFFF
            1 + 2  : AAAABCDEFFFF
        """
        raise NotImplementedError("Not yet implemented.")
        '''
        if sanity_checks:
            if not isinstance(trace, Trace):
                raise TypeError
            #  check id
            if self.get_id() != trace.get_id():
                raise TypeError("Trace ID differs: %s vs %s" %
                                (self.get_id(), trace.get_id()))
            #  check sample rate
            if self.stats.sampling_rate != trace.stats.sampling_rate:
                raise TypeError("Sampling rate differs: %s vs %s" %
                                (self.stats.sampling_rate,
                                 trace.stats.sampling_rate))
            #  check calibration factor
            if self.stats.calib != trace.stats.calib:
                raise TypeError("Calibration factor differs: %s vs %s" %
                                (self.stats.calib, trace.stats.calib))
            # check data type
            if self.data.dtype != trace.data.dtype:
                raise TypeError("Data type differs: %s vs %s" %
                                (self.data.dtype, trace.data.dtype))
        # check times
        if self.stats.starttime <= trace.stats.starttime:
            lt = self
            rt = trace
        else:
            rt = self
            lt = trace
        # check whether to use the latest value to fill a gap
        if fill_value == "latest":
            fill_value = lt.data[-1]
        elif fill_value == "interpolate":
            fill_value = (lt.data[-1], rt.data[0])
        sr = self.stats.sampling_rate
        delta = (rt.stats.starttime - lt.stats.endtime) * sr
        delta = int(compatibility.round_away(delta)) - 1
        delta_endtime = lt.stats.endtime - rt.stats.endtime
        # create the returned trace
        out = self.__class__(header=deepcopy(lt.stats))
        # check if overlap or gap
        if delta < 0 and delta_endtime < 0:
            # overlap
            delta = abs(delta)
            if np.all(np.equal(lt.data[-delta:], rt.data[:delta])):
                # check if data are the same
                data = [lt.data[:-delta], rt.data]
            elif method == 0:
                overlap = create_empty_data_chunk(delta, lt.data.dtype,
                                                  fill_value)
                data = [lt.data[:-delta], overlap, rt.data[delta:]]
            elif method == 1 and interpolation_samples >= -1:
                try:
                    ls = lt.data[-delta - 1]
                except Exception:
                    ls = lt.data[0]
                if interpolation_samples == -1:
                    interpolation_samples = delta
                elif interpolation_samples > delta:
                    interpolation_samples = delta
                try:
                    rs = rt.data[interpolation_samples]
                except IndexError:
                    # contained trace
                    data = [lt.data]
                else:
                    # include left and right sample (delta + 2)
                    interpolation = np.linspace(ls, rs,
                                                interpolation_samples + 2)
                    # cut ls and rs and ensure correct data type
                    interpolation = np.require(interpolation[1:-1],
                                               lt.data.dtype)
                    data = [lt.data[:-delta], interpolation,
                            rt.data[interpolation_samples:]]
            else:
                raise NotImplementedError
        elif delta < 0 and delta_endtime >= 0:
            # contained trace
            delta = abs(delta)
            lenrt = len(rt)
            t1 = len(lt) - delta
            t2 = t1 + lenrt
            # check if data are the same
            data_equal = (lt.data[t1:t2] == rt.data)
            # force a masked array and fill it for check of equality of valid
            # data points
            if np.all(np.ma.masked_array(data_equal).filled()):
                # if all (unmasked) data are equal,
                if isinstance(data_equal, np.ma.masked_array):
                    x = np.ma.masked_array(lt.data[t1:t2])
                    y = np.ma.masked_array(rt.data)
                    data_same = np.choose(x.mask, [x, y])
                    data = np.choose(x.mask & y.mask, [data_same, np.nan])
                    if np.any(np.isnan(data)):
                        data = np.ma.masked_invalid(data)
                    # convert back to maximum dtype of original data
                    dtype = np.max((x.dtype, y.dtype))
                    data = data.astype(dtype)
                    data = [lt.data[:t1], data, lt.data[t2:]]
                else:
                    data = [lt.data]
            elif method == 0:
                gap = create_empty_data_chunk(lenrt, lt.data.dtype, fill_value)
                data = [lt.data[:t1], gap, lt.data[t2:]]
            elif method == 1:
                data = [lt.data]
            else:
                raise NotImplementedError
        elif delta == 0:
            # exact fit - merge both traces
            data = [lt.data, rt.data]
        else:
            # gap
            # use fixed value or interpolate in between
            gap = create_empty_data_chunk(delta, lt.data.dtype, fill_value)
            data = [lt.data, gap, rt.data]
        # merge traces depending on NumPy array type
        if True in [isinstance(_i, np.ma.masked_array) for _i in data]:
            data = np.ma.concatenate(data)
        else:
            data = np.concatenate(data)
            data = np.require(data, dtype=lt.data.dtype)
        # Check if we can downgrade to normal ndarray
        if isinstance(data, np.ma.masked_array) and \
           np.ma.count_masked(data) == 0:
            data = data.compressed()
        out.data = data
        return out
        '''

    def get_id(self):
        """
        Return an identifier of the channel.

        :rtype: str
        :return: identifier

        The identifier contains the filename, antenna type, and system
        for the current Channel object.

        .. rubric:: Example

        >>> meta = {'filename': 'FILE__001.DZT', 'rh_ant': '3207', 'rh_system': 'SIR 4000'}
        >>> tr = Channel(header=meta)
        >>> print(tr.get_id())
        BW.MANZ..EHZ
        >>> print(tr.id)
        BW.MANZ..EHZ
        """
        syst = UNIT[self.stats.rh_system]
        out = "%(infile)s Ant %(antfreq)s Sys %(syst)s Ch %(channel)s"
        return out % (self.stats)

    id = property(get_id)

    @id.setter
    def id(self, value):
        """
        Set network, station, location and channel codes from a SEED ID.

        Raises an Exception if the provided ID does not contain exactly three
        dots (or is not of type `str`).

        >>> from obspy import read
        >>> tr = read()[0]
        >>> print(tr)  # doctest: +ELLIPSIS
        BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z ... | 100.0 Hz, 3000 samples
        >>> tr.id = "GR.FUR..HHZ"
        >>> print(tr)  # doctest: +ELLIPSIS
        GR.FUR..HHZ | 2009-08-24T00:20:03.000000Z ... | 100.0 Hz, 3000 samples

        :type value: str
        :param value: SEED ID to use for setting `self.stats.network`,
            `self.stats.station`, `self.stats.location` and
            `self.stats.channel`.
        """
        try:
            f, ant, syst, ch = .replace(' Ant ', ',').replace(' Sys ', ',').replace(' Ch ', ',').split(',')
        except AttributeError:
            msg = ("Can only set a Trace's SEED ID from a string "
                   "(and not from {})").format(type(value))
            raise TypeError(msg)
        except ValueError:
            msg = ("Not a valid SEED ID: '{}'").format(value)
            raise ValueError(msg)
        self.stats.infile = f
        self.stats.antenna = ant
        self.stats.system = syst
        self.stats.channel = ch

