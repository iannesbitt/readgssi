# Changelog

## changes since 0.0.18
- fixed a problem that led to errors creating a conda skeleton
- explicitly specify base _e_ (`numpy.e`) in `SymLogNorm` call in `readgssi:plot.radargram`
- added the ability to output to any supported matplotlib format
- fixed `docs/make_plots.sh` and branched a `docs/make_readme_plots.sh` for README figure creation
- corrected docs text and `docs/_static` images that incorrectly applied FIR and BGR (or didn't apply them at all)
- added an example plot demonstrating the absolute value of gradient (`-A -c gray_r`) method

## changes since 0.0.17
- fixed the read of the byte that contains `rh_system` and `rh_version` in the header ([#26](https://github.com/iannesbitt/readgssi/issues/26))
- fixed sampling depth interpretation ([#28](https://github.com/iannesbitt/readgssi/issues/28))
- added DZT file output ([#29](https://github.com/iannesbitt/readgssi/pull/29))
- added documentation for displaying absolute value of down-trace gradient in plots
- fixed a bug that incorrectly displayed long axis units on stacked arrays
- added [conda installation method](https://readgssi.readthedocs.io/en/latest/installing.html#installing-from-anaconda-cloud) and streamlined installation documentation
- switched version handling to file (`_version.py`)
- fixed a bug that did not handle `rhf_depth == 0` cases correctly
- added support for the 3102 antenna (500 MHz)
- fixed a bug that incorrectly plotted TWTT
- updated examples in Readme and fixed the autogen script (`make_plots.sh`)
- corrected an error with how `setup.py` got the version number, which prevented the creation of a conda skeleton

## changes since 0.0.16
- merged [#19](https://github.com/iannesbitt/readgssi/pull/19) from [teshaw](https://github.com/teshaw) which allows the user to specify partial read parameters for DZT files
- reintroduced a testing feature which creates CSV files from DZG records, in order to easily import location information to GIS
- added support for the StructureScan Mini XT which suffered from the unfortunate fate of having an antenna named 'none'
- improved handling of multiple user-specified frequencies
- adding the ability to plot the absolute value of the down-trace gradient, which can increase faint layer visibility at the cost of wave front resolution
- now use `rf_top` to correct depths, a major bug in previous versions
- limited distance normalization console output to one message every ten chunks (in the future, this will be controlled with a \r statement)
- added pause correction function to fix DZG/DZT trace number offset when collection is paused and GPS is active
- added ability to plot user marks as vertical lines (similar to the output on the controller itself)
- corrected module call documentation for plotting ([#23](https://github.com/iannesbitt/readgssi/issues/23))

## changes since 0.0.15
- fixed [#14](https://github.com/iannesbitt/readgssi/issues/14) which incorrectly asserted that user-set samples per meter was negative when it was not (sign was flipped) but processed the file correctly regardless
- moved zoom calculation and automatic file naming to their own functions
- added sphinx autodoc descriptions to some functions, in order to work towards solving [#9](https://github.com/iannesbitt/readgssi/issues/9)
- added comments to datetime parsing function
- fixed sampling frequency calculations to the value of `epsr` set in the header, which will prevent perceived frequency wander in frequency-based filters if the user sets `epsr`
- changed the behavior of the readdzt script to automatically search for a DZG file of the same name, and load that data if possible. this should allow python users to read all three variables (header, arrays, gps) if GPS exists.
- fixed command line control of DPI
- switched to "gray" colormap from "Greys". "Greys" rendered opposite polarity [#18](https://github.com/iannesbitt/readgssi/issues/18)

## changes since 0.0.14
- added support for the 5103 400 MHz antenna, and an antenna called `CUSTOM` in the header, for which center frequency is not known but is likely adjustable
- added support for the 350 HS hyperstacking antenna
- fixed a bug that created an extra matplotlib axis
- added rounding to epsilon_r value on y-axis depth-type display
- added a patch for [#12](https://github.com/iannesbitt/readgssi/issues/12) to improve axis sizing and tight_layout() handling
- changed background removal (BGR) function to operate similar to RADAN boxcar function
  - this change means that you can no longer simply specify `-r` for full-width background removal. new nomenclature for full-width BGR flag is `-r 0`. `-r 100` will apply a 100-trace rolling boxcar BGR (after normalization and stacking)
  - this is done with the `scipy.ndimage.filters.uniform_filter1d()` function and means that `scipy` is now explicitly required
  - function will automatically filter out low-frequency washout noise caused by bgr, using obspy's implementation of scipy's butterworth bandpass from `0.1*f` to `10*f`, where `f` is antenna frequency. nyquist is automatically accounted for by obspy.
  - BGR value is displayed in title if set > 0, or as "full" if BGR is full-width (i.e. `-r 0`)
- added zerophase vertical triangular FIR filter, and changed default filter from butterworth to triangular to attempt to match that in RADAN. butterworth is no longer used (but kept for posterity).
  - this function uses the `scipy.signal.firwin()` filter design and `scipy.signal.lfilter()` implementation
- added ability to suppress plot title using `-T` or `--titleoff` from the command line or title=False in main python function
- changed `ns_per_zsample` in header to read data shape from header rather than array size
- added a bug fix for filtering that caused the sample rate to be set too high
- significantly improved triangular bandpass filter, so that it nearly matches RADAN
- when Z axis value is set to "samples", the zeroed samples are taken into account. so, if the array had 150 samples sliced off, the plot axis will now start at 150 instead of 0
- added per-channel handling of timezero. you can pass a list with `-Z 233,150,92` (or `zero=[233,150,92,None]` in python). defaults to `-Z 2` (`zero=[2,None,None,None]`)
- added programmable zoom with `-e left,right,up,down` flag and list
- cleaned up some dangling floats
- updated help text and README help text
- added automatic tight bbox axes for savefig
- changed from 150 to 300 dpi for easier poster printing measurements
- fixed calculation for two-way time (previously per [#17](https://github.com/iannesbitt/readgssi/issues/17), calculation erroneously displayed one-way time)

## changes since 0.0.13
- updated examples in README
- fixed [#16](https://github.com/iannesbitt/readgssi/issues/16) which incorrectly applied GPS array values for normalization

## changes since 0.0.12
- fixed [#13](https://github.com/iannesbitt/readgssi/issues/13) by adding `SS MINI` to list of recognized antenna codes
- fixed bug ([#15](https://github.com/iannesbitt/readgssi/issues/15)) which caused runaway memory usage when distance-normalizing large files. files are now distance normalized in chunks.
- fixed a bug that caused a read failure on DZG files with RMC strings before GGA (iat function didn't like my slicing)

## changes since 0.0.11
- fixed bug that prevented reading NMEA RMC-only DZG files. now fully compatible with DZGs created with [gpx2dzg](https://github.com/iannesbitt/gpx2dzg)
- added `-d` flag documentation to help text and readme
- updated docstring formatting
- added PyPI downloads badge
- added ability to manually set samples per meter using `-d <float>` flag
- added support and badge for travis-ci in anticipation of test suite
- `-V` or `--version` outputs version string
- fixed bug ([#10](https://github.com/iannesbitt/readgssi/issues/10)) which read NMEA GGA strings incorrectly from DZGs that don't contain NMEA RMC
- fixed bug ([#11](https://github.com/iannesbitt/readgssi/issues/11)) which prevented SIR-20 files with antenna code `GSSI` from being read correctly

## changes since 0.0.10
- addresses [#7](https://github.com/iannesbitt/readgssi/issues/7) to add support for DZT files created with gprMax 
- added explicit support several antenna codes specific to SIR-3000 units and before
- added the ability to label radargram axes with distance and time units
- created readthedocs support files in anticipation of more full documentation and a future stable version release

## changes since 0.0.9
- a patch was added that includes several important bug fixes
  - added support for the `400MHz` antenna type
  - fixed a bug that affected the stacking routine
  - fixed a bug with the time zero variable not being available when implementing the naming scheme
- fixed a bug with plotting that resulted from a key error in the header variable
- moved dzt reading-related functions to `dzt.py`
- changed tab spacing aesthetics in two plotting routines
- fixed a bug that caused errors reading multi-channel files
- script has more degrees of freedom while handling unknown antenna types
  - script should handle unknown antennas gracefully
  - script will try to extract frequency information from antenna name (harder than it sounds given GSSI naming inconsistency)
- added ability to reverse radargram (i.e. flip horizontal left to right)
- fixed bug with command line autostack
- changed command line verbose messages
- added ability to distance-normalize profile using GPS records
  - currently can read .DZG GPS records only, but plan to add ability to read .csv (lat, long, time) and NMEA GGA/RMC textfiles
- changed naming scheme to be "more readable"
  - changed filename differentiator from frequency to channel number (makes sense because theoretically, a user can have the same frequency antenna on two different channels, which would result in a naming conflict)
- fixed a bug in normalization caused by an errant format string
- stacking algorithm now uses reduce function to create copy array
- normalization will now automatically set traces per meter value of `header['rhf_spm']`
- added export numpy binary file (.npy)
- added header export to json
- added export to gprpy (.npy & .json) per [this discussion](https://github.com/NSGeophysics/GPRPy/issues/3)

## changes since 0.0.8
- moved plotting routines to new module `plot.py`
- moved translations to new module `translate.py`
- moved gps reading to new module `gps.py`
- moved geophysical and GSSI constants to new module `constants.py`
- moved stacking algorithm to `filtering.py`
- significantly improved layout of main processing function `readgssi.readgssi()`
  - script flow is *so much more natural now*
  - made way for future additions like interactive picking
- csv output improvements
  - added the ability to filter prior to csv export (duh?)
  - added the ability to export multiple csv files when more than one radar channel is present
- improved histogram plotting
- improved array handling when passing to functions
- changed the way files are named if no output file is passed (the Seth Campbell Honorary Naming Scheme)

## changes since 0.0.7
- moved filtering routines to new module `filtering.py`
- added a way to call `readgssi.__version__`
- moved some config stuff to `config.py`
- bitwise datetime read works properly now!! this was a longstanding bug that took me forever to figure out. the bit structure was not at all intuitive and the script kind of ends up using brute force to decode them to datetime objects, but it works. dates and times of file creation and modification should now match those in RADAN.
- changed to verbose by default and quiet if `-q` / `--quiet` flag is set
- changed print statement to output date and timestamp (helpful for tracking date and time of things when, for example, processing a whole survey data folder full of radar files)


## changes since 0.0.6
- added ability to install via PyPI
  - setuptools integrated command line script creation (i.e. `readgssi` instead of `python readgssi.py`)
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
