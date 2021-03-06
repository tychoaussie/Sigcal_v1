__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20140724"
__license__ = "MIT"

import os, sys, csv
from scipy import signal
from scipy.integrate import simps
import pylab as plt
import numpy as np
import scipy as sp
import time, string
                                           # from obspy.core import read, Trace, Stream, UTCDateTime
                                           # from obspy.sac import SacIO

# Now, the most important part -- The legalese:
# COPYRIGHT �  BOARD OF TRUSTEES OF MICHIGAN STATE UNIVERSITY
# ALL RIGHTS RESERVED

# PERMISSION IS GRANTED TO USE, COPY, COMBINE AND/OR MERGE, CREATE DERIVATIVE
# WORKS AND REDISTRIBUTE THIS SOFTWARE AND SUCH DERIVATIVE WORKS FOR ANY PURPOSE,
# SO LONG AS THE NAME OF MICHIGAN STATE UNIVERSITY IS NOT USED IN ANY ADVERTISING
# OR PUBLICITY PERTAINING TO THE USE OR DISTRIBUTION OF THIS SOFTWARE WITHOUT 
# SPECIFIC, WRITTEN PRIOR AUTHORIZATION.  IF THE ABOVE COPYRIGHT NOTICE OR ANY
# OTHER IDENTIFICATION OF MICHIGAN STATE UNIVERSITY IS INCLUDED IN ANY COPY OF 
# ANY PORTION OF THIS SOFTWARE, THEN THE DISCLAIMER BELOW MUST ALSO BE INCLUDED.

# THIS SOFTWARE IS PROVIDED AS IS, WITHOUT REPRESENTATION FROM MICHIGAN STATE
# UNIVERSITY AS TO ITS FITNESS FOR ANY PURPOSE, AND WITHOUT WARRANTY BY MICHIGAN
# STATE UNIVERSITY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
# LIMITATION THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE.

# THE MICHIGAN STATE UNIVERSITY BOARD OF TRUSTEES SHALL NOT BE LIABLE FOR ANY
# DAMAGES, INCLUDING SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES,
# WITH RESPECT TO ANY CLAIM ARISING OUT OF OR IN CONNECTION WITH THE USE OF
# THE SOFTWARE, EVEN IF IT HAS BEEN OR IS HEREAFTER ADVISED OF THE POSSIBILITY
# OF SUCH DAMAGES.

class Sigcal(object):
    '''Sigcal is a utility for converting ascii files generated by 
       the 2010 version of DAT2ASC's csv output that represent a series of sinusoidal
       signals which were excited by a calibration coil and recorded simultaneously
       on the seismometer velocity coil and with a laser position sensor that tracks
       actual movement of the seismometer mass. By comparing the seismometer signal
       to the laser position, it is possible to determine the sensitivity at that 
       frequency. This program takes a series of files representing frequencies across
       the instrument passband and uses them to create a calibration response curve.
       There are some initial constants that are required in order to process these
       files. They are found within the file called 'calconst.cal' which is invoked
       by this program. This file should exist within the parent directory that
       also contains all the csv files. 
        

       Syntax: Sigcal target_directory (outfile_name) (calconst.cal_alternate_name) 

       

       Typical useage:
       <ObsPy> C:\Python27\scripts> python Sigcal.py c:/calibration/station/ [outfputfile] [calconstfile]

    '''




                                   #                       Function load:
 
                                   # load the csv infile as generated by DAT2ASC with csv option
def load(infile):                                    
    with open(infile,'r') as fin:
        list = csv.reader(fin)
        rowcnt=0
        stack = []
        header = []
        for row in list:           # Bring in the data and create a list of lists, each of which                                  
            if rowcnt == 0:        # corresponds with a given sample.
                header.append(row)
            else:
                stack.append(row)
            rowcnt = 1
    return (header,stack)





                                   #                       Function getconstants:

def getconstants(calcontrol):      # From calcontrol file, retrieve the list of constants 
    constants = load(calcontrol)   # that relate these measurements to the real world.
    constant = constants[1][0]        # constants[0] contains headers that we don't really use
                                   # constant[0] = (text) Station: 'station name'
                                   # constant[1] = (float) adccal[0]: cal constant for ch 0 (microvolts / count)
                                   # constant[2] = (float) adccal[1]: cal constant for ch 1 (microvolts / count)
                                   # constant[3] = (float) adccal[2]: cal constant for ch 2 (microvolts / count)
                                   # constant[4] = (float) adccal[3]: cal constant for ch 3 (microvolts / count)
                                   # constant[5] = (float) laserres: cal constant for the laser ( mV / micron)
                                   # constant[6] = (float) lcalconst: cal constant for geometry correction factor
                                   # constant[7] = (float) h: Damping ratio for the seismometer as measured by engineer.
                                   # constant[8] = (float) resfreq: Free period resonance freq. as measured by engineer.
    return(constant)

