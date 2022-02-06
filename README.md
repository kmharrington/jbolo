## Overview
*jbolo* is a tool for simulating the optical loading and noise properties of bolometers.
It is largely derived from the original BoloCalc (https://github.com/chill90/BoloCalc), written by Charlie Hill,
and bolo-calc (https://github.com/KIPAC/bolo-calc), an adaptation of BoloCalc written by Eric Charles that introduced
the convenience of yaml files to set up an "experiment".  

I've tried to arrange
jbolo so that it is easy to look inside the calculation and extract a lot of information
that was difficult for me to get at in the previous versions.  I've also tried to make it easier
to use in non-standard configurations like "in the lab looking at a blackbody",
or "I only want to run the dark detector calculations with no optics", etc.

The basic idea behind jbolo is that we read in a yaml file describing the experiment,
sticking the whole thing in a dictionary structure called "sim".  Things that are
calculated from then on are stuffed into the sim['outputs'] dictionary.  I try to save
as much as can possibly be useful along the way, so that in the end the "sim" dictionary
contains all the inputs as well as the outputs, in one big dictionary structure.  Some of the saved things, like optical efficiency of a particular element or the whole system, are saved as frequency-dependent numpy vectors.
The sim dictionary can
then be saved to a pickle file for later use.

Experiment yaml file examples are in the jbolos/yamls/ subdirectory.  The yaml
file describes the sources (like CMB and atmosphere) of radiation entering the optics,
the optics themselves (losses, temperatures, etc), and the detector parameters.

The python code driving jbolo lives in the python/ subdirectory.  The files there are:
- physics.py  This is mostly copied from the original BoloCalc/bolo-calc, with some functions removed or simplified.
- jbolo_funcs.py  This has two main functions, "run_optics" and "run_bolo", as well as some helper functions for those and some reporting functions.  Typically one would "run_optics" to find the photon-related properties (optical power, photon noise, etc), then "run_bolo" to calculate detector NEPs, NETs, etc.  However, one could just use one of those routines without the other if you want to streamline calculations for some other purpose.
- RunOnce.py  This is a python script that reads a yaml file, calls run_optics, then run_bolo, then prints some useful information.  It can be run from the command line (with the yaml filename as an argument), and will save the sim to a pickle file if you use the relevant keyword argument.  This is (for me) the typical way jbolo is run.

Two python jupyter notebooks of interest are in the top-level directory.
- Jbolo_nb.ipynb shows a simple case of using RunOnce.py, and prints some optics info from one channel.
- Jbolo_vary1.ipynb shows an example of how to:
 - read in a yaml file
 - run_optics and run_bolo once to find psats if needed,
 - then loop as you change some parameter in the sim dictionary structure, recalculating and saving Poptical and NET each time through the loop.  In this case we clear the sim dictionary every time though the loop, discarding everything but the parameters of interest.


## Setup/Configuration

You'll need to set things up so that your sys.path can find the jbolo/python directory.  

For example, on my mac running anaconda python, I insert it in

    ~/.ipython/profile_default/ipython_config.py
    ## lines of code to run at IPython startup.
    c.InteractiveShellApp.exec_lines = [
      "sys.path.append('/path/to/jbolo/python')"
      ]

Or, you can use the following line (modified for your installation) in every notebook you use this stuff in:

    sys.path.insert(0,'/path/to/jbolo/python/')

There are some Aperture function pickle files required to calcualate the horn-horn correlation factors.  Those live in jbolo/ApertureFuncs, and at this point you need to run your python scripts from the jbolo/ directory in order for the relevant physics.py function to find them.

An hdf5 file containing a grid of atmospheric mission vs (frequency, pwv, elevation) is in jbolo/atmos/atm_20201217.hdf5.  The yaml file needs to
point to that file in the relevant spot (see example).

I suggest (but it is not required) that output files go in jbolo/outputs.


## Things that will come "soon":
Here are some things that are missing that I expect to add in the not-too-distant future:
- Johnson noise
- Readout noise from a specified NEI
- band files for reflections and absorption
- read atmos file from am output rather than the hdf5 file.
- Loop gain (given alpha).

## Differences with BoloCalc/bolo-calc
jbolo differs from BoloCalc/bolo-calc in a few ways that make real numerical
differences:
- bolo-calc implements absorption, reflection, scattering as though they are
 elements in "series", ie T = (1-R)*(1-A)*(1-S), rather than imposing T+R+A+S = 1.  
 jbolo does the latter, which I believe is more in line with in-lab measurement
 practice.  This leads to small differences in the calculated
 optical efficiency and loadings.
