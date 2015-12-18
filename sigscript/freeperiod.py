__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20150721"
__license__ = "MIT"

# Repaired the file import to handle csv, sac, and css files

# Now, the most important part -- The legalese:
# COPYRIGHT  BOARD OF TRUSTEES OF MICHIGAN STATE UNIVERSITY
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

import os, sys, csv
from obspy import read
from scipy import signal
from scipy.integrate import simps
import pylab as plt
import numpy as np
import scipy as sp
import string


                                           # import time, string
                                           # from obspy.core import read, Trace, Stream, UTCDateTime
                                           # from obspy.sac import SacIO
class Freeperiod(object):
    '''Freeperiod is a utility for converting ascii files generated by 
       the 2010 version of DAT2ASC's csv output that represent a series of transient
       signals which were excited by a calibration coil and recorded simultaneously
       on the seismometer velocity coil and with a laser position sensor that tracks
       actual movement of the seismometer mass. There are two types of transients that
       this program is designed to process: A free-period oscillation in which the 
       damping coil has been disconnected, and a damping ratio measuremnet transient
       in which the damping coil is connected. Both transients will result in a decaying
       sinusoidal signal; This program will return a file with measurement of an average
       oscillation frequency, an average damping ratio representing the first three
       oscillations of the transient, followed by a table of measured periods until the
       peak oscillation drops below -18dB (12.5%) of the peak amplitude of the initial 
       peak transient.
       
        

       Syntax: freeperiod target_directory (outfile_name) (calconst.cal_alternate_name) 

       

       Typical useage:
       <ObsPy> C:\Python27\scripts> python freeperiod.py c:/calibration/station/filename filetype
       
       where, filetype is either: csv, sac, mseed, or css.
       Sac, Miniseed, and css files requires a wildcard in file name to import all related channels.

    '''

                                   #                       Function load:
 
                            # Function getcal: Retrieve the calibration control file
def getcal(calcontrol): 
    # calcontrol needs to include calibration constants as well as the station name and the channel name, and the particular constant for that channel.
    # Thus a third line is necessary that specifies the channel identifier and the channel assignment of that channel.
    # Channel name is located in the top row already, and it's position is associated with the sensitivity. So the third row designates the UUT and the
    # laser position channel.
    with open(calcontrol,'r') as fin:
        list = csv.reader(fin)
        rowcnt=0
        cconstant = ["","",1.0,"",1.0,"",1.0,"",1.0,1.0,1.0,1.0,1.0,2,3]
        stack = []
        header = []
        calconstants = []
        selection = []
        for row in list:
            stack.append(row)
        header = stack[0]
        calconstants = stack[1]
        if len(stack)==3:# old calibration file format, so prompt the user for the appropriate channel assignments.
            selection = stack[2]
        else:
            for i in range(0,4):
                print "\n\nNo channels selected for calibration in cal control file."
            for i in range(0,4):
                print"Note: Channel {0} is listed as channel number {1}".format(header[i+1],i)
        
            selection.append(int(raw_input('Choose the channel number for the unit under test:  ')))
            selection.append(int(raw_input('Choose the channel number for the laser position sensor:  ')))

        cconstant[0] = calconstants[0]        # (test) Station name
        cconstant[1] = header[1]              # (text) Channel name for CH0
        cconstant[2] = float(calconstants[1]) # (float) adccal[0]: cal constant for ch 0 (microvolts / count)
        cconstant[3] = header[2]              # (text) Channel name for CH1
        cconstant[4] = float(calconstants[2]) # (float) adccal[1]: cal constant for ch 1 (microvolts / count)
        cconstant[5] = header[3]              # (text) Channel name for CH2
        cconstant[6] = float(calconstants[3]) # (float) adccal[2]: cal constant for ch 2 (microvolts / count)
        cconstant[7] = header[4]              # (text) Channel name for CH3
        cconstant[8] = float(calconstants[4]) # (float) adccal[3]: cal constant for ch 3 (microvolts / count)
        cconstant[9] = float(calconstants[5]) # (float) laserres: cal constant for the laser ( mV / micron)
        cconstant[10] = float(calconstants[6])# (float) lcalconst: cal constant for geometry correction factor
        cconstant[11] = float(calconstants[7])# (float) h: Damping ratio for the seismometer as measured by engineer.
        cconstant[12] = float(calconstants[8])# (float) resfreq: Free period resonance freq. as measured by engineer.
        cconstant[13] = int(selection[0])     # channel number of channel being tested
        cconstant[14] = int(selection[1])     # channel number of the laser position sensor data
    return(cconstant)



                                   # load the csv infile as generated by DAT2ASC with csv option
