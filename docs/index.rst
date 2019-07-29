`readgssi` |version| documentation
#####################################

Welcome to readgssi's documentation. This program was written to read and process ground-penetrating radar files from instruments made by Geophysical Survey Systems Incorporated (GSSI), although I have no affiliation with nor endorsement for the afforementioned organization.

The demands of ice- and ground-penetrating radar (GPR) surveying, as in many types of scientific fieldwork, require that both quality control and time savings are critical to a successful field campaign. This software provides a way to quickly read, process, and display radar data produced by GSSI radar antennas and control units. GSSI's own RADAN software is bulky, closed-source, non-free, and not meant to handle folders full of GPR data files at once. `readgssi` was designed to be used in the field to quality-check entire folders of data files by converting radar profiles to portable network graphics (PNG) images, saving users valuable time versus performing the equivalent actions by hand in RADAN, especially in the case of projects with large file counts.

The project's source repository is `here <https://github.com/iannesbitt/readgssi>`_.

.. toctree::
    :numbered:
    :maxdepth: 2
    :caption: Tutorial

    installing
    general
    reading
    plotting
    processing
    translating
    advanced
    troubleshooting
    contributing

.. toctree::
    :maxdepth: 2
    :caption: Modules

    readgssi
    dzt
    arrayops
    filtering
    functions
    gps
    plot
    translate
    constants
    config

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

`Back to top ↑ <#top>`_
