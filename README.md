# readgssi v0.0.7
*Copyleft 🄯 2017-2019*

![Example Radargram](https://github.com/iannesbitt/readgssi/raw/master/examples/1.png)

[![PyPI version](https://badge.fury.io/py/readgssi.svg)](https://badge.fury.io/py/readgssi)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.1439119.svg)](https://dx.doi.org/10.5281/zenodo.1439119)
[![License](https://img.shields.io/badge/license-GNU%20Affero%203.0-lightgrey.svg)](https://github.com/iannesbitt/readgssi/blob/master/LICENSE)

`readgssi` is a tool intended for use as an open-source reader and preprocessing module for subsurface data collected with Geophysical Survey Systems Incorporated (GSSI) ground-penetrating georadar (GPR) devices. It has the capability to read DZT and DZG files with the same pre-extension name and plot the data contained in those files. `readgssi` is also currently able to translate most DZT files to CSV and will be able to translate to multiple other output formats including HDF5 and SEG-Y, though not all formats are available yet (see [future](#future)). Matlab code donated by [Gabe Lewis](https://earthsciences.dartmouth.edu/people/gabriel-lewis), Dartmouth College Department of Earth Sciences. Python adaptation of Matlab code written with permission by Ian Nesbitt, University of Maine School of Earth and Climate Sciences.

The file read parameters are based on GSSI's DZT file description, similar to the ones available on pages 55-57 of the [SIR-3000 manual](https://support.geophysical.com/gssiSupport/Products/Documents/Control%20Unit%20Manuals/GSSI%20-%20SIR-3000%20Operation%20Manual.pdf). File structure is, unfortunately, prone to change at any time, and although I've been able to test with files from several systems, I have not encountered every iteration of file header yet. If you run into trouble, please [create a github issue](https://github.com/iannesbitt/readgssi/issues), or contact me at the address below.

Questions, feature requests, and bugs: **ian * nesbitt at gmail * com** (kindly provide the error, what you are attempting to do, and the file causing you trouble when you contact me)

## requirements
Strongly recommended to install via [anaconda](https://www.anaconda.com/download)
- [`obspy`](https://obspy.org/)
- [`matplotlib`](https://matplotlib.org/)
- [`numpy`](http://www.numpy.org/)
- [`pandas`](https://pandas.pydata.org/)
- [`h5py`](https://www.h5py.org/)

## installation

Once you have [anaconda](https://www.anaconda.com/download) running, installing requirements is pretty easy.

```bash
conda config --add channels conda-forge
conda create -n readgssi python==3.7
conda activate readgssi
conda install pandas h5py pytz obspy
pip install pynmea2 readgssi
```

That should allow you to run the commands below.

#### Note:

If you choose to install a specific commit rather than the [latest working release of this software](https://dx.doi.org/10.5281/zenodo.1439119), you may download this package, unzip to your home folder, open a command line, then install in the following way:

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
-v, --verbose   |                     |  verbosity
-o, --output    | file:  /dir/f.ext   |  specify an output file
-f, --format    | string, eg. "csv"   |  specify output format (csv is the only working format currently)
-p, --plot      | +integer or "auto"  |  plot will be x inches high (dpi=150), or "auto". default: 10
-n, --noshow    |                     |  suppress matplotlib popup window and simply save a figure (useful for multiple file processing)
-c, --colormap  | string, eg. "Greys" |  specify the colormap (https://matplotlib.org/users/colormaps.html#grayscale-conversion)
-g, --gain      | positive integer    |  gain value (higher=greater contrast, default: 1)
-r, --bgr       |                     |  horizontal background removal algorithm (useful to remove ringing)
-w, --dewow     |                     |  trinomial dewow algorithm
-t, --bandpass  | +int-+int (MHz)     |  butterworth bandpass filter (positive integer range in megahertz; ex. 100-145)
-b, --colorbar  |                     |  add a colorbar to the radar figure
-a, --antfreq   | positive integer    |  specify antenna frequency (read automatically if not given)
-s, --stack     | +integer or "auto"  |  specify trace stacking value or "auto" to autostack to ~2.5:1 x:y axis ratio
-m, --histogram |                     |  produce a histogram of data values
-z, --zero      | positive integer    |  skip this many samples from the top of the trace downward (useful for removing transceiver delay)
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
- L1 dilectric
- sampling depth
- speed of light at given dilectric
- number of traces
- number of seconds

## basic functionality
### CSV output
```bash
readgssi -i DZT__001.DZT -o test.csv -f CSV
```
Translates radar data array to CSV format, if that's your cup of tea. No header information is included in the CSV, however.

### plotting
#### example 1A
```bash
readgssi -i DZT__001.DZT -p 5 -s auto -c viridis
```
The above command will cause `readgssi` to save and show a plot named "DZT__001_100MHz.png" with a y-size of 6 inches at 150 dpi (`-p 6`) and the autostacking algorithm will stack the x-axis to some multiple of times shorter than the original data array for optimal viewing, approximately 2.5\*y (`-s auto`). The plot will be rendered in the viridis color scheme, which is the default for matplotlib.
![Example 1a](https://github.com/iannesbitt/readgssi/raw/master/examples/DZT__001_100MHz.png)

#### example 1B
```bash
readgssi -i DZT__001.DZT -o 1b.png -p 5 -s auto -c viridis -g 50 -m -r -w
```
This will cause `readgssi` to create a plot from the same file, but matplotlib will save the plot as "1b.png" (`-o 1b.png`). The script will plot the y-axis size (`-p 5`) and automatically stack the x-axis to (`-s auto`). The script will plot the data with a gain value of 50 (`-g 50`), which will increase the plot contrast by a factor of 50. The `-m` flag will draw a histogram for each data channel. Finally, `readgssi` will run the background removal (`-r`) and dewow (`-w`) filters.
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
The script does the same thing, except it applies a background removal. Note the difference in ringing artifacts between examples 2a and 2b.
![Example 2b](https://github.com/iannesbitt/readgssi/raw/master/examples/2b.png)


## contributors
- Ian Nesbitt ([@iannesbitt](https://github.com/iannesbitt), author)
- Francois-Xavier Simon ([@fxsimon](https://github.com/fxsimon))
- Thomas Paulin ([@thomaspaulin](https://github.com/thomaspaulin))

### citation suggestion:
Ian M. Nesbitt, Francois-Xavier Simon, Thomas Paulin, 2018. readgssi - an open-source tool to read and plot GSSI ground-penetrating radar data. [doi:10.5281/zenodo.1439119](https://dx.doi.org/10.5281/zenodo.1439119)

## changes since 0.0.6
- added ability to install via PyPI
- broke out several routines into individual functions

## changes since 0.0.5
- now define time zero point manually (time zero is when the direct wave passes the receiver. previously, i used an unreliable calculation using header values to determine the time zero point)
  - in the future, i will add a signal processing algorithm to detect the time zero point automatically
- added bandpass filter (requires [obspy](https://obspy.org/))
- significantly optimized background removal and dewow algorithms
- added example code and plots
- fixed a bug that caused both plots of dual-channel radar files to be written out to one file
- fixed a bug that caused manually-created output file names to be ignored when plotting
- added basic background removal and dewow capability ([#5](https://github.com/iannesbitt/readgssi/pull/5) from [@fxsimon](https://github.com/fxsimon))
- added support for the D50800/D50300 antenna
  - added plotting support for dual-channel radar devices
  - merged [#3](https://github.com/iannesbitt/readgssi/pull/3) from [@fxsimon](https://github.com/fxsimon) which fixed a bug that caused multi-channel file traces to be read in a 121212 sequence instead of 111222
- updated the workings of the plotting algorithm's colormap
- changed the way files are saved (bug in 0.0.5 mangled some filenames)
- added the ability to specify colormap and whether to draw a colorbar and a histogram
- added an automatic figsize option (leaves figsize up to Matplotlib)
- added ability to apply gain
- fixed bug that caused gain to be applied incorrectly
- script now tries to automatically calculate timezero using (nsamp\*range)/position
#### known bugs:
- translation to anything but csv is broken (hope to have time to at least fix HDF5 output soon)
  - csv translation does not work for dual-channel radar devices (exports to file but channels are merged end-to-end)
- color bar shows up too large on some plots (no known fix yet)
- dewow doesn't work on all files
- histogram only shows pre-gain data distribution

## future
- GPS transcription (read from associated DZG file or CSV with fields like `mark name, lon, lat, elev, time`)
- interactive geologic/dilectric layer picking, layer velocity calculation (using minimum of clustered hyperbola tail angle measurements, or manual input), velocity-based depth adjustments, velocity gradient/angle of incidence-based array migration
- supplementing a flag indicating geophysical format (HDF5, SEGY, etc.) will write to that format
- break parts of script out into independent functions and supporting python files