def csvload(infile):
    print "Attempting to load CSV files."    
    Station = raw_input('Please enter the station name. ')
    laserchan = int(raw_input('\n\nWhich channel was used to record the laser?(ch 0 through ch3) '))
    sensorchan = int(raw_input('\nWhich channel was used to record the sensor?(ch0 through ch3) '))
                                
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
                                            # Parse out the sensor and laser data
    sensor = [] 
    laser = []
    for i in range(0,len(stack)):
        sensor.append(int(stack[i][sensorchan+1], base=10)) # Channel 2 is sensor
        laser.append(int(stack[i][laserchan+1], base=10))# Channel 1 is laser


    delta = ((float(stack[len(stack)-1][12])+float(stack[len(stack)-1][15]))-(float(stack[0][12])+float(stack[0][15])))/len(stack)


    return(sensor,laser,delta)

#    return (header,stack)

   
def cssload(infile):
    print "Attempting to load CSS files."
    cs = read(infile, format = "css")
    print "Available channels:\n"

    for i in range(0,len(cs)):
        print "Channel: {}".format(cs[i].stats.channel)


    lsrchan = raw_input('\n\nWhat is the name of the channel for the laser? ')
    senchan = raw_input('\nWhat is the name of the channel for the sensor? ')

    delta = cs[0].stats.delta
    for i in range(len(cs)):
        if string.lower(senchan) == string.lower(cs[i].stats.channel):
            sensor = cs[i].data
        elif sring.lower(lsrchan) == string.lower(cs[i].stats.channel):
            laser = cs[i].data

    return(sensor,laser,delta)



def sacload(infile):
    print "Attempting to load SAC files."

    cs = read(infile, format = "sac")

    print "Available channels:\n"

    for i in range(0,len(cs)):
        print "Channel: {}".format(cs[i].stats.channel)

#    Station = raw_input('Please enter the station name. ')

    sensor = []
    laser = []
    delta = cs[0].stats.delta
    while len(sensor)==0 or len(laser) == 0:
        lsrchan = raw_input('\n\nWhat is the name of the channel for the laser? ')
        senchan = raw_input('\nWhat is the name of the channel for the sensor?')
        for i in range(len(cs)):
            if string.lower(senchan) == string.lower(cs[i].stats.channel):
                sensor = cs[i].data
            elif string.lower(lsrchan) == string.lower(cs[i].stats.channel):
                laser = cs[i].data
        if len(sensor) == 0 or len(laser) == 0:
            print "Unable to resolve laser or sensor from these channels."

    return(sensor,laser,delta)



def mseedload(infile):
    print "Attempting to load miniseed files."
    cs = read(infile, format = "mseed")
    print "Available channels:\n"
    for i in range(0,len(cs)):
        print "Channel: {}".format(cs[i].stats.channel)

#    Station = raw_input('Please enter the station name. ')
    lsrchan = raw_input('\n\nWhat is the name of the channel for the laser? ')
    senchan = raw_input('\nWhat is the name of the channel for the sensor?')

    delta = cs[0].stats.delta
    for i in range(len(cs)):
        if string.lower(senchan) == string.lower(cs[i].stats.channel):
            sensor = cs[i].data
        elif string.lower(lsrchan) == string.lower(cs[i].stats.channel):
            laser = cs[i].data

    return(sensor,laser,delta)

                                #                       Function getconstants:

#def getconstants(calcontrol):      # From calcontrol file, retrieve the list of constants 
#    constants = load(calcontrol)   # that relate these measurements to the real world.
#    constant = constants[1][0]        # constants[0] contains headers that we don't really use
                                   # constant[0] = (text) Station: 'station name'
                                   # constant[1] = (float) adccal[0]: cal constant for ch 0 (microvolts / count)
                                   # constant[2] = (float) adccal[1]: cal constant for ch 1 (microvolts / count)
                                   # constant[3] = (float) adccal[2]: cal constant for ch 2 (microvolts / count)
                                   # constant[4] = (float) adccal[3]: cal constant for ch 3 (microvolts / count)
                                   # constant[5] = (float) laserres: cal constant for the laser ( mV / micron)
                                   # constant[6] = (float) lcalconst: cal constant for geometry correction factor
                                   # constant[7] = (float) h: Damping ratio for the seismometer as measured by engineer.
                                   # constant[8] = (float) resfreq: Free period resonance freq. as measured by engineer.
#    return(constant)


