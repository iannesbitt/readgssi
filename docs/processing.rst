Processing radar arrays
#####################################

.. todo:: Under construction.

===========================
Stacking
===========================

Autostacking
-------------------

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='1a.png', frmt=None,
                      zero=[233], plot=5, gain=60, stack='auto')

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 1a.png -Z 233 -p 5 -g 60 -s auto

.. image:: _static/1a.png
    :width: 100%
    :alt: Autostacking


Stacking an explicit number of times
--------------------------------------

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='1b.png', frmt=None,
                      zero=[233], plot=5, gain=60, stack=5)

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 1b.png -Z 233 -p 5 -g 60 -s 3

.. image:: _static/1b.png
    :width: 100%
    :alt: Stacking an explicit number of times

=================================
Getting rid of horizontal noise
=================================

Horizontal average filters (BGR)
----------------------------------

Horizontal average filters, also known as background removal or BGR, are commonly used to remove both low-frequency skew and higher frequency horizontal reverberation banding that can occur in some survey environments. In this program there are two types of BGR: full-width average and moving window average. The former resembles RADAN's simplest BGR algorithm, while the latter emulates its BOXCAR style filter.

Full-width
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The full-width BGR filter in readgssi simply takes the average of each row in the array and subtracts that value from the row values themselves, essentially moving their mean value to zero. This can work well in some environments but can cause additional horizontal banding if strongly reflective layers are horizontal for many consecutive traces.

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='2a.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60,
                      bgr=0)


.. code-block:: bash

    readgssi -i DZT__001.DZT -o 2a.png -Z 233 -p 5 -s auto -g 60 -r 0

.. image:: _static/2a.png
    :width: 100%
    :alt: Full-width BGR

Boxcar/moving window
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The boxcar-style method is preferred by many because although it has a tendancy to wipe out data that's too strongly horizontal, it also removes more noise from areas of weak returns and can help make the profile look cleaner. The side effect of this is that it causes artificial wisps on either side of non-horizontal objects, about the size of half the window, and that it can wipe out horizontal layers that are longer than the window length. If you find that it turns horizontal layers into indistinguishable mush, increase the window size and try again.

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='2b.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60,
                      bgr=100)

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 2b.png -Z 233 -p 5 -s auto -g 60 -r 100

.. image:: _static/2b.png
    :width: 100%
    :alt: Boxcar/moving window BGR

Frequency filter (vertical triangular bandpass)
-------------------------------------------------

The vertical filter is more sophisticated and requires proper identification of the antenna's center frequency. Because antennas emit bands of frequencies centered around the manufacturer's specified center frequency, data will often lie within those frequencies. However, noise at other frequency bands is sometimes picked up, whether due to the dielectric of the first layer, or external sources. Often it will be necessary to let pass only the frequencies around the center frequency. 

For a 100 MHz antenna, this band can be as wide as 70-130 MHz at low dielectric values. Open water profiles are often much cleaner after being filtered approximately 80% as high as those in higher dielectric media, approximately 60-100 MHz.

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='2c.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60,
                      freqmin=60, freqmax=100)

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 2c.png -Z 233 -p 5 -s auto -g 60 -t 60-100

.. image:: _static/2c.png
    :width: 100%
    :alt: Vertical triangular bandpass


Combining filters
-------------------------------

It's typically worthwhile to play with combining filters, as often they can have a compounding effect on cleaning up the profile. See for example what the application of both the horizontal moving window and the vertical triangular filter can do to make the water column of this lake profile look clean enough to see thermoclines:

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='2c.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60, dpi=300,
                      bgr=100, freqmin=60, freqmax=100)

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 2c.png -Z 233 -p 5 -s auto -g 60 -D 300 -r 100 -t 60-100

.. image:: _static/2d.png
    :width: 100%
    :alt: Both horizontal and vertical filters

===========================
Distance normalization
===========================

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='2c.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60,
                      normalize=True)

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 3a.png -Z 233 -p 5 -s auto -g 60 -N -x m

.. image:: _static/3a.png
    :width: 100%
    :alt: Vertical triangular bandpass

===========================
Reversing
===========================

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='4a.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60,
                      reverse=True)

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 4a.png -Z 233 -p 5 -s auto -g 60 -R

.. image:: _static/4a.png
    :width: 100%
    :alt: Vertical triangular bandpass


`Back to top ↑ <#top>`_
