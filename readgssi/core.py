from obspy.core.util import AttribDict
import warnings
from future.utils import native_str
from obspy.core.utcdatetime import UTCDateTime


class Header(AttribDict):
    '''
    Container for header information of a Line object.
    Based heavily on the :py:class:`obspy.core.trace.Stats` class.

    '''
    # set of read only attrs
    readonly = ['MINHEADSIZE','PARAREASIZE','rhb_cdt', 'endtime', 'rh_nsamp']
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
        'timezero': 0,
        'antfreq': 200,
        'sec': 1,
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
        'delta', 'rhf_sps', 'starttime', 'rhf_depth', 'rhf_epsr', 'rhf_range',
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
            elif key == 'npts':
                if not isinstance(value, int):
                    value = int(value)
            # set current key
            super(Header, self).__setitem__(key, value)
            # set derived value: delta
            try:
                delta = 1.0 / float(self.sampling_rate)
            except ZeroDivisionError:
                delta = 0
            self.__dict__['delta'] = delta
            # set derived value: endtime
            if self.npts == 0:
                timediff = 0
            else:
                timediff = float(self.npts - 1) * delta
            self.__dict__['endtime'] = self.starttime + timediff
            return
        if key == 'component':
            key = 'channel'
            value = str(value)
            if len(value) != 1:
                msg = 'Component must be set with single character'
                raise ValueError(msg)
            value = self.channel[:-1] + value
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
    string to the Line.stats.processing list.
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

class Line(object):
    '''
    An object containing data of a continuous series, such as a radar survey line.

    '''


