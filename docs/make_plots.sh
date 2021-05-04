#!/bin/bash

indir="../testing"
outdir="_static"
plot_ex0="DZT__001.DZT"
process_ex1="DZT__001.DZT"
process_ex2="DZT__001.DZT"
process_ex3="DZT__001.DZT"
process_ex4="DZT__001.DZT"

# example 0a - simple
readgssi -i $indir/$plot_ex0 -o $outdir/0a.png -n -Z 233 -p 5
# 0b - stack and gain
readgssi -i $indir/$plot_ex0 -o $outdir/0b.png -n -Z 233 -p 5 -s auto -g 60
# 0c - stack, gain, and Z axis
readgssi -i $indir/$plot_ex0 -o $outdir/0c.png -n -Z 233 -p 5 -s auto -g 60 -z m -E 80
# 0d - stack, gain, z-axis, and titleoff
readgssi -i $indir/$plot_ex0 -o $outdir/0d.png -n -Z 233 -p 5 -s auto -g 60 -z m -E 80 -T -D 300 -r 75 -t 70-130
# 0d - stack, gain, z-axis, titleoff, and colormap
readgssi -i $indir/$plot_ex0 -o $outdir/0e.png -n -Z 233 -p 5 -s auto -g 60 -z m -E 80 -T -D 300 -r 75 -t 70-130 -c seismic


# example 1a - autostacking
readgssi -i $indir/$process_ex1 -o $outdir/1a.png -n -Z 233 -p 5 -g 60 -s auto
# example 1b - stacking number of times
readgssi -i $indir/$process_ex1 -o $outdir/1b.png -n -Z 233 -p 5 -g 60 -s 3
# example 2a - full-width BGR
readgssi -i $indir/$process_ex2 -o $outdir/2a.png -n -Z 233 -p 5 -s auto -g 60 -r 0
# example 2b - moving window BGR
readgssi -i $indir/$process_ex2 -o $outdir/2b.png -n -Z 233 -p 5 -s auto -g 60 -r 100
# example 2c - vertical triangular bandpass
readgssi -i $indir/$process_ex2 -o $outdir/2c.png -n -Z 233 -p 5 -s auto -g 60 -t 70-130
# example 2d - combining filters
readgssi -i $indir/$process_ex2 -o $outdir/2d.png -n -Z 233 -p 5 -s auto -g 60 -D 300 -r 100 -t 70-130
# example 3a - distance normalization
readgssi -i $indir/$process_ex3 -o $outdir/3a.png -n -Z 233 -p 5 -s auto -g 60 -N -x m
# example 3b - reversing
readgssi -i $indir/$process_ex4 -o $outdir/4a.png -n -Z 233 -p 5 -s auto -g 60 -R
