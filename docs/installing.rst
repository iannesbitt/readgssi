Installing
#####################################

*********************************
Requirements
*********************************

I strongly recommend installing the following dependencies via Anaconda (https://www.anaconda.com/distribution/).

* :py:data:`obspy` (https://docs.obspy.org)
* :py:mod:`numpy` (https://docs.scipy.org/doc/numpy)
* :py:mod:`scipy` (https://docs.scipy.org/doc/scipy/reference)
* :py:data:`matplotlib` (https://matplotlib.org)
* :py:mod:`pandas` (https://pandas.pydata.org/pandas-docs/stable)
* :py:data:`h5py` (http://docs.h5py.org/en/stable)

Those that are not available via the Anaconda installer are available on the Python Package Index (PyPI):

* :py:data:`pynmea2` (https://github.com/Knio/pynmea2)
* :py:mod:`geopy` (https://geopy.readthedocs.io/en/stable/)
* :py:data:`pytz` (https://pythonhosted.org/pytz/)

*********************************
Installation guide
*********************************

Installing from PyPI
=========================

.. note:: This does not cover the installation of Anaconda, as it may differ depending on your system, and there are many excellent resources out there that can explain far better than me for your system of choice. Start with https://docs.anaconda.com/anaconda/install/.

.. note:: The console commands outlined here use Linux bash script. Mac users should be able to use all the same commands as I do, but Windows users will need to install and understand the Windows Subsystem for Linux (WSL) in order to execute these commands successfully. If you'd like information about installing and using WSL, see this guide for more details: https://docs.microsoft.com/en-us/windows/wsl/install-win10

Once you have conda running, installing requirements is pretty easy. All dependencies are available through conda or pip. 

.. code-block:: console

    $ conda config --add channels conda-forge
    $ conda create -n readgssi python==3.7 pandas h5py pytz obspy
    $ conda activate readgssi
    $ pip install readgssi

That should allow you to run the commands below.

Installing from source
=========================

If you choose to install a specific commit rather than the latest working release of this software, I recommend doing so via the following commands:

.. code-block:: console

    $ conda config --add channels conda-forge
    $ conda create -n readgssi python==3.7 pandas h5py pytz obspy
    $ conda activate readgssi
    $ pip install git+https://github.com/iannesbitt/readgssi

If you plan on modifying the code and installing/reinstalling once you've made changes, you can do something similar to the following, assuming you have conda dependencies installed:

.. code-block:: console

    $ cd ~
    $ git clone https://github.com/iannesbitt/readgssi

    $ # make code changes if you wish, then:
    
    $ pip install ~/readgssi

Installing onto armv7l architecture
====================================

This has not been tested (though will be in the future), but installing on the Raspberry Pi and other ARM processors should be possible in theory. Start with this:

.. code-block:: console

    $ # from https://github.com/obspy/obspy/wiki/Installation-on-Linux-via-Apt-Repository
    $ deb http://deb.obspy.org stretch main
    $ wget --quiet -O - https://raw.github.com/obspy/obspy/master/misc/debian/public.key | sudo apt-key add -
    $ sudo apt-get update
    $ sudo apt-get install python-obspy python3-obspy
    $ sudo apt-get install ttf-bistream-vera
    $ rm -rf ~/.matplotlib ~/.cache/matplotlib
    $ sudo apt-get install python-pandas python-h5py
    $ pip install -U pytz pynmea2 geopy readgssi

    $ # test:
    $ readgssi -h
