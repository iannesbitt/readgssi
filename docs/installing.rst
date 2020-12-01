Installing
#####################################

.. role:: bash(code)
   :language: bash

*********************************
Requirements
*********************************

I strongly recommend installing the following dependencies via Anaconda (https://www.anaconda.com/distribution/). These and other requirements are available in the `environment.yml <https://github.com/iannesbitt/readgssi/blob/master/environment.yml>`_ file in the project's `GitHub repository <https://github.com/iannesbitt/readgssi>`_.

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

`Back to top ↑ <#top>`_

*********************************
Installation guide
*********************************

.. note:: This does not cover the installation of Anaconda, as it may differ depending on your system, and there are many excellent resources out there that can explain far better than me for your system of choice. Start with `the Anaconda installation guide <https://docs.anaconda.com/anaconda/install/>`_.

.. note:: The console commands outlined here use Linux bash script. Mac users should be able to use all the same commands as I do, but Windows users will need to install and understand the Windows Subsystem for Linux (WSL) in order to execute these commands successfully. If you'd like information about installing and using WSL, see this guide for more details: https://docs.microsoft.com/en-us/windows/wsl/install-win10

Use of Anaconda is strongly recommended. After you've installed Anaconda, open a Terminal interface (UNIX) or the Anaconda Prompt (Windows) and make sure Anaconda works:

.. code-block:: bash

    conda --version

You should get output that displays the conda version (4.8.5 in my case). If not, `please see note 1 above <#installation-guide>`_.


Installing from Anaconda Cloud
================================

Anaconda cloud is `conda's package index <https://anaconda.org/>`_.
readgssi is `available as a conda package <https://anaconda.org/iannesbitt/readgssi>`_! This allows for a one-liner installation as indicated below.

.. code-block:: bash

    # create an environment named readgssi and install readgssi from the iannesbitt channel:
    conda create -n readgssi -c iannesbitt readgssi
    # and then activate the environment by doing:
    conda activate readgssi

Remember, you will need to activate the readgssi conda environment (i.e. :bash:`conda activate readgssi`) each time you open a new terminal window in order for the readgssi commands to work (see note below for a brief explanation).

This should allow you to run the commands in the next section (:doc:`general`).

.. note::

    :bash:`conda activate readgssi` switches into a "virtual environment" which is basically a python space where you can install dependencies without messing with the functionality of python on the rest of your machine. This is useful but can be confusing: if you try to run readgssi from outside the virtual environment you just made, you will not be able to find it! The reason it's useful is that it doesn't modify the version of python or packages that your computer may use for system tasks (no one likes obscure errors, so we try to avoid them...and one of the best ways of doing that is by using virtual environments). To get back into the readgssi environment you created from a newly opened terminal window, simply do :bash:`conda activate readgssi`.


Installing from PyPI
=========================

*PyPI is the* `Python Package Index <https://pypi.org>`_.

Once you have `conda running <#installation-guide>`_, installing requirements is pretty easy. All dependencies are available through conda or pip. 

.. code-block:: bash

    conda config --add channels conda-forge
    conda create -n readgssi python==3.7 pandas h5py pytz obspy
    conda activate readgssi
    pip install readgssi


That should allow you to run the commands in the next section (:doc:`general`).

.. note::

    This code is doing a couple important things so if you're unfamiliar with python and/or terminal commands, let's go over what they are. :bash:`conda config --add channels conda-forge` tells conda to look in the conda user code repository called "Conda Forge". ObsPy and a lot of other user-created code lives in the Forge. Next, :bash:`conda create -n readgssi` creates a virtual environment (more on that in a second).
    
    We tell conda what software to put in that virtual environment using the rest of the line (:bash:`python==3.7 pandas h5py pytz obspy`). We want python 3.7 specifically (hence :bash:`python==3.7`), and then the latest release of pandas, h5py, pytz, and obspy. This will install several other dependencies, notably numpy which is the library we really care about because it allows us to do math on arrays.

    Then, we activate our virtual environment using :bash:`conda activate readgssi` which allows us to operate in a "virtual environment" which is basically a python space where you can install dependencies without messing with the functionality of python on the rest of your machine. Now that we're in the virtual environment, we can install things using :bash:`pip`, the python package manager. :bash:`pip install readgssi` will install the readgssi version available on the Python Package Index (PyPI) into your readgssi environment, but nowhere else. This is useful but can be confusing: if you try to run readgssi from outside the virtual environment you just made, you will not be able to find it! The reason it's useful is that it doesn't modify the version of python or packages that your computer may use for system tasks (no one likes obscure errors, so we try to avoid them...and one of the best ways of doing that is by using virtual environments). To get back into the readgssi environment you created, simply do :bash:`conda activate readgssi`.

`Back to top ↑ <#top>`_

Installing from source
=========================

If you choose to install a specific commit rather than the latest working release of this software, I recommend doing so via the following commands:

.. code-block:: bash

    conda config --add channels conda-forge
    conda create -n readgssi python==3.7 pandas h5py pytz obspy
    conda activate readgssi
    pip install git+https://github.com/iannesbitt/readgssi

If you plan on modifying the code and installing/reinstalling once you've made changes, you can do something similar to the following, assuming you have conda dependencies installed:

.. code-block:: bash

    cd ~
    git clone https://github.com/iannesbitt/readgssi

    # make code changes if you wish, then:
    
    pip install ~/readgssi

`Back to top ↑ <#top>`_

Installing onto armv7l architecture
====================================

This has not been tested (though will be in the future), but installing on the Raspberry Pi and other ARM processors should be possible in theory. Start with this:

.. code-block:: bash

    # from https://github.com/obspy/obspy/wiki/Installation-on-Linux-via-Apt-Repository
    deb http://deb.obspy.org stretch main
    wget --quiet -O - https://raw.github.com/obspy/obspy/master/misc/debian/public.key | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install python-obspy python3-obspy
    sudo apt-get install ttf-bistream-vera
    rm -rf ~/.matplotlib ~/.cache/matplotlib
    sudo apt-get install python-pandas python-h5py
    pip install -U pytz pynmea2 geopy readgssi

.. todo:: Install and test readgssi on armv7l architecture

`Back to top ↑ <#top>`_

************************
Testing
************************

There is no testing module as such yet, but a simple test will ensure that most things are working properly:

.. code-block:: bash

    readgssi -V  # this will display the version
    readgssi -h  # this will display the help text

If it's working, head over to :doc:`general`.

.. todo:: Create a testing module and routines.

`Back to top ↑ <#top>`_
