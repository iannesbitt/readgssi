# readgssi
*Copyleft 🄯 2017-2019*

![Example Radargram](https://github.com/iannesbitt/readgssi/raw/master/examples/main.png)

[![PyPI version](https://img.shields.io/pypi/v/readgssi.svg?colorB=limegreen&label=pypi%20package)](https://badge.fury.io/py/readgssi)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.1439119.svg)](https://dx.doi.org/10.5281/zenodo.1439119)
[![License](https://img.shields.io/badge/license-GNU%20Affero%203.0-lightgrey.svg)](https://github.com/iannesbitt/readgssi/blob/master/LICENSE)
[![Build Status](https://travis-ci.org/iannesbitt/readgssi.svg?branch=master)](https://travis-ci.org/iannesbitt/readgssi)
[![Downloads per month](https://img.shields.io/pypi/dm/readgssi.svg)](https://pypi.org/project/readgssi/)

`readgssi` is a tool intended for use as an open-source reader and preprocessing module for subsurface data collected with Geophysical Survey Systems Incorporated (GSSI) ground-penetrating georadar (GPR) devices. It has the capability to read DZT and DZG files with the same pre-extension name and plot the data contained in those files. `readgssi` is also currently able to translate most DZT files to CSV and will be able to translate to other output formats including HDF5  (see [future](#future)). Matlab code donated by [Gabe Lewis](https://earthsciences.dartmouth.edu/people/gabriel-lewis), Dartmouth College Department of Earth Sciences. Python adaptation written with permission by Ian Nesbitt, University of Maine School of Earth and Climate Sciences.

The file read parameters are based on GSSI's DZT file description, similar to the ones available on pages 55-57 of the [SIR-3000 manual](https://support.geophysical.com/gssiSupport/Products/Documents/Control%20Unit%20Manuals/GSSI%20-%20SIR-3000%20Operation%20Manual.pdf). File structure is, unfortunately, prone to change at any time, and although I've been able to test with files from several systems, I have not encountered every iteration of file header yet. If you run into trouble, please [create a github issue](https://github.com/iannesbitt/readgssi/issues).

Questions, feature requests, and bugs: please [open a github issue](https://github.com/iannesbitt/readgssi/issues). Kindly provide the error output, describe what you are attempting to do, and attach the DZT/DZG file(s) causing you trouble.

## requirements
Strongly recommended to install via [anaconda](https://www.anaconda.com/download):
- [`obspy`](https://obspy.org/)
- [`matplotlib`](https://matplotlib.org/)
- [`numpy`](http://www.numpy.org/)
- [`pandas`](https://pandas.pydata.org/)
- [`h5py`](https://www.h5py.org/)

Install via `pip`:
- [`pynmea2`](https://pypi.org/project/pynmea2/)
- [`geopy`](https://pypi.org/project/geopy/)
- [`pytz`](https://pypi.org/project/pytz/)

## installation

Once you have [anaconda](https://www.anaconda.com/download) running, installing requirements is pretty easy.

```bash
conda config --add channels conda-forge
conda create -n readgssi python==3.7 pandas h5py pytz obspy
conda activate readgssi
pip install readgssi
```

That should allow you to run the commands below.

#### installing from source:

If you choose to install a specific commit rather than the [latest working release of this software](https://pypi.org/project/readgssi), you may download this package, unzip to your home folder, open a command line, then install in the following way:

```bash
pip install ~/readgssi
```

## usage

To display the help text:

```bash
$ readgssi -h

usage:
readgssi -i input.DZT [OPTIONS]

optional flags:
     OPTION     |      ARGUMENT       |       FUNCTIONALITY
-o, --output    | file:  /dir/f.ext   |  specify an output file
-f, --format    | string, eg. "csv"   |  specify output format (csv is the only working format currently)
-p, --plot      | +integer or "auto"  |  plot will be x inches high (dpi=150), or "auto". default: 10
-x, --xscale    | string, eg. "dist"  |  readgssi will attempt to convert the x-axis to distance, time, or traces based on header values
-z, --zscale    | string, eg. "time"  |  readgssi will attempt to convert the x-axis to depth, time, or samples based on header values
-n, --noshow    |                     |  suppress matplotlib popup window and simply save a figure (useful for multiple file processing)
-c, --colormap  | string, eg. "Greys" |  specify the colormap (https://matplotlib.org/users/colormaps.html#grayscale-conversion)
-g, --gain      | positive (+)integer |  gain value (higher=greater contrast, default: 1)
-r, --bgr       |                     |  horizontal background removal algorithm (useful to remove ringing)
-R, --reverse   |                     |  reverse (flip radargram horizontally)
-w, --dewow     |                     |  trinomial dewow algorithm
-t, --bandpass  | +int-+int (MHz)     |  butterworth bandpass filter (positive integer range in megahertz; ex. 100-145)
-b, --colorbar  |                     |  add a colorbar to the radar figure
-a, --antfreq   | positive integer    |  specify antenna frequency (read automatically if not given)
-s, --stack     | +integer or "auto"  |  specify trace stacking value or "auto" to autostack to ~2.5:1 x:y axis ratio
-N, --normalize |                     |  reads a .DZG NMEA data if it exists; otherwise tries to read a csv file with lat, lon, and time fields to distance normalize with
-d, --spm       | positive float      |  specify the samples per meter (spm) manually. overrides header value.
-m, --histogram |                     |  produce a histogram of data values
-E, --epsr      | float > 1.0         |  user-defined epsilon sub r (sometimes referred to as "dielectric"; ignores value in DZT header)
-Z, --zero      | positive integer    |  skip this many samples from the top of the trace downward (useful for removing transceiver delay)

naming scheme for exports:
   CHARACTERS   |      MEANING
    c0          |  Profile from channel 0 (can range from 0 - 3)
    Dn          |  Distance normalization
    Tz233       |  Time zero at 233 samples
    S8          |  Stacked 8 times
    Rv          |  Profile read in reverse (flipped horizontally)
    Bgr         |  Background removal filter
    Dw          |  Dewow filter
    Bp100-145   |  2-corner bandpass filter applied from 100 to 145 MHz
    G30         |  30x contrast gain
```

From a unix command line:
```bash
readgssi -i DZT__001.DZT
```
Simply specifying an input DZT file like in the above command (`-i file`) will display a host of data about the file including:
- name of GSSI control unit
- antenna model
- antenna frequency
- samples per trace
- bits per sample
- traces per second
- L1 dielectric as entered during survey
- sampling depth
- speed of light at given dielectric
- number of traces
- number of seconds

## basic functionality
### CSV output
```bash
readgssi -i DZT__001.DZT -o test.csv -f CSV
```
Translates radar data array to CSV format, if that's your cup of tea. One might use this to export to Matlab. One CSV will be written per channel. The script will rename the output to 'test_100MHz.csv' automatically. No header information is included in the CSV.

```bash
readgssi -i DZT__001.DZT -s 8 -w -r -o test.csv -f CSV
```
Applies 8x stacking, dewow, and background removal filters before exporting to CSV.

### plotting
#### example 1A
```bash
readgssi -i DZT__001.DZT -p 5 -s auto -c viridis -m
```
The above command will cause `readgssi` to save and show a plot named "DZT__001_100MHz.png" with a y-size of 6 inches at 150 dpi (`-p 6`) and the autostacking algorithm will stack the x-axis to some multiple of times shorter than the original data array for optimal viewing on a monitor, approximately 2.5\*y (`-s auto`). The plot will be rendered in the viridis color scheme, which is the default for matplotlib. The `-m` flag will draw a histogram for each data channel.
![Example 1a](https://github.com/iannesbitt/readgssi/raw/master/examples/1a.png)
![Example 1a histogram](https://github.com/iannesbitt/readgssi/raw/master/examples/1a-h.png)

#### example 1B
```bash
readgssi -i DZT__001.DZT -o 1b.png -p 5 -s auto -c viridis -g 50 -m -r -w
```
This will cause `readgssi` to create a plot from the same file, but matplotlib will save the plot as "1b.png" (`-o 1b.png`). The script will plot the y-axis size (`-p 5`) and automatically stack the x-axis to (`-s auto`). The script will plot the data with a gain value of 50 (`-g 50`), which will increase the plot contrast by a factor of 50. Next `readgssi` will run the background removal (`-r`) and dewow (`-w`) filters. Finally, the `-m` flag will draw a histogram for each data channel. Note how the histogram changes when filters are applied.
![Example 1b](https://github.com/iannesbitt/readgssi/raw/master/examples/1b.png)
![Example 1b histogram](https://github.com/iannesbitt/readgssi/raw/master/examples/1b-h.png)

#### example 1C: gain can be tricky depending on your colormap
```bash
readgssi -i DZT__001.DZT -o 1c.png -p 5 -s auto -r -w -c seismic
```
Here, background removal and dewow filters are applied, but no gain adjustments are made (equivalent to `-g 1`). The script uses matplotlib's "seismic" colormap (`-c seismic`) which is specifically designed for this type of waterfall array plotting. Even without gain, you will often be able to easily see very slight signal perturbations. It is not colorblind-friendly for either of the two most common types of human colorblindness, however, which is why it is not the default colormap.
![Example 1c](https://github.com/iannesbitt/readgssi/raw/master/examples/1c.png)

#### example 2A: no background removal
```bash
readgssi -i DZT__002.DZT -o 2a.png -p 10 -s 3 -n
```
Here `readgssi` will create a plot of size 10 and stack 3x (`-p 10 -s 3`). Matplotlib will use the default "Greys" colormap and save a PNG of the figure, but the script will suppress the matplotlib window (`-n`, useful for processing an entire directory full of DZTs at once).
![Example 2a](https://github.com/iannesbitt/readgssi/raw/master/examples/2a.png)

#### example 2B: horizontal mean BGR algorithm applied
```bash
readgssi -i DZT__002.DZT -o 2b.png -p 10 -s 3 -n -r
```
The script does the same thing, except it applies horizontal mean background removal `-r`. Note the difference in ringing artifacts between examples 2a and 2b.
![Example 2b](https://github.com/iannesbitt/readgssi/raw/master/examples/2b.png)


## contributors
- Ian Nesbitt ([@iannesbitt](https://github.com/iannesbitt), author)
- François-Xavier Simon ([@fxsimon](https://github.com/fxsimon))
- Thomas Paulin ([@thomaspaulin](https://github.com/thomaspaulin))

### citation suggestion:
Ian M. Nesbitt, François-Xavier Simon, Thomas Paulin, 2018. readgssi - an open-source tool to read and plot GSSI ground-penetrating radar data. [doi:10.5281/zenodo.1439119](https://dx.doi.org/10.5281/zenodo.1439119)

#### known bugs:
- color bar shows up too large on some plots (matplotlib bug)

## future
- explicit documentation
- automatic script testing for smoother dev
- create a class for surveyline objects, similar to [`obspy.core.trace.Trace`](https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.html)
- GPS transcription from CSV with fields like `mark name, lon, lat, elev, time`
- Use GPS altitude to adjust z position across profile
- GUI-based geologic/dielectric layer picking
  - layer velocity calculation (using minimum of clustered hyperbola tail angle measurements, or manual input)
  - velocity-based depth adjustments
  - ability to incorporate ground truth measurements
- velocity gradient/angle of incidence-based array migration
- translation to common geophysical formats (HDF5, SEGY, etc.)
- integration with [`vista`](https://docs.pyvista.org) for 3D visualization of location-aware arrays
