# readgssi v0.0.6-beta2

A tool intended for use as an open-source translator and preprocessing module for subsurface data collected with GSSI ground-penetrating georadar (GPR) devices. It has the capability to read DZT and DZG files with the same pre-extension name and will be able to translate to multiple output formats including HDF5 and CSV, and create matplotlib plots as well, though not all formats are available yet (SEG-Y is in future plans). Original Matlab code developed by Gabe Lewis, Dartmouth College Department of Earth Sciences. Python translation written with permission by Ian Nesbitt, University of Maine School of Earth and Climate Science.

Questions, feature requests, and bugs: **ian * nesbitt at gmail * com**

## changes in 0.0.6-beta2
- added support for the D50800 antenna
- added plotting support for dual-channel radar devices
  - merged #3 from @fxsimon which fixed a bug that caused multi-channel file traces to be read in a 121212 sequence instead of 111222
- updated the workings of the plotting algorithm's colormap
- changed the way files are saved (bug in 0.0.5 mangled some filenames)
- added the ability to specify colormap and whether to draw a colorbar and a histogram
- added an automatic figsize option (leaves figsize up to Matplotlib)
#### known bugs:
- time-zero is broken (it's currently a constant and needs to be a function of antenna separation and samplerate)
- translation to anything but csv is broken (hope to have time for a fix soon)
  - csv translation does not work for dual-channel radar devices (exports to file but channels are merged end-to-end)
- color bar shows up too large on some plots (no known fix yet)
- colormap of radargram doesn't always work for certain types of data (adding user-adjustable gain soon)

## usage
```
usage:
readgssi.py -i <input DZX> [OPTIONS]

optional flags:
-v                    = verbose
-o f.ext              = specify output file
-f "csv"              = specify output format (csv is the only working format currently)
-p integer or "auto"  = plot will be x inches high (dpi=150), or if "auto", the default matplotlib figsize
-c "Greys"            = specify the colormap (https://matplotlib.org/users/colormaps.html#grayscale-conversion)
-b                    = add a colorbar to the figure
-a integer            = specify antenna frequency (read automatically if not given)
-s integer or "auto"  = specify trace stacking value or "auto" to autostack to ~2.5:1 x:y axis ratio
-g                    = produce a histogram of data values
```

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
readgssi.py -i DZT__001.DZT -p "auto" -s "auto" -g
```
This will create the same plot but matplotlib will determine the y-axis size and the autostacking algorithm will stack the x-axis to approximately 2.5\*y for optimal display. The `-g` flag will draw a histogram for each data channel.

```
readgssi.py -i DZT__001.DZT -o test.csv -f CSV
```
Translates radar data to CSV format, which can be imported to, for example, `numpy` or `pandas` (or R, if that's your cup of tea).

## contributors
- Ian Nesbitt ([@iannesbitt](https://github.com/iannesbitt), author)
- Francois-Xavier Simon ([@fxsimon](https://github.com/fxsimon))
- Thomas Paulin ([@thomaspaulin](https://github.com/thomaspaulin))

## future
- GPS transcription (read from associated DZG file or CSV with mark name, lon, lat, elev, time)
- supplementing a flag indicating geophysical format (HDF5, SEGY, etc.) will write to that format
- calls to readgssi.readgssi(filename) from script or python shell will return np array and critical file statistics

## possible other future tools
- [irlib](https://github.com/njwilson23/irlib) integration (iir, timezero)
- usage of basic [obspy](https://github.com/obspy/obspy) filters?
