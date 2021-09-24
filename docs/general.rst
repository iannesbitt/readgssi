.. role:: bash(code)
   :language: bash

.. role:: code(code)
   :language: python

#####################################
General usage
#####################################

:bash:`readgssi` can be run straight from a :bash:`bash` console, using a python interpreter like :bash:`ipython` or the python console, or scripted in a development environment like Jupyter Notebook, Spyder, or Pycharm. Usage of :bash:`bash` is covered in :ref:`bash usage`, while usage in python is covered below in :ref:`Python usage`.

.. note::
    In the first part of this tutorial, I will separate bash and python operations, but towards the end I will bring them together, as they will produce nearly identical outputs. However, I felt it pertinent to separate the two at the start, since some may know either bash or python but not both. Newcomers to either one will note that both have different benefits over the other, which is why I develop most of the functionality of this program to be accessible from both.

    bash is useful for coordinating calls to multiple files in a directory in for loops, which has distinct uses for processing large amounts of files in a much shorter amount of time than RADAN. bash's range of interoperability is much narrower, but it is very good at processing a number of things in a row using similar patterns of parameters.

    Python is useful for its ability to hold objects in memory, and to pass objects to and from various functions. Python's range is broader in terms of array manipulation and object passing.

===============================
Python usage
===============================

Most python functionality is covered under the modules in the left panel, and in the following sections. I will cover the very basics here.

The :py:func:`readgssi.readgssi.readgssi` covers a large portion of the use cases you are likely to want out of readgssi. A properly formulated command is long but should return what you want. In the future, radar arrays will be python classes, which will make things easier.

Simply printing a file's header information to output is easy:

.. code-block:: python

    >>> from readgssi import readgssi
    >>> readgssi.readgssi(infile='DZT__001.DZT', frmt=None, verbose=True)
    2019-07-22 16:56:20 - reading...
    2019-07-22 16:56:20 - input file:         DZT__001.DZT
    2019-07-22 16:56:20 - WARNING: no time zero specified for channel 0, defaulting to 2
    2019-07-22 16:56:20 - success. header values:
    2019-07-22 16:56:20 - system:             SIR 4000 (system code 8)
    2019-07-22 16:56:20 - antennas:           ['3207', None, None, None]
    2019-07-22 16:56:20 - time zeros:         [2, None, None, None]
    2019-07-22 16:56:20 - ant 0 center freq:  100 MHz
    2019-07-22 16:56:20 - date created:       2017-07-25 18:21:24+00:00
    2019-07-22 16:56:20 - date modified:      2018-08-06 17:02:24+00:00
    2019-07-22 16:56:20 - gps-enabled file:   yes
    2019-07-22 16:56:20 - number of channels: 1
    2019-07-22 16:56:20 - samples per trace:  2048
    2019-07-22 16:56:20 - bits per sample:    32 signed
    2019-07-22 16:56:20 - traces per second:  24.0
    2019-07-22 16:56:20 - traces per meter:   300.0
    2019-07-22 16:56:20 - epsr:               80.0
    2019-07-22 16:56:20 - speed of light:     3.35E+07 m/sec (11.18% of vacuum)
    2019-07-22 16:56:20 - sampling depth:     33.5 m
    2019-07-22 16:56:20 - "rhf_top":          3.4 m
    2019-07-22 16:56:20 - offset to data:     131072 bytes
    2019-07-22 16:56:20 - traces:             28343
    2019-07-22 16:56:20 - seconds:            1180.95833333
    2019-07-22 16:56:20 - array dimensions:   2048 x 28343
    2019-07-22 16:56:20 - beginning processing for channel 0 (antenna 3207)
    >>>

Note here that there is a warning regarding the time-zero. That can be set using :code:`zero=[int]`, but won't really come into play until the next section.

See :doc:`reading` for next steps.

`Back to top ↑ <#top>`_

===============================
bash usage
===============================

:py:data:`readgssi` comes with a UNIX command line interface, for easy bash scripting. This is very useful when processing folders full of many files. If you'd like a full description of all options, enter:

.. code-block:: bash

    readgssi -h

You should see readgssi output its help text, which will display options like those below, but in a more condensed form.

.. note::
    Each option flag here below passed to :py:func:`readgssi.readgssi.readgssi` after the command has been processed by :py:func:`readgssi.readgssi.main`.


Usage:

.. code-block:: bash

    readgssi -i input.DZT [OPTIONS]

Required flags
------------------

    -i file, --infile=file              Input DZT file.

