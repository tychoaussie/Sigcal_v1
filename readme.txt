Sigcal_v1
=========

Calibration software for electromechanical seismometers retrofitted with laser position sensors
that track mass motion and relate it to ground motion. 
Works with Symmetric Research CSV files, along with SAC files, CSS,
and Miniseed files.
IMPORTANT SCRIPTS: Located in the subdirectory sigscript. They are
generally launched with the included BATCH file. You must include in
your system path the location of the folder containing these scripts
if you want them to run from any current working directory.

Script descriptions:
Sigcal.py - The main processing algorithm that runs through the csv files to assemble the cal curve
calcontrol.py - A step-through code to assemble the calibration constants text file used by Sigcal
cal2sacpz.py - An advanced subroutine from sigcal for regenerating sac to pz files with optional features
dampingratio.py - analyzes a datafile containing impulse events to calculate the damping ratio of seismometer
dat2sac.py - batch converts symmetric research data files into a
sigcal compatable SAC format
displaycal.py - uses the sigcal file output to plot the calibration curve
displaycsv.py - displays a single csv file for visualization of the time-history data within
displaysac.py - displays either sac, miniseed, or CSS file waveforms
but only the first channel in the stream.
freeperiod.py - calculates the free period of an undamped oscillation within the csv file
==========

Basic procedure:
1) Ensure the ADC channels of the digitizer are calibrated in microvolts / count
2) Ensure the laser position sensor is calibrated in terms of microns / millivolt
3) Ensure that the calibration constant for the particular seismometer is known. 
   This is the ratio between the laser pickup point and the center of pendulum mass in relation to fulcrum.
4) Create the calibration constants text file, except for the free period and damping ratio
5) Collect the calibration data with a series of sin sweeps from 0.1 Hz to 10 Hz, 1 file per frequency
6) Parse the data files into the appropriate directories
7) Collect the free period data and the damping ratio data
8) convert the data with dat2sac.py if necessary
9) run freeperiod.py to measure free period and record the value.
10) run dampingratio.py to measure damping ratio and record the value.
11) run calcontrol.py and enter all constants into the control file
        including damping ratio and resonance frequency.
11) Edit the calcontrol.cal file and ensure all values are correct.
12) run sigcal.py to analyze the frequencies, determine ratio of coil voltage to laser displacement on the mass,
    and use it to determine the calibration curve over the whole frequency range. Sigcal will also "best-fit" the
    curve and create a SAC poles & zeros file using a grid-search algorithm to finding amplitude, best free-period, and
    best damping ratio that describes the data.