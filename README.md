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
- utils.py contains utilities related to loading experiments and files
- RunOnce.py  This is a python script that reads a yaml file, calls run_optics, then run_bolo, then prints some useful information.  It can be run from the command line (with the yaml filename as an argument), and will save the sim to a pickle file if you use the relevant keyword argument.  This is (for me) the typical way jbolo is run.

Two python jupyter notebooks of interest are in the top-level directory.
- Jbolo_nb.ipynb shows a simple case of using RunOnce.py, and prints some optics info from one channel.
- Jbolo_vary1.ipynb shows an example of how to:
 - read in a yaml file
 - run_optics and run_bolo once to find psats if needed,
 - then loop as you change some parameter in the sim dictionary structure, recalculating and saving Poptical and NET each time through the loop.  In this case we clear the sim dictionary every time though the loop, discarding everything but the parameters of interest.


## Setup/Configuration

To install jbolo run this in the main directory:

    pip install . 

Two environment variables are used to define the locations of various supporting files used by this repository. These are the path to where you have this repo saved and the path to where all the instrument models are saved. 

The software uses `JBOLO_PATH` environmental variable to define the path to this repository. It assumes that you have the aperture functions and atmospheric source files saved in this repo under the structure

    /path/to/jbolo/
        ApertureFuncs
        atmos 

- The Aperture function pickle files are required to calcualate the horn-horn correlation factors.  
Those live in the jbolo/ApertureFuncs directory. The code will find them if you define
that environment variable;  your other option is to run things directly from your jbolo
directory, or make symlinks to the relevant places.
- The atmosphere files need to be downloaded or otherwise generated. You can download Charlie Hill's hdf5 file containing a grid of atmospheric mission 
vs (frequency, pwv, elevation) from http://pbfs.physics.berkeley.edu/BoloCalc/ATM/atm_20201217.hdf5
and put it in jbolo/atmos/atm_20201217.hdf5 .  You can either point to that file in the input yaml file, or not point to it and the code 
should find it if you've put it there.

The software uses the `MODELS_PATH` environmental variable to link to the base location for any band response files used in the instrument models for the optics and detector definitions. For example, if you have 

    /path/to/my_models/
        detectors/
            band1.txt
            band2.txt
        optics/
            lpe_1.txt
            alumia.txt

Then you can set `MODELS_PATH` to be `/path/to/my_models/` and then you only need `detectors/band1.txt` in your experiment definitions. This makes it easier to point jbolo at different repos of models for different experiments.

If you want to not have to think able these paths, add this to your `.bash_profile` or `.bashrc` file:

    export JBOLO_PATH=/path/to/jbolo/
    export MODELS_PATH=/path/to/models/


## Things that will come "soon":
Here are some things that are missing that I expect to add in the not-too-distant future:
- band files for reflections and absorption
- read atmos file from am output rather than the hdf5 file.

## Differences with BoloCalc/bolo-calc
jbolo differs from BoloCalc/bolo-calc in a few ways that make real numerical
differences:
- bolo-calc implements absorption, reflection, scattering as though they are
 elements in "series", ie T = (1-R)*(1-A)*(1-S), rather than imposing T+R+A+S = 1.  
 jbolo does the latter, which I believe is more in line with in-lab measurement
 practice.  This leads to small differences in the calculated
 optical efficiency and loadings.