Optional flags
------------------

    ``-o file``, ``--outfile=file``             Output file. If not set, the output file will be named similar to the input. See :py:func:`readgssi.functions.naming` for naming convention details.
    ``-f str``, ``--format=str``                Output file format (eg. "csv", "numpy", "gprpy"). See :py:mod:`readgssi.translate`.
    ``-p int``, ``--plot=int``                  Tells :py:func:`readgssi.plot.radargram` to create a radargram plot <int> inches high (defaults to 7).
    ``-D int``, ``--dpi=int``                   Set the plot DPI in :py:func:`readgssi.plot.radargram` (defaults to 150).
    ``-T``, ``--titleoff``                      Tells :py:func:`readgssi.plot.radargram` to turn the plot title off.
    ``-x m``, ``--xscale=m``                    X units for plotting. Will attempt to convert the x-axis to distance, time, or trace units based on header values. See :py:func:`readgssi.plot.radargram` for scale behavior. Combine with the :py:data:`-N` option to enable distance normalization, or :py:data:`-d int` to change the samples per meter.
    ``-z m``, ``--zscale=m``                    Z units for plotting. Will attempt to convert the x-axis to depth, time, or sample units based on header values. See :py:func:`readgssi.plot.radargram` for scale behavior. Combine with the :py:data:`-E int` option to change the dielectric.
    ``-e``, ``--zoom=[L,R,U,D]``                Set a zoom to automatically jump to. Takes list as argument, in the order is ``[left,right,up,down]`` and units are the same as axis.
    ``-n``, ``--noshow``                        Suppress matplotlib popup window and simply save a figure (useful for multi-file processing).
    ``-c str``, ``--colormap=str``              Specify the colormap to use in radargram creation function :py:func:`readgssi.plot.radargram`. For a list of values that can be used here, see https://matplotlib.org/users/colormaps.html#grayscale-conversion
    ``-g int``, ``--gain=int``                  Gain constant (higher=greater contrast, default: 1).
    ``-A``, ``--absval``                        Displays the absolute value of the vertical gradient of the array when plotting. Good for displaying faint array features, e.g. in blue ice.
    ``-r int``, ``--bgr=int``                   Horizontal background removal (useful to remove ringing). Specifying 0 as the argument here sets the window to full-width, whereas a positive integer sets the window size to that many traces after stacking.
    ``-R``, ``--reverse``                       Reverse (flip array horizontally) using :py:func:`readgssi.arrayops.flip`.
    ``-w``, ``--dewow``                         Trinomial dewow algorithm (experimental, use with caution). For details see :py:func:`readgssi.filtering.dewow`.
    ``-t int-int``, ``--bandpass=int-int``      Triangular FIR bandpass filter applied vertically (positive integer range in megahertz; ex. 70-130). For details see :py:func:`readgssi.filtering.triangular`.
    ``-b``, ``--colorbar``                      Adds a :py:class:`matplotlib.colorbar.Colorbar` to the radar figure.
    ``-a``, ``--antfreq=int``                   Set the antenna frequency. Overrides header value in favor of the one set here by the user.
    ``-s``, ``--stack=int``                     Set the trace stacking value or "auto" to autostack, which results in a ~2.5:1 x:y axis ratio.
    ``-N``, ``--normalize``                     Distance normalize. :py:func:`readgssi.gps.readdzg` reads the .DZG NMEA data file if it exists, otherwise tries to read CSV with lat, lon, and time fields. Then, the radar array and GPS time series are passed to :py:func:`readgssi.arrayops.distance_normalize` where the array is expanded and contracted proportional to the distance traveled between each GPS distance mark. This is done in chunks to save memory.
    ``-P``, ``--pausecorr``                     Pause correction;. Fixes decoupling of DZG and DZT trace numbers during survey pauses using low velocity GPS marks
    ``-d float``, ``--spm=float``               Specify the samples per meter (SPM). Overrides header value. Be careful using this option on distance-naive files, and files in which "time" was used as the main trigger for trace shots!
    ``-m``, ``--histogram``                     Produces a histogram of data values for each channel using :py:func:`readgssi.plot.histogram`.
    ``-E float``, ``--epsr=float``              User-defined epsilon_r (sometimes referred to as "dielectric"). If set, ignores value in DZT header in favor of the value set here by the user.
    ``-Z int``, ``-Z [int,int,int,int]``, ``--zero=int``, ``--zero= [int,int,int,int]``   Timezero: skip this many samples before the direct wave arrives at the receiver. Samples are removed from the top of the trace. Use a four-integer list format for multi-channel time-zeroing. Example: :py:data:`-Z 40,145,233,21`.

Command line functionality is explained further in the following sections.


`Back to top ↑ <#top>`_
