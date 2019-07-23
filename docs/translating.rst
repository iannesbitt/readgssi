Translating to different formats
#####################################

===========================
CSV
===========================

Basic CSV
---------------

Translation to csv is easy.

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

And finally, these commands output the same data to a format compatible with `GPRPy <https://github.com/NSGeophysics/gprpy>`_.

`Python:`

.. code-block:: python
    
    readgssi.readgssi(infile='DZT__001.DZT', outfile='DZT__001.csv', frmt='gprpy',
                      normalize=True, freqmin=60, freqmax=100, bgr=0)

`bash:`

.. code-block:: bash
    
    readgssi -i DZT__001.DZT -o DZT__001.csv -f gprpy -N -t 60-100 -r 0

`Back to top ↑ <#top>`_
