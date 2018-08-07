# readgssi v0.0.5

A tool intended for use as an open-source translator and preprocessing module for subsurface data collected with GSSI ground-penetrating georadar (GPR) devices. It has the capability to read DZT and DZG files with the same pre-extension name and will be able to translate to multiple output formats including HDF5 and CSV, and create matplotlib plots as well, though not all formats are available yet (SEG-Y is in future plans). Original Matlab code developed by Gabe Lewis, Dartmouth College Department of Earth Sciences. Python translation written with permission by Ian Nesbitt, University of Maine School of Earth and Climate Science.

Questions, feature requests, and bugs: **ian * nesbitt at gmail * com**

## usage
From a unix command line:
```
readgssi.py -i DZT__001.DZT
```
Simply specifying an input DZT file will display a host of data about the file including:
- name of GSSI control unit
- antenna model
- antenna frequency
- samples per trace
- bits per sample
- traces per second
- L1 dilectric
- sampling depth
- number of traces
- number of seconds
```
readgssi.py -i DZT__001.DZT -p 20 -s 6
```
The above command will create and save a plot named "DZT__001.png" with a y-size of 20 inches and stack the x-axis to 6 times shorter than the original data array.

```
readgssi.py -i DZT__001.DZT -p 20 -s "auto"
```
This will create the same plot but use the autostacking algorithm to stack the x-axis to approximately 2.5\*y for optimal display.

## future
- GPS transcription (read from associated DZG file or CSV with mark name, lon, lat, elev, time)
- supplementing a flag indicating geophysical format (HDF5, SEGY, etc.) will write to that format
- calls to readgssi.readgssi(filename) from script or python shell will return np array and critical file statistics

## possible other future tools
- [irlib](https://github.com/njwilson23/irlib) integration (iir, timezero)
- usage of basic [obspy](https://github.com/obspy/obspy) filters?
