Plotting radargrams
#####################################

* :ref:`Plotting with Python`
* :ref:`Plotting with bash`

.. note::
    I apologize to metric system users. matplotlib uses inches and dots per inch (DPI) and for consistency's sake I chose to adhere to imperial units for plot size :(

I give a basic plotting example here, but you will quickly realize that a lot of radar data requires at least a little bit of a touchup before it looks presentable. That's covered in the next section, :doc:`processing`.

===========================
Plotting with Python
===========================

Rudimentary plot (python)
--------------------------

Plotting in Python just means setting :code:`plot=7` or another integer, which represents the vertical size in inches. In this example, we use the :code:`zero=[233]` flag to get rid of the part of the radargram from before the direct wave meets the receiver.

.. code-block:: python

    from readgssi import readgssi
    readgssi.readgssi(infile='DZT__001.DZT', outfile='0a.png', frmt=None,
                      zero=[233], plot=5)

.. image:: _static/0a.png
    :width: 100%
    :alt: That's too wide

Whoops! That's very long and not very helpful on this screen. Let's pretend we've read :doc:`processing` and know how to stack arrays horizontally (see :ref:`Stacking`), and let's also add some gain to this image as well.

Gain (python)
---------------

Gain is added using the :code:`gain=int` setting. Let's set that to 60, since this is a lake profile and radar waves attenuate quickly in water.

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='0b.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60)

.. image:: _static/0b.png
    :width: 100%
    :alt: Much better!

Wow, looking much better! Now let's see if we can display depth units on the Z-axis.


Z axis depth (python)
----------------------

To set the z-axis to display water depth, we use two separate flags: :code:`epsr=80` --- which modifies the wave velocity by setting the dielectric to roughly that of water at 20 degrees C --- and :code:`z='m'`, which sets the z-axis to use those units to calculate profile depths. `"m"` stands for `meters`, but you can also specify "meters", "centimeters"/"cm", or "millimeters"/"mm" explicitly.



.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='0c.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60,
                      epsr=80, z='m')

.. image:: _static/0c.png
    :width: 100%
    :alt: With water depth displayed on the Z-axis

Looking good so far, but we will try removing some of that noise in :doc:`processing`.

`Back to top ↑ <#top>`_

===========================
Plotting with bash
===========================

Rudimentary plot (bash)
--------------------------

Plotting on the command line is easy. The most basic plotting routine is accessible just by setting the -p flag and specifying a plot height in inches (-p 5). Here, we also use a zero of 233 samples (:code:`-Z 233`).

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 0a.png -Z 233 -p 5

.. image:: _static/0a.png
    :width: 100%
    :alt: That's too wide (bash edition)

Whoops! As you notice in the Python example above, this file is very long, which makes viewing tough on a screen (but may be good for figure creation).

Gain (bash)
---------------

Let's use a function that will condense this very long file horizontally (:code:`-s auto`; called :ref:`Stacking`) in :doc:`processing`, and then plot with increased gain (:code:`-g 60`).

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 0b.png -Z 233 -p 5 -s auto -g 60

.. image:: _static/0b.png
    :width: 100%
    :alt: Much better


Z axis depth (bash)
---------------------

Now let's say we want to display a water depth z-axis like above. To do that, simply supply :code:`-z m` and :code:`-E 80` (`m` stands for `meters`, but you can also specify meters, centimeters/cm, or millimeters/mm explicitly).

.. code-block:: bash

    readgssi -i DZT__001.DZT -o 0c.png -Z 233 -p 5 -s auto -g 60 -z m -E 80

.. image:: _static/0c.png
    :width: 100%
    :alt: With water depth displayed on the Z-axis

Let's head to :doc:`processing` to try and remove some of that noise.

`Back to top ↑ <#top>`_


================================
Making poster-quality figures
================================

Let's say you are really enamored with the way that last figure looks, and you now want to create a figure-quality image for a poster. You'll likely want to drop the title (:code:`title=False` in Python or :bash:`-T` in bash), and increase the DPI to something that will work well on a plotter (:code:`dpi=300` in Python or :bash:`-D 300` in bash). Pretty simple. Let's see it in action.

.. note:: I use 300 DPI here to keep file size down, but if you are truly aiming for very high print quality, you may want to increase to 600 DPI to match the capability of most high-end plotters.

.. code-block:: python

    readgssi.readgssi(infile='DZT__001.DZT', outfile='0d.png', frmt=None,
                      zero=[233], plot=5, stack='auto', gain=60,
                      epsr=80, z='m', title=False, dpi=300)

.. code-block:: bash

     readgssi -i DZT__001.DZT -o 0d.png -Z 233 -p 5 -s auto -g 60 -z m -E 80 -T -D 300

.. image:: _static/0d.png
    :width: 100%
    :alt: No plot title and figure-quality DPI

`Back to top ↑ <#top>`_