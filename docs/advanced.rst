Advanced usage with bash
##############################

.. role:: bash(code)
   :language: bash

UNIX users have a distinct advantage of being able to easily process entire folders full of DZTs with a simple command. Users who wish to do this should `read up <https://linuxize.com/post/bash-for-loop/>`_ on how to construct for loops in Bash or simply follow and modify these examples below.

Processing all files in a folder
====================================

This command makes use of the :bash:`ls` function in Bash, which lists all files that match a specific pattern. In this case, we want the pattern to be "any DZT file," which ends up being simply :bash:`ls *.DZT` (the :bash:`*` symbol is a wildcard, meaning it matches any set of characters, so in this case it would match both :bash:`FILE____005.DZT` and :bash:`test.DZT` but not :bash:`Test01.dzt` because the .DZT is case sensitive.).

.. code-block:: bash

	for f in `ls *.DZT`; do readgssi -p 8 -n -r 0 -g 40 -Z 233 -z ns -N -x m -s auto -i $f; done

The structure of this command is easy to understand if you know a little bit about :bash:`for` loops. This command loops over every file with the extension :bash:`.DZT` (:bash:`ls *.DZT` where :bash:`*` indicates a wildcard) and assigns the filename to the :bash:`f` variable on each loop. Then, after the semicolon, bash runs readgssi for every pass of the loop. In this case, the parameters are:

.. code-block:: bash

	-p 8    # plot with size 8
	-n      # suppress the matplotlib window; useful if you do not want the operation interrupted
	-r 0    # full-width background removal
	-g 40   # gain of 40
	-Z 233  # time zero at 233 samples
	-z ns   # display the depth axis in nanoseconds
	-N      # distance-normalize the profile
	-x m    # display the x-axis in meters
	-s auto # apply automatic stacking
	-i $f   # recall the `f` variable containing this loop's filename and feed it to the input flag of readgssi

Finally, end the loop by closing the command with a linebreak :bash:`;`, and the :bash:`done` marker.


Processing specific subsets of files
=======================================

You can make the command even more specific by further modifying the set of files returned by the :bash:`ls` command. For example:

.. code-block:: bash

	for f in `ls FILE__{010..025}.DZT`; do readgssi -p 8 -n -r 0 -g 40 -Z 233 -z ns -N -x m -s auto -i $f; done

This command will process only the 16 files in the numeric sequence between and including 010 and 025 in the set (:bash:`FILE__010.DZT`, :bash:`FILE__011.DZT`, :bash:`...`, :bash:`FILE__025.DZT`). :bash:`bash` handles the zero padding for you as well. Pretty cool.
