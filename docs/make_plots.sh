#!/bin/bash

header=DZT__001.DZT
process_ex1=DZT__001.DZT
process_ex2=DZT__002.DZT
process_ex3=DZT__003.DZT
#process_ex4=DZT__001.DZT

indir=../testing
outdir=../examples

## display
# example 1a - simple without gain
readgssi -i $indir/$process_ex1 -o $outdir/1a.png -n -Z 233 -p 5 -s auto
# 1b - with gain and bgr 75
readgssi -i $indir/$process_ex1 -o $outdir/1b.png -n -Z 233 -p 5 -s auto -g 60 -r 75
# 1c - stack, gain, and Z axis
readgssi -i $indir/$process_ex1 -o $outdir/1c.png -n -Z 233 -p 5 -s auto -g 60 -r 75 -z m -E 80
# 1d - stack, gain, z-axis, and titleoff
readgssi -i $indir/$process_ex1 -o $outdir/1d.png -n -Z 233 -p 5 -s auto -g 60 -r 75 -z m -E 80 -T -D 300
# 1e - stack, gain, z-axis, titleoff, and colormap
readgssi -i $indir/$process_ex1 -o $outdir/1e.png -n -Z 233 -p 5 -s auto -g 20 -r 75 -z m -E 80 -c seismic
# 1f - vertical gradient absval with fir
readgssi -i $indir/$process_ex1 -o $outdir/1f.png -n -Z 233 -p 5 -s auto -g 100 -r 75 -z m -E 80 -c gray_r -A -t 80-120

# example 1g - autostacking
#readgssi -i $indir/$process_ex1 -o $outdir/1f.png -n -Z 233 -p 5 -g 60 -s auto
# example 1h - stacking number of times
#readgssi -i $indir/$process_ex1 -o $outdir/1g.png -n -Z 233 -p 5 -g 60 -s 3

## filtering
# example 2a - no BGR
readgssi -i $indir/$process_ex2 -o $outdir/2a.png -n -m -Z 233 -p 5 -s auto -g 30
# example 2b - full-width BGR
readgssi -i $indir/$process_ex2 -o $outdir/2b.png -n -m -Z 233 -p 5 -s auto -g 30 -r 0
# example 2c - moving window BGR
readgssi -i $indir/$process_ex2 -o $outdir/2c.png -n -m -Z 233 -p 5 -s auto -g 30 -r 75
# example 2d - vertical triangular bandpass
readgssi -i $indir/$process_ex2 -o $outdir/2d.png -n -m -Z 233 -p 5 -s auto -g 30 -t 80-120
# example 2e - combining filters
readgssi -i $indir/$process_ex2 -o $outdir/2e.png -n -m -Z 233 -p 5 -s auto -g 30 -D 300 -r 75 -t 60-100

## array manipulation
# example 3a - no distance normalization
readgssi -i $indir/$process_ex3 -o $outdir/3a.png -n -Z 233 -p 5 -s auto -g 60 -x m
# example 3b - distance normalization
readgssi -i $indir/$process_ex3 -o $outdir/3b.png -n -Z 233 -p 5 -s auto -g 60 -N -x m
# example 3c - reversing
readgssi -i $indir/$process_ex3 -o $outdir/3c.png -n -Z 233 -p 5 -s auto -g 60 -N -x m -R

## Header image
readgssi -i $indir/$header -o $outdir/main.png -n -Z 233 -N -p 7 -s auto -g 20 -r 75 -c seismic -x m -e 320,880,1200,500
mv $outdir/mainZ.320.880.1300.500.png $outdir/main.png