def plot_curve(Station,Frequencies,Sensitivities,Freeperiod,h):
    
 
    # prepare data points
    # plot it
    
    plt.loglog(Frequencies, Sensitivities, "*")     # "*" means draw asterisk instead of lines
    plt.xlabel("Free period = {0:.2f} Hz           Frequency in Hz              Damping Ratio = {1:.3f}".format(Freeperiod,h))
    plt.ylabel("Sensitivity in V/m/sec")
    plt.title("Sensitivity curve for station "+Station+" on "+time.asctime())
#    plt.annotate("Free period = {:.1f} Hz".format(Freeperiod), xy=(0.02,0.02),xytext=(0.02,0.02))
#    plt.annotate("Damping Ratio = {:.3f}".format(h), xy=(1,.02),xytext=(1,.02))
#    plt.annotate("* = sensitivity measurement points", xy=(10,5), xytext=(3,1),
#                 arrowprops=dict(facecolor='black',shrink=0.05))

    plt.show()




                                      #                    Function process:

def process(infile,outfile,calfile):

    fdata = load(infile)     # Load the current infile
    header = fdata[0]
    adccal = [1.0,1.0,1.0,1.0]

    constant = getconstants(calfile)         # Retrieve the constants from the file

    Station = constant[0]                    # Name of Station under test
    for i in range(0,4):
        adccal[i] = float(constant[i+1])     # Calibration constants for the ADC channels as measured by engineer
                                             # for this particular system. Each one is unique.
    laserres = float(constant[5])            # CALIBRATED value from laser position sensor in mV/micron
    lcalconst = float(constant[6])           # Typ. 1.022, for the SM3, based on the geometry of the laser target 
                                             # and center of coil relative to radius of moment arm
    h = float(constant[7])                   # typically about 0.7 but MUST be accurately measured beforehand!
    resfreq = float(constant[8])             # Typically between 0.7 and 1.3 Hz. Expressed in Hz, not seconds.
    Rn = (np.pi * 2.0 * resfreq)             # Free period as expressed in radians / second                      
    lasercal = laserres/1000                 # microns / count from the CALIBRATED laser and CALIBRATED ADC.

                                             # Parse out the sensor and laser data
    sensor = [] 
    laser = []
    for i in range(0,len(fdata[1])):
        sensor.append(int(fdata[1][i][1], base=10))
        laser.append(int(fdata[1][i][4], base=10))

                                             # Calculate the sample period based on the timing channels (in seconds)

    delta = ((float(fdata[1][len(fdata[1])-1][12])+float(fdata[1][len(fdata[1])-1][15]))-(float(fdata[1][0][12])+float(fdata[1][0][15])))/len(fdata[1])

                                      #            
                                      # Find the period of the observed signal
                                      #
    sense = signal.detrend(sensor)
    N = len(sense)
    W    = np.fft.fft(sense)
    freq = np.fft.fftfreq(len(sense),delta) # First value represents the number of samples and delta is the sample rate

                                      #
                                      # Take the sample with the largest amplitude as our center frequency. 
                                      # This only works if the signal is heavily sinusoidal and stationary 
                                      # in nature, like our calibration data.
                                      #

    idx = np.where(abs(W)==max(np.abs(W)))[0][-1]
    Frequency = abs(freq[idx]) # Frequency in Hz
    period = 1/(Frequency*delta) # represents the number of samples for one cycle of the test signal.
    gmcorrect = (2*np.pi*Frequency)**2/np.sqrt((Rn**2-(2*np.pi*Frequency)**2)**2+(4*h**2*(2*np.pi*Frequency)**2*Rn**2))

                                      #
                                      # create an axis representing time.
                                      #

    dt = [] # Create an x axis that represents elapsed time in seconds. delta = seconds per sample, i represents sample count
    for i in range(0,len(sensor)):
        dt.append(i*delta)

                                      # gmcorrect is the correction factor for observed pendulum motion 
                                      # vs true ground motion.
                                      # 
                                      #
                                      # At this point, we know the frequency interval, the delta, and we have the arrays 
                                      # for signal and laser. We can now piecewise adjust the signals for a 3* their period 
                                      # for DC offset. Adjust sensor and laser for linear trend removal, then apply an 
                                      # optional filter. Then apply calibration constants to yield units of microvolts 
                                      # for sensor, and units of microns for the laser position sensor.
                                      #
                                      # Next, calculate the integral of the sensor, and the derivative of the laser position 
                                      # sensor. Take the average of laser/intsensor and sensor/derivlaser to arrive at
                                      # the sensitivity of the coil.

    # print 'Frequency calcuated to ',Frequency,' Hz.' 

                                      #
                                      # piece-wise Linear Trend Removal for sensor and laser
                                      #
                                      # From point 0 to n periods, use the average of first n periods.
                                      # Hold average for last n periods of signal
                                      #

    pintv = 3                         # number of cycles to average for sliding linear trend removal
    sensor2 = []
    laser2 = []
                                      # period is the number of samples that represent one cycle of the signal:

    for i in range(0,len(sensor)-pintv*int(period)): 
        senavg = np.mean(sensor[i:i+pintv*int(period)])
        lasavg = np.mean(laser[i:i+pintv*int(period)])
        sensor2.append(sensor[i]-senavg)
        laser2.append(laser[i]-lasavg)

    for i in range(len(sensor)-pintv*int(period),len(sensor)): # Last n periods use a static mean. 
        sensor2.append(sensor[i]-senavg)
        laser2.append(laser[i]-lasavg)
    laser2 = sp.signal.detrend(laser2,type='constant')
    sensor2 = sp.signal.detrend(sensor2,type='constant')

                                      # Apply the calibration constants
                                      # Input represents counts of the ADC. 
                                      # The sensor is likely velocity in microvolts per micron/second.
                                      # Sensor(counts/micron/sec) * adccal (microvolts/count )
                                      # Laser requires conversion from counts to microvolts/count, to millivolts.micron 
                                      # then to ground motion corrected microns.
                                      #
                                      # sensor3 = sensor in terms of microvolts / microns/sec * unknown cal factor
                                      # laser3 in terms of known microns of ground motion

    sensor3 = adccal[0]*np.array(sensor2) 
    laser3 = adccal[3]*lasercal*lcalconst/gmcorrect*np.array(laser2)

                                      # Now calculate the integral of the sensor and the derivative of ground motion
                                      # Integral limits of integration: time from zero to end of the record
                                      # integral of sensor over limits of zero to t, of Ydx
                                      # The function is Ydx area = base * height, where height = Y and base = delta

                                      # Integrate the sensor to yield microvolt/microns * our as-of-yet unknown constant
                                      #    
   

    intsensor = []
    for i in range(1,len(sensor3)+1):
        intsensor.append(simps(sensor3[0:i],dt[0:i]))

    intsensor = sp.signal.detrend(intsensor,type='linear')
 
                                      # Remove the mean to remove DC offset type = 
                                      # This signal represents the peak-peak voltage signal representing 
                                      # the sensor response to ground motion at the given frequency.

    derlaser = []
    derlaser.append(((laser3[0]-laser3[1])*-1)/delta)

                                      #
                                      # Calculate the derivative of the laser position sensor 
                                      # (how fast position is changing)
    derlaser = []
    derlaser.append(((laser3[0]-laser3[1])*-1)/delta)
    for i in range(1,len(laser3)-1):
        derlaser.append(((laser3[i-1]+3*laser3[i]+laser3[i+1])/5-laser3[i-1])/delta)
    derlaser.append(((laser3[i]+3*laser3[i+1])/4-laser3[i])/delta)
    derlaser = sp.signal.detrend(derlaser,type='linear')

                                      #
                                      # Calculate the calibration ratios using a total rms of each signal.
                                      #

    cal1 = (np.std(intsensor)/np.std(laser3)) # Calibration constant as calculated via integration of sensor
    cal2 = (np.std(sensor3)/np.std(derlaser)) # Calibration constant as calculated via derivative of ground motion
    ccal = (cal1+cal2)/2 # This is the calibration constant at this frequency in uV/micron/sec, which is also V/M/sec
    confidence = (1-cal1/cal2)*100    # degree of correlation between the two separate calculation methods
                                      #
                                      # ccal represents the cal constant as determined by both calculation methods.
                                      #

    print("ccal (int/dev deviation={0:.1f} %) calculates to: {1:.3f} for frequency {2:.1f} Hz".format(confidence,ccal,Frequency))

                                      #
                                      #     Calculate the phase difference between input signal and the response
                                      #     not yet implemented
    phase = 0.0

                                      #
                                      #     Output the results to an output file
                                      #     Field 1: Frequency = Frequency (float)
                                      #     Field 2: ccal = Sensor response in V/m/sec
                                      #     Field 3: confidence = confidence in percentage between the two calculation methods.
                                      #     Field 4: phase = Phase difference between the cal coil drive signal and the output
                                      #     Field 5:Name of input file (text)
                                      #
    if (np.abs(confidence) < 15.0):             #
        with open(outfile,'a') as csvfile: # use 'wb' in place of 'a' if you want to overwrite the file.
            outrow = csv.writer(csvfile, delimiter = ",",
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            outrow.writerow([Frequency,ccal,confidence,phase,infile])
    else:
        print("ccal uncertainty is greater than 15% deviation so frequency {:.1f} Hz will not be written to file.".format(Frequency))                                  #
                                      #    
                                      

#######################################################################################



def main():
                                      #           MAIN PROGRAM BODY
                                      #  Parse the command line switches
                                      # Commmand example: c:\Python27>Python.exe Sigcal.py c:\seismo\caldata\momo
                                      # where momo is the working directory containing the csv files
                                      # as well as the calibration control file, c:\seismo\caldta\calcontrol.csv
                                      # The third option can designate an optional location for the calcontrol file.
                                      #
    optioncount = len(sys.argv)
    outputfile_defined = False
    filelist = []
    dir=""
    infile = ""
    outfile = os.getcwd()+"\calibration_output.cal"
    calfile = os.getcwd()+"\calcontrol.cal"

    if optioncount > 1:

        if optioncount == 4:
            outfile = sys.argv[2]                          # Assume that output file has been designated            

            if '.csv' in sys.argv[3]:                      # If there is a calcontrol set, use it.
                calfile = sys.argv[3]
            else:
                calfile = sys.argv[3]+"\calcontrol.cal" # Assume they pointed at a directory.
            
            if "." in sys.argv[1]:                         
                infile = sys.argv[1]
                filelist.append(infile)
            else:                
                filelist = os.listdir(sys.argv[1])

        if optioncount == 3:                               # No calcontrol designator, but an output file is designated
            calfile = os.getcwd()+"\calcontrol.cal"     # Set the default cal control as current working directory.
            outfile = sys.argv[2]
            
            if "." in sys.argv[1]:                         # Set the input file 
                filelist.append(sys.argv[1])            
            else:
                filelist = os.listdir(sys.argv[1])
                
            
        if optioncount == 2:
            calfile = os.getcwd()+"\calcontrol.cal"
            outfile = os.getcwd()+"\calibration_output.cal"

            if "." in sys.argv[1]:
                infile = sys.argv[1]
                filelist.append(infile)
                
            else:
                filelist = os.listdir(sys.argv[1])
    else:
        filelist = os.listdir(os.getcwd())                 # No switches? No problem. Use the current working directory.
        
        print " Cal control file:",calfile
        constant = getconstants(calfile)
                                                           # 
                                                           # Create the header for the calibration output file.
                                                           # Header contains the station name, ADC cal constants,
                                                           # Laser cal constant, the geometric correction factor,
                                                           # the damping ratio, and the free period frequency.
                                                           #
 
#        with open(outfile,'wb') as csvfile: # use 'wb' in place of 'a' if you want to overwrite the file.
#            outrow = csv.writer(csvfile, delimiter = ",",
#                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
#            outrow.writerow(constant)
                                                           # Now loop through the directory of csv files to build the
                                                           # calibration curve.

#        for n in range(len(filelist)):                     # Parse through directory for all .csv files
#            if ".csv" in filelist[n]:                      # Skip any files that are not a .csv
#                infile = filelist[n]                       # Set the input file from the file listing if it is a .csv
#                print "Infile set to: ",infile
#                process(infile,outfile,calfile)            # Process the file and output to outfile based on parameters
                                                           # found in calcontrol

#    print("output sent to {} ".format(outfile))
    
                                                           #
                                                           # Now that the file has been created,
                                                           # Bring in the data and plot.                
    print "The name of the outfile is: '{}'".format(outfile)                                                           #
    fdata = load(outfile)
    header = fdata[0]                     # The header contains the initial constants used for creation of the datafile
                                          # and includes the damping ratio, free period frequency, and channel calibration information
                                          # in this order:
    Station = fdata[0][0][0]              # Station name
                                          # fdata[0][0][1] # Channel 0 ADC sensitivity in microvolts / count
                                          # fdata[0][0][2] # Channel 1
                                          # fdata[0][0][3] # Channel 2
                                          # fdata[0][0][4] # Channel 3
                                          # fdata[0][0][5] # Laser position sensor in millivolts/micron
                                          # fdata[0][0][6] # Lcalconstant geometry correction factor
    h = float(fdata[0][0][11])             # h damping ratio
    Freeperiod = float(fdata[0][0][12])    # Free period oscillation in Hz  
    Frequencies = []
    Sensitivities = []
    for i in range(0,len(fdata[1])):      #        Build the list of frequencies and sensitivities from the file.
        Frequencies.append(float(fdata[1][i][0]))
        Sensitivities.append(float(fdata[1][i][1]))
    plot_curve(Station,Frequencies,Sensitivities,Freeperiod,h)



#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()