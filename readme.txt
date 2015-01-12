Sigcal_v1
=========

Calibration software for Russian seismometers retrofitted with laser position sensors. 
Works with csv files representing the ADC output in counts.
IMPORTANT SCRIPTS: Located in the subdirectory sigscript.

Script descriptions:
Sigcal.py - The main processing algorithm that runs through the csv files to assemble the cal curve
build_calconst.py - A step-through code to assemble the calibration constants text file used by Sigcal
cal2sacpz.py - An advanced subroutine from sigcal for regenerating sac to pz files with optional features
calconst.py- Creates the calcontrol file based on the user prompts, similar to build_calconst.py
dampingratio.py - analyzes a csv containing impulse events to calculate the damping ratio of seismometer
dat2csv.py - batch converts symmetric research data files into a sigcal compatable .csv file format
displaycal.py - uses the sigcal file output to plot the calibration curve
displaycsv.py - displays a single csv file for visualization of the time-history data within
freeperiod.py - calculates the free period of an undamped oscillation within the csv file
grid_search.py - Subroutine used by sigcal to create a 'best-fit' poles and zeros SAC file
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
8) convert the data with dat2csv.py
9) run freeperiod.py to measure free period and place value into cal constants text file
10) run dampingratio.py to measure damping ratio and place value into cal constants text file (calcontrol.cal)
11) Edit the calcontrol.cal file and ensure all values are correct
12) run sigcal.py to analyze the frequencies, determine ratio of coil voltage to laser displacement on the mass,
    and use it to determine the calibration curve over the whole frequency range. Sigcal will also "best-fit" the
    curve and create a SAC poles & zeros file using a grid-search algorithm to finding amplitude, best free-period, and
    best damping ratio that describes the data.