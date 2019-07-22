Reading radar data
#####################################

* :ref:`In Python`
* :ref:`In bash`

==========================
In Python
==========================

Simplest usage (reading the header)
-------------------------------------

As mentioned in the previous section, you can use :py:func:`readgssi.readgssi.readgssi` to output some of the header values:
* name of GSSI control unit
* antenna model
* antenna frequency
* samples per trace
* bits per sample
* traces per second
* L1 dielectric as entered during survey
* sampling depth
* speed of light at given dielectric
* number of traces
* number of seconds
* ...and more. In all likelihood, more than you need or want to know. However if you feel there is something important I'm leaving out, I'd be happy to include it. `Open a github feature request issue <https://github.com/iannesbitt/readgssi/issues/new>`_ and let me know what you would like to see.

Printing a file's header information to output is easy. Use :code:`frmt=None` and :code:`verbose=True`.

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

Note here that there is a warning regarding the time-zero. That can be set using :code:`zero=[int]`, as below.

Reading to python objects
----------------------------

Now, we'll be reading the file into python objects using :py:func:`readgssi.readgssi.readgssi`.

If you would like to return the header, radar array, and gps info (if it exists), and set time-zero to 233 samples, the command is simpler. Here, we drop :code:`verbose=True`, and :code:`frmt=None`, which suppresses console output and causes python objects to be returned:

.. code-block:: python

    >>> hdr, arrs, gps = readgssi.readgssi(infile='DZT__001.DZT', zero=[233])
    >>> type(hdr)
    <class 'dict'>
    >>> type(arr[0])
    <class 'numpy.ndarray'>
    >>> type(gps)
    <class 'pandas.core.frame.DataFrame'>

If no GPS file exists, you will get a soft error printed to the console, like this, and the :code:`gps` variable will be :code:`False`:

.. code-block:: python

    >>> hdr, arrs, gps = readgssi.readgssi(infile='DZT__002.DZT', zero=[233])
    2019-07-22 17:28:43 - WARNING: no DZG file found for GPS import
    >>> print(gps)
    False

No valid GPS file means that you will not be able to distance normalize the array using :code:`normalize=True`. If you do happen to have a valid GPS file to normalize with, skip to :doc:`processing` to learn how to do it.

`Back to top ↑ <#top>`_

===========================
In bash
===========================

Same as above, you can print a host of information about the DZT specified with a simple command.

From a unix/linux/mac command line or Windows Anaconda Prompt, type:

.. code-block:: bash

    $ readgssi -i DZT__001.DZT
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

`Back to top ↑ <#top>`_
