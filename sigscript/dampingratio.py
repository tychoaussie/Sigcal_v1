__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20150228"
__license__ = "MIT"

import os, sys, csv
from obspy.core import read
from scipy import signal
from scipy.integrate import simps
import pylab as plt
import numpy as np
import scipy as sp


# Rev 2 incorporates the calculation of free period based on the period of damping ratio impulse.
# Based on formulas from Soviet instrumentation textbooks that relate how damping ratio affects
# the shift in oscillation frequency.
#
# Rev 2 also has support for SAC and Miniseed files.
#
                                           # import time, string
                                           # from obspy.core import read, Trace, Stream, UTCDateTime
                                           # from obspy.sac import SacIO
class Dampingratio(object):
    '''Dampingratio is a utility for measuring the seismometer damping ratio.
       It will return an average damping ratio representing the first two
       oscillations of the transient. It will also estimate free period from
       the impulse period based on the average damping ratio.
       
        

       Syntax: dampingratio target_file filetype

       

       Typical useage:
       <ObsPy> C:\Python27\scripts> python dampingratio.py c:/calibration/damping/myfile.sac sac

       Optional parameters: filetype of either: [ csv, sac, msd ]
    '''






def csvload(infile):      	# function csvload: Bring in only one channel, specified by user.
                                    
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
            
    sensor = [] 
    laser = []

#    keyboard = raw_input('\n Enter the channel num. for the laser position sensor')
#    if keyboard =="":
#        keyboard = "0"
#    lsrchan = int(keyboard)
    keyboard = raw_input('\n Enter the channel num. for the seismic sensor')
    if keyboard =="":
        keyboard = "1"
    senchan = int(keyboard)

    for i in range(0,len(stack)): # populate the sensor and laser lists with the data
        sensor.append(int(stack[i][senchan+1], base=10))
#        laser.append(int(stack[i][lsrchan+1], base=10))

                                  # Calculate the sample period based on the timing channels (in seconds)

    delta = ((float(stack[len(stack)-1][12])+float(stack[len(stack)-1][15]))-(float(stack[0][12])+float(stack[0][15])))/len(stack)
            
    return (sensor,delta)




				# function sacload: This function serves both sac and miniseed files.



def sacload(infile):

    st=read(infile)
    delta = st[0].stats.delta
    sensor = st[0].data

    return(sensor,delta)






                                   # Create a low pass filter to be applied to the signal and laser
                                   # in order reduce interference from 50 or 60 hz hum and stuff like that
                                   #

def firfilt(interval, freq, sampling_rate):  # Interval is the array upon which you wish to apply the low pass filter
    nfreq = freq/(0.5*sampling_rate)
    taps =  sampling_rate + 1
    a = 1
    b = sp.signal.firwin(taps, cutoff=nfreq)
    firstpass = sp.signal.lfilter(b, a, interval)
    secondpass = sp.signal.lfilter(b, a, firstpass[::-1])[::-1]
    return secondpass                                  

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
                                              # Load the infile currently loaded with 1 Hz data
    if filetype == 'csv':
        (sensor,delta) = csvload(infile)
    elif (filetype == 'sac') or (filetype == 'msd'):
        (sensor,delta) = sacload(infile)
    else:
        print "\n\n\nError: Unable to determine the file type of this input file.\n\n\n"    


#    constant = getconstants(calfile)         # Retrieve the constants from the file

#    Station = constant[0]                    # Name of Station under test
#    for i in range(0,4):
#        adccal[i] = float(constant[i+1])     # Calibration constants for the ADC channels as measured by engineer
                                             # for this particular system. Each one is unique.
#    laserres = float(constant[5])            # CALIBRATED value from laser position sensor in mV/micron
#    lcalconst = float(constant[6])           # Typ. 1.022, for the SM3, based on the geometry of the laser target 
                                             # and center of coil relative to radius of moment arm
#    h = float(constant[7])                   # typically about 0.7 but MUST be accurately measured beforehand!
#    resfreq = float(constant[8])             # Typically between 0.7 and 1.3 Hz. Expressed in Hz, not seconds.
#    Rn = (np.pi * 2.0 * resfreq)             # Free period as expressed in radians / second                      
#    lasercal = laserres/1000                 # microns / count from the CALIBRATED laser and CALIBRATED ADC.


    print 'This program is designed to assist you in the measurement of the damping ratio.\n'
    print ' You should have a csv file that represents several damping ratio impulses.' 
    print ' The following screens will open and enable you to plot the waveform within'
    print ' the file. The data is filtered with a low-pass filter to 10 Hz. For each'
    print ' impulse, measure the sample number representing the downslope of the '
    print ' first impulse as well as the sample number representing the end of the'
    print ' level part of the ending part of the wave where signal is flat.\n' 
    print ' The program will enable you to enter these sample numbers for as many impulses'
    print ' as you have within the file.\n\n'
    print ' The program will calculate the damping ratios as the average of Z1 to Z2,'
    print ' and Z2 to Z3, then make an average damping ratio from the impulses. '
    
                                             # Parse out the sensor and laser data

                                             # Calculate the sample period based on the timing channels (in seconds)

#        delta = ((float(fdata[1][len(fdata[1])-1][12])+float(fdata[1][len(fdata[1])-1][15]))-(float(fdata[1][0][12])+float(fdata[1][0][15])))/len(fdata[1])

#    laser = firfilt(laser,10,1/delta)
    sensor = firfilt(sensor,10,1/delta)
                                             # Apply a high pass filter to remove any high-frequency interference from signal

    # laser = sp.signal.symiirorder1(laser,4,.8) # Adjust the signal for DC bias of laser, then filter.
