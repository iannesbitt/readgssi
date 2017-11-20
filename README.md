# readgssi

A tool intended to read binary GSSI ground-penetrating radar (GPR) data. Original Matlab code developed by Gabe Lewis, Dartmouth College Department of Earth Sciences. Python translation written with permission by Ian Nesbitt, University of Maine School of Earth and Climate Science.

## now
- calls to `__main__` with filename as argument will return various header statistics and array length

## future
- calls to readgssi.readgssi(filename) will return np array and critical file statistics
- GPS implementation (read from associated DZX file)
- supplementing -c and format (HDF5, SEGY, etc.) will convert to the specified format

- irlib integration
- usage of basic obspy filters (FIR)