def scatter_comparison():
    '''exponential function, y = exp(0.05 x)'''
 
    # prepare data points
    # plot it
    
    plt.loglog(F1, S1, "*", F2, S2, "+") #, F3, S3, "*")     # the "." means draw points instead of lines
    plt.xlabel("Frequency")
    plt.ylabel("Sensitivity in V/m/sec")
    plt.title("Comparison of sensitivity curves")
    plt.annotate("* = derivative data", xy=(10,5), xytext=(3,1),
                 arrowprops=dict(facecolor='black',shrink=0.05))
    plt.annotate("+ = integral data", xy=(.1,.1), xytext=(1,.1),
                 arrowprops=dict(facecolor='green',shrink=0.05))
#    plt.annotate("* = Signal hybrid", xy = (.1,.1), xytext = (1,.01),
#                 arrowprops=dict(facecolor='red',shrink=0.05))
    plt.show()
    
def graph_curve(time,counts,resfreq):
    plt.plot(time,counts)
    plt.xlabel("Time (in seconds)    Free period frequency = {:.3f} Hz".format(resfreq))
    plt.ylabel("Counts")
    plt.show()

def graph_curve2(X,Y,Ylabel,Y1,ylabel1):
    plt.plot(X,Y, '-b', label = Ylabel)
    plt.plot(X,Y1, '-r', label = Ylabel1)
    plt.xlabel("Samples")
    plt.ylabel("Counts")
    plt.show()

def process(infile,filetype):

  
    if filetype == 'csv':
        (sensor,laser,delta) = csvload(infile)     # Load the infile currently loaded with 1 Hz data
    elif filetype =='sac':
        (sensor,laser,delta) = sacload(infile)
    else:
        (sensor,laser,delta) = cssload(infile)

   
    adccal = [1.0,1.0,1.0,1.0]
            # microns / count from the CALIBRATED laser and CALIBRATED ADC.
                                            # Calculate the sample period based on the timing channels (in seconds)

        # laser = sp.signal.symiirorder1(laser,4,.8) # Adjust the signal for DC bias of laser, then filter.
#    lasermean = np.mean(laser[(len(laser)-2048):len(laser)]) # Take the DC bias measurement fm end of signal
#    laser[:] = [x-int(lasermean) for x in laser]
                                      #
                                      # I am not yet able to auto process these files
                                      # Therefore we'll open the graph, plot the whole waveform
                                      # and let the user pick the starting sample point.
                                      # Then we'll process frequency from there.


    x = []
    for i in range (0,len(laser)):
        x.append(i)
    plt.plot(x,laser)
    plt.show()

    start =int(raw_input('Enter the estimated sample number of the beginning of the impulse  '))
  
    end = start+1024
        ##########################################################


    ##########################################################
                                      #            
                                      # Find the period of the observed signal
                                      #


    sense = signal.detrend(laser[start:end])   # 2466:(2466+4096)]
                                      # sense = sense[:]
    N = len(sense)
    W    = np.fft.fft(sense)
    freq = np.fft.fftfreq(len(sense),delta) 
                                      # First value represents the number of samples and delta is the sample rate

                                      #
                                      # Take the sample with the largest amplitude as our center frequency. 
                                      # This only works if the signal is heavily sinusoidal and stationary 
                                      # in nature, like our calibration data.
                                      #

    idx = np.where(abs(W)==max(np.abs(W)))[0][-1]
    Frequency = abs(freq[idx])        # Frequency in Hz
    print Frequency, delta
    period = 1/(Frequency*delta)      # represents the number of samples for one cycle of the test signal.

                                      # gmcorrect = (2*np.pi*Frequency)**2/np.sqrt((Rn**2-(2*np.pi*Frequency)**2)**2+(4*h**2*(2*np.pi*Frequency)**2*Rn**2))
                                      #
                                      # create an axis representing time.
                                      #

    dt = [] # Create an x axis that represents elapsed time in seconds. delta = seconds per sample, i represents sample count
    for i in range(0,len(sense)):
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
    x = []
    for i in range(0,len(sense)):
        x.append(i*delta)
    graph_curve(x,sense,Frequency)

    print 'Frequency calculated to ',Frequency,' Hz.' 







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
    infile = '*.sac'
    outfile = os.getcwd()+"\calibration_freeperiod_report.cal"
    calfile = os.getcwd()+"\calcontrol.cal"
    filetype = 'sac'                  # The default filetype
    for i in range(1,len(sys.argv)):
        if "." in sys.argv[i]:        # assume that this argument contains a file name.
            infile = sys.argv[i]
        elif 'csv' in sys.argv[i]:
            filetype = 'csv'
        elif 'css' in sys.argv[i]:
            filetype = 'css'
        elif 'sac' in sys.argv[i]:
            filetype = 'sac'
        elif 'mseed' in sys.argv[i]:
            filetype = 'mseed'

    if len(infile) != 0:
        process(infile,filetype)
    else:        
        print "\nThis program requires that you specify a file representing the free period resonance."#        constant = getconstants(calfile)

#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()