#    lasermean = np.mean(laser[(len(laser)-2048):len(laser)]) # Take the DC bias measurement fm end of signal
#    laser[:] = [x-int(lasermean) for x in laser]
    
                                      #
                                      # I am not yet able to auto process these files
                                      # Therefore we'll open the graph, plot the whole waveform
                                      # and let the user pick the starting sample point.
                                      # Then we'll process frequency from there.
    x = []
    for i in range (0,len(sensor)):
        x.append(i)
    plt.plot(x,sensor)
    plt.show()
    keyboard = raw_input('\n\n How many impulses have you measured? ')
    if keyboard =="":
        print "Nothing entered. Setting the default to one pulse."
        keyboard = "1"
    impnum = int(keyboard)
    last = []
    first = []
    for i in range (1,impnum+1):
        keyboard = raw_input('\n Enter the estimated sample number of the beginning of the impulse {}  '.format(i))
        if keyboard == "":
            print "Nothing entered. Setting default to sample # 1"
            keyboard = 1
        first.append(int(keyboard))
        keyboard = raw_input('Enter the estimated sample number of the ending of the impulse train {} '.format(i))
        if keyboard =="":
            print "Nothing entered. Setting default to sample 1024"
            keyboard = "1024"
        last.append(int(keyboard))


    ##########################################################
    nn = 0
    hn = []
    freep = []
    for i in range(0,impnum):

        sense = sensor[first[i]:last[i]]
        sgrad = np.gradient(sense,80)
                                  # sgrad is the derivative of the sensor: Scan for zero crossings
        sgfilt = sp.signal.symiirorder1(sgrad,4,.8)
        dt = []
        Z = []                            # Z is the list of sensor values corresponding to where the derivative flips sign,
        ZZ = []                           # and should represent where the local max/min occurred in the waveform.
        offset = np.mean(sense[(len(sense)-131):len(sense)])   # Use the tail to determine the zero point of the impulse          
        polarity = 0
        
        zero_crossings = np.where(np.diff(np.sign(sgfilt)))[0]
  
        for n in range(0,len(zero_crossings)):
           Z.append(sense[zero_crossings[n]]-offset)

           if (n<>0) and (n<4):
               dt.append(2*(zero_crossings[n]-zero_crossings[n-1])*delta)
               # time between the peaks in seconds
           # Z represents the actual peak sample where the derivative went to zero and is offset corrected
#        for n in range(0,len(dt)):
#            print "dt[{0}] equals {1}".format(n,dt[n]) #    print sense[zero_crossings[i]]
        for n in range(0,len(Z)-1):
            zz = np.abs(Z[n])       # zz is the absolute value of the signal datapoint
            ZZ.append(zz)             # ZZ is the list of absolute values from Z
                                  # Adjust Z for middle tail-end to fix bias problems
                                               # Calculate the list of "good" points based on the fact that each value should 
                                               # be smaller than the next 
        nn = 0
        flag = True
  
        for n in range(1,len(ZZ)):
                if np.int(ZZ[n])>np.int(ZZ[n-1]): # look at peak to see if is indeed smaller than prev impulse
                    flag = False
                else:
                    if flag == True:
                        nn +=1
        if nn>3:
            nn = 3 # stop counting at 4   
        hh = []
        fp = []

        for n in range(1,nn):              # calculate a list of damping ratios starting with the second local max
            hh.append(np.log(np.abs(float(Z[n-1])/Z[n])) / np.sqrt(np.square(np.pi)+np.log(np.abs(float(Z[n-1])/Z[n]))))
        hn.append(np.mean(hh))


        for n in range(1,len(dt)):
            fps = dt[n]*np.sqrt(1-np.mean(hh)**2)
            fp.append(fps)
#            print "dt = {0} and h = {1} for a freeperiod of {2} sec".format(dt[n],np.mean(hh), fps)  # calculate the theoretical free period
        freep.append(np.mean(fp))

        print '\n Damping ratios for impulse {0} that create a mean of {1:0.3f} are as follows: '.format(i,np.mean(hh))
        print hh 
    hm = np.median(hn)
    ha = np.mean(hn)

    freeperiod = np.mean(freep)
    print '\n\n The median damping ratio for your {0} impulses = {1:0.3f} . '.format(impnum,hm)
    print '\n The mean damping ratio for your {0} impulses = {1:0.3f} . '.format(impnum,ha)
    print '\n The calculated mean free period is equal to: \n{0} seconds.   ({1} Hz)'.format(freeperiod,1/freeperiod)

#    Delta tells us the sample period of the digitized data. Z is the samplenumbers of the zero crossings.
#    Ts'n to Ts'n+1 is the time to complete one cycle.
#    Ts, the free period is related by the formula Ts'*sqrt(1-h^2)
#    So, report the time, which is (Z(n+2) - Z(n))*Delta

    



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
    outfile = os.getcwd()+"\calibration_freeperiod_report.cal"

    if optioncount > 1:
        for n in range(1,optioncount):
            if "csv" in sys.argv[n]:
                filetype = 'csv'
            if "sac" in sys.argv[n]:
                filetype = 'sac'
            if "msd" in sys.argv[n]:
                filetype = 'msd'
            if "." in sys.argv[n]:
                infile = sys.argv[n]
    else:
        print " This program requires that you input a file representing \na calibration impulse for damping ratio calculation."
        print " The file type should also be designated. The three possible types are: csv, sac, or msd"
        exit()
    
    process(infile,filetype)                                                     


#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()
