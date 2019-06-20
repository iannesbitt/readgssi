# Changelog

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
