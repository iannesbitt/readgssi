Translating to different formats
#####################################

Functions that output radar data to various file formats.
Details on these functions can be found at :py:mod:`readgssi.translate`

===========================
DZT
===========================

.. |3k-manual| raw:: html

    <a target="_blank" href="https://support.geophysical.com/gssiSupport/Products/Documents/Control%20Unit%20Manuals/GSSI%20-%20SIR-3000%20Operation%20Manual.pdf">GSSI's SIR 3000 manual</a>

DZT is the native file format of GSSI data.
DZT files are binary and thus must follow strict formatting guidelines,
and can only be read by specialized software.
To write DZT files using readgssi, you can use either the command line or python
depending on your preference.

For more information on DZT files, see page 55 of |3k-manual|.

Basic DZT
---------------

Output to DZT is easy.

`Python:`

.. code-block:: python
    
    readgssi.readgssi(infile='DZT__001.DZT', outfile='DZT__001.DZT', frmt='dzt')

`bash:`

.. code-block:: bash
    
    readgssi -i DZT__001.DZT -o DZT__001.DZT -f dzt

DZT of processed data
-----------------------

It's common to process data before outputting. Here, we distance-normalize and filter before writing to DZT.

`Python:`

.. code-block:: python
    
    readgssi.readgssi(infile='DZT__001.DZT', outfile='DZT__001.DZT', frmt='dzt',
                      normalize=True, freqmin=60, freqmax=100, bgr=0)

`bash:`

.. code-block:: bash
    
    readgssi -i DZT__001.DZT -o DZT__001.DZT -f dzt -N -t 60-100 -r 0


===========================
CSV
===========================

Basic CSV
---------------

Translation to csv is also easy.

`Python:`

.. code-block:: python
    
    readgssi.readgssi(infile='DZT__001.DZT', outfile='DZT__001.csv', frmt='csv')

`bash:`

.. code-block:: bash
    
    readgssi -i DZT__001.DZT -o DZT__001.csv -f csv

CSV of processed data
-----------------------

It's common to process data before outputting. Here, we distance-normalize and filter before writing to CSV.

`Python:`

.. code-block:: python
    
    readgssi.readgssi(infile='DZT__001.DZT', outfile='DZT__001.csv', frmt='csv',
                      normalize=True, freqmin=60, freqmax=100, bgr=0)

`bash:`

.. code-block:: bash
    
    readgssi -i DZT__001.DZT -o DZT__001.csv -f csv -N -t 60-100 -r 0


===========================
numpy binary
===========================

The following python and bash commands do the same (process then output), but output to numpy binary format instead.

`Python:`

.. code-block:: python
    
    readgssi.readgssi(infile='DZT__001.DZT', outfile='DZT__001.csv', frmt='numpy',
                      normalize=True, freqmin=60, freqmax=100, bgr=0)

`bash:`

.. code-block:: bash
    
    readgssi -i DZT__001.DZT -o DZT__001.csv -f numpy -N -t 60-100 -r 0


===========================
GPRPy-compatible format
===========================

And finally, these commands output the same data to a format compatible with `GPRPy <https://github.com/NSGeophysics/gprpy>`_, which involves numpy binary (.npy) and a JSON serialization of header values.

`Python:`

.. code-block:: python
    
    readgssi.readgssi(infile='DZT__001.DZT', outfile='DZT__001.csv', frmt='gprpy',
                      normalize=True, freqmin=60, freqmax=100, bgr=0)

`bash:`

.. code-block:: bash
    
    readgssi -i DZT__001.DZT -o DZT__001.csv -f gprpy -N -t 60-100 -r 0

`Back to top ↑ <#top>`_
