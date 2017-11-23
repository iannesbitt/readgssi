# readgssi

A tool intended to read binary GSSI ground-penetrating radar (GPR) data. Original Matlab code developed by Gabe Lewis, Dartmouth College Department of Earth Sciences. Python translation written with permission by Ian Nesbitt, University of Maine School of Earth and Climate Science.

## now
- calls to `__main__` with filename as argument will return various header statistics and array length
- calls to `__main__` with filename, output, and format as arguments will output a csv

## future
- calls to readgssi.readgssi(filename) from script or python shell will return np array and critical file statistics
- GPS transcription (read from associated DZX file)
- supplementing a geophysical format (HDF5, SEGY, etc.) will write to that format

## possible other tools
- stacking of data
- [irlib](https://github.com/njwilson23/irlib) integration (iir, timezero)
- usage of basic [obspy](https://github.com/obspy/obspy) filters