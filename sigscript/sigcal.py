__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20151001"
__license__ = "MIT"

# 20151001 - Bring Calcontrol setups into this program, eliminate CSV support and simplify the interface.
# 20150925 - Add proper css file support via WFD format support.
# 20150814 - Add some error traps for bad files and fix some printed fields.
# 20150721 - replace dependency on Python27 directory with Anaconda dependency
# 20150721 - change the recommended defaults for grid search to Hz.
# 20150722 - Change the CWD used for the plots in gridsearch to the appropriate directory
# 20150728 - change some of the plotted text to describe the calibration values

# NEW VERSION for testing revised signal processing techniques.
# Use FFT for finding the RMS of the signals,
# then use 2*pi*f to compare relationship of signal to derivative of
# the laser position.
# Break the waveform into 4096 sample chunks and process them.
# Then, look at the standard deviation and use the chunk with the
# lowest dtandard deviation for determining sensitivity.

# 20141114 version: Move the file construction out of the process loop, and instead, pass
# the raw parameters into main, where they are then assembled into an array
# and file. Then, use the array directly with grid searching for determining 
# the optimum damping ratio that fits the curve, and then write out the final
# file, based on the optimized damping ratio.

# This prepares the code for use in internalizing the curve calculations.
# The next iteration of code likely will pass the UNCOMPENSATED ground motion curve 
# into the grid search algorithm so that we won't have to know what the damping
# ratio is. Rather, we'll use the shape of the calibration curve and a grid search
# to model the theoretical damping ratio that best describes the behavior of the
# transducer. This should be the practical damping ratio of the whole system.

# 11/25/2014 - fixed the problem with free period going into the grid search as a
# frequency rather than a period.
# - Rev b: Constrained the grid search to use the MSU measured free period AND damping
# when doing a grid search because of demonstrated dependency on damping ratio as
# affecting the results of the initial sensitivity curve. Improve at a later date.

# 12jan2015 - minor bug fixes to file paths on output
#
# Version 2: 
#
# 09Feb2015 - Integrate Grid search into the main code space
# Bring in sac file support. sac option also supports miniseed.
# In order to use the files, the station name, the channel name
# (as described in calcontrol.cal) must be in the file name for
# sigcal to find it.
# Rewrite the command line switch sequence.
# 3/3/2015 - include interim css3.0 file support 


# Now, the most important part - The legalese: 

# COPYRIGHT BOARD OF TRUSTEES OF MICHIGAN STATE UNIVERSITY
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

# SPARTY WILL GET YOU IF YOU BREAK THE RULES SO DONT TELL ME I DIDNT WARN YOU

import os, sys, csv
from scipy import signal
from scipy.integrate import simps
from obspy.core import read
import obspy.signal.invsim as sim
#import pylab as plt
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import difflib as diff
import time, string
#import grid_search                         # Grid_search created by Hans Hartse, LANL
                                           

                                           # from obspy.core import read, Trace, Stream, UTCDateTime
                                           # from obspy.sac import SacIO
                                
class Sigcal(object):
    '''Sigcal is a utility for converting SAC, Mseed, or CSS files
       that represent a series of sinusoidal
       signals which were excited by a calibration coil and recorded simultaneously
       on the seismometer velocity coil and with a laser position sensor that tracks
       actual movement of the seismometer mass. By comparing the seismometer signal
       to the laser position, it is possible to determine the sensitivity at that 
       frequency. This program takes a series of files representing frequencies across
       the instrument passband and uses them to create a calibration response curve.
       There are some initial constants that are required in order to process these
       files. They are found within the file called 'calcontrol.cal' which is invoked
       by this program. This file should exist within the parent directory that
       also contains all the csv files. Calcontrol contains the calibration data
       as well as the channel names, station name, and the controlling channels that
       represent the sensor under calibration as well as the laser position channel.
        

       Syntax: Sigcal [target_directory] [target_filetype] [station_name]
       where, target directory is an optional parameter designating the directory
              containing the calibration data.
              target filetype is either 'sac', 'msd', or 'css'.
              station_name is designated within the data file names, and they are
                 a .sac file. The .sac file extension is unnecessary if you
                 designate the station name, however you must make sure the files 
                 are all good sac files.  

       

       Typical useage:
       <ObsPy> C:\Python27\scripts> python Sigcal.py c:/calibration/station/ [outfputfile] [calconstfile]

    '''

#                                                    Function Load:
#                                 General purpose loading function that brings in the first line as
#                                 a header list, and the remaining dataset as a secondary list
#
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


#
#                                                     Function getoptions
#                                       Function parses through the command line options
#                                       and returns a file list of files that match
#                                       the file type, or the station name. 
#                                       File type .csv is the default. 
#                                       File type .sac may be specified.
#                                       If station name is used preceded by the word 'station'
#                                       it is assumed the file type is sac
#
#                                       Returns: 1) Directory path
#                                                2) list of files
#                                                3) Cal file name
#                                                4) output file name
#                                                5) File type
#                                      Special handling of css files: Ignore any 'audit' wfd's in the file list.

def getoptions():
    directory = os.getcwd()
    if ('\\' not in directory[-1:]) and ('/' not in directory[-1:]):
                directory = directory+'\\'
    filetype = 'sac' # Default file type. sac covers sac, miniseed.
    filelist = []
    station = 0
    stname = 'unk'
    for i in range(1,len(sys.argv)): # corrected this bug drb 20150721
#    print "Option {0} is equal to '{1}'".format(i,sys.argv[i])
 #       if 'csv' in string.lower(sys.argv[i]):
 #           filetype = 'csv'
#        print "Setting the file type to csv"
        if 'sac' in string.lower(sys.argv[i]):
            filetype = 'sac'
        if 'msd' in string.lower(sys.argv[i]):
            filetype = 'sac'
        if 'css' in string.lower(sys.argv[i]):
            filetype = 'css'
        if ('\\' in sys.argv[i]) or ('/' in sys.argv[i]):
            if ('\\' in sys.argv[i][-1:]) or ('/' in sys.argv[i][-1:]):
                directory = sys.argv[i]
            else: 
                directory = sys.argv[i]+'\\'
        if station:
            filetype = 'sac'
            stname = sys.argv[i]
        if 'station' in string.lower(sys.argv[i]):
            station = 1
        else:
            station = 0

    calfile = 'c:\\anaconda\\sigscript\\calcontrol.csv'   #### DEFAULT FILE LOCATION FOR THE CALFILE TEMPLATE
    outfile = directory+"calibration_output.cal"
    cconstant = getcal(calfile)                           #### DONT FORGET TO AUDIT THE CALFILE ####
	
    buffer = os.listdir(directory)

    for i in range(0,len(buffer)):
        filtype = 'unk'
#        if '.csv' in string.lower(buffer[i]):
#            filtype = 'csv'
        if ('.sac' in string.lower(buffer[i]) and '.sacpz' not in string.lower(buffer[i])):
            filtype = 'sac'
        elif ('.wfd' in string.lower(buffer[i]) and 'audit' not in string.lower(buffer[i])):
            filtype = 'css'
            print "A wfd file was found within the directory and filtype set to css."

# cconstant[0] = station name
			
    
        if (         (filtype == filetype) or (stname in buffer[i]) \
            or (str(cconstant[0]) in buffer[i]) or (str(cconstant[1]) in buffer[i]) \
            or (str(cconstant[3]) in buffer[i])                             ) \
                                         and \
            ( ('.sacpz' not in buffer[i]) and ('png' not in buffer[i])  ):

            filelist.append(buffer[i])

#            Need to clean up the list in cases of css files

    if filetype == 'css':  # clean out unwanted file types. This is  HACK , I know. but I am time limited

        list = []
        for i in range(0,len(filelist)): 
            if ('.wfd' in string.lower(filelist[i]) and 'audit' not in string.lower(filelist[i])):
                list.append(filelist[i])
        filelist = list
#    print filelist		
# Note that the css filelist should contain only wfd files which just point to the real data files
    options = [directory,filelist,calfile,outfile,filetype]
    return(cconstant,options)


                                    # Function sacparse
                                    # Input the file list, the sensor channel, the laser channel name
                                    # and return a sorted list of sac files for these two channel pairs
def sacparse(wdir,filelist,senchan,lsrchan):
    sensorfiles = []
    laserfiles = []
    print "senchan set to: {0} and lsrchan set to: {1} \n File list contains {2} items.".format(senchan,lsrchan,len(filelist))
    for i in range(0,len(filelist)):
#        print filelist[i]
        if senchan in filelist[i]:
            sensorfiles.append((wdir+filelist[i]))
#        else: 
#            print "senchan not found in {}".format(filelist[i])
        if lsrchan in filelist[i]:
            laserfiles.append((wdir+filelist[i]))
    sensorfiles.sort(key=str.lower)
    laserfiles.sort(key=str.lower)
    return(sensorfiles,laserfiles)


                                   # Function sacload
                                   # Bring in two file names, compare, load the stream and
                                   # output the stream data and sample period (in seconds)
                                   #
def sacload(sensorfile,laserfile,senchan,lsrchan):
                                   # input parameters: infile[],senchan,lsrchan
    result = diff.ndiff(sensorfile,laserfile)    # Result gives us the common letters from the file name
    txt = ''.join(result)
    common = ""
    for i in range(0,int(len(txt))/3):
        if (txt[i*3] == " "):
            common = common+txt[i*3+2]
        if (txt[i*3] == "-") or (txt[i*3] == "+"):  # Add a wild card for any letters that are different
            common = common+"*"
    st=read(common)                                 # Read all conforming channels that match the channel names
    delta = st[0].stats.delta
    for i in range(0,len(st)):
        if (string.lower(senchan) == string.lower(st[i].stats.channel)):   # If the stream matches sensor or laser channel name
            sensor = st[i].data
        elif (string.lower(lsrchan) == string.lower(st[i].stats.channel)): # Append it.
            laser = st[i].data
    return(sensor,laser,delta)





                                   #                 Function csvload:
                                   # load the csv infile as generated by DAT2ASC with csv option
                                   # Return the unit channel data, laser data, and sample period
                                   # senchan determines which channel is the sensor data
                                   # lsrchan determines which channel is the laser data
def csvload(infile,senchan,lsrchan):                                    
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
    for i in range(0,len(stack)): # populate the sensor and laser lists with the data
        sensor.append(int(stack[i][senchan+1], base=10))
        laser.append(int(stack[i][lsrchan+1], base=10))

                                  # Calculate the sample period based on the timing channels (in seconds)

    delta = ((float(stack[len(stack)-1][12])+float(stack[len(stack)-1][15]))-(float(stack[0][12])+float(stack[0][15])))/len(stack)
            
    return (sensor,laser,delta)




                                # support for css data format #
								
def wfdaudit(cwd,wfdin):  # Audit the css wfd file and repair it if there are missing streams.
                          # Input: Record of current working directory, and the name of the wfd file

    wfdout = cwd+wfdin[:-4]+"_audit.wfd"
    wfdin = cwd+wfdin
    cssbufffile = open(wfdin)
    print "this is wfdin: '{}'".format(wfdin)
    cssbuffout = open(wfdout, mode = "w")
    
    #     Okay, we need to fix the wfd by editing it and removing reference to any non-existent files.
    #     Audit the wfd and create a modified version.
    #     Auditing and removing non-existent file references ensures we can open the CSS.
    
    cssbuff = []
    try:
        for i in range(0,1000):
            buff =cssbufffile.readline()
            if buff != "":
                cssbuff.append(buff)        
    except:
        print "There was a Problem when opening wfd file"

    buffout = []    
    for i in range(0,len(cssbuff)):
        buffile = cwd+cssbuff[i][150:225].lstrip() # parse out the file names found inside wfd
 #       print "buffile = '{}'".format(buffile)
        if os.path.isfile(buffile):
#           print '"{}" exists.'.format(buffile)
            cssbuffout.write(cssbuff[i])
    return(wfdout)  # Return the name of the audited wfd file

	
	
def cssload(sensorstream,laserstream): #   Two separate streams from the wfd.
    delta=sensorstream.stats.delta
    sensor =sensorstream.data
    laser = laserstream.data
    #for i in range(len(sensor)):
    #    if string.lower(senchan) == string.lower(cs[i].stats.channel):
    #        sensor = cs[i].data
    #    elif string.lower(lsrchan) == string.lower(cs[i].stats.channel):
    #        laser = cs[i].data

    return(sensor,laser,delta)



                            # Function getcal: Retrieve the calibration control file
def getcal(calcontrol):
    stack = []
    try:
        print calcontrol
        with open(calcontrol,'r') as fin:
            list = csv.reader(fin, delimiter = ',')
            for row in list:
                stack.append(row)
            cconstant = ccaudit(calcontrol,stack)
            return(cconstant)
    except:
        print "Calcontrol file is not yet defined. These parameters are required to run Sigcal."
        print "They must be located in the directory at this file location: \n {}".format(calcontrol)
        print "For now, the following default values are being generated:"
        print "Update these numbers and then re-run Sigcal."
        stack.append(["STATION_NAME","MSU"])
        stack.append(["SENCHAN","BHZ"])
        stack.append(["SENCHAN_SENSITIVITY",0.945])
        stack.append(["LSRCHAN","LASER"])
        stack.append(["LSR_SENSITIVITY",0.945]) # expressed in microvolts/count
        stack.append(["LASER_RESOLUTION",1.000])
        stack.append(["LCAL_CONSTANT",0.579]) # SM3 accepted value
        stack.append(["DAMPING_RATIO",0.707])
        stack.append(["RESONANCE_FREQ",0.890]) # Expressed in Hz
        with open(calcontrol,'w') as fout:
            cal = csv.writer(fout, delimiter=',',
                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in range(0,len(stack)):        
                cal.writerow(stack[i])
                print "{0} = {1}".format(stack[i][0],stack[i][1])
        cconstant = ccaudit(calcontrol,stack)
        return(cconstant) 



                                   # Function ccaudit:
                                   # From calcontrol file, retrieve the list of constants 
                                   # that relate these measurements to the real world.
								   # Stack[][] contains the defaults going in. Audit them, 
								   # update the stack, write it back out if user desires to
								   # update, and then return cconstant back to the program.

                                   # constant[0] = (text) Station: 'station name'
								   # constant[1] = (text) Sensor channel name
                                   # constant[2] = (float) cal constant for Sensor channel (microvolts / count)
                                   # constant[3] = (text) Laser channel name
								   # constant[4] = (float) Laser channel cal constant (microvolts/count)
                                   # stack[5][1] = (float) laserres: Sensitivity for the laser ( mV / micron)
                                   # stack[6][1] = (float) lcalconst: cal constant for geometry correction factor
                                   # stack[7][1] = (float) h: Damping ratio for the seismometer as measured by engineer.
                                   # stack[8][1] = (float) resfreq: Free period resonance freq. as measured by engineer.

def ccaudit(calcontrol,stack):
    cconstant = []
    for i in range(0,len(stack)):
        cconstant.append(stack[i][1])
	

    try:
        invar = raw_input('Please enter the station name. (Default = [ {} ]) \n--> '.format(stack[0][1]))
        if len(invar)==0:
            invar = str(stack[0][1])
            print "Station name is set to default '{}'".format(stack[0][1])
        cconstant[0]=str(invar)
        stack[0][1] = str(invar)
        
    except ValueError:
        print "Please enter appropriate characters. Station name set to '{}'.".format(stack[0][1])


    try:
        print"\nEnter the name of the sensor channel: (Default = [ {} ]) ".format(stack[1][1])
        invar = str(raw_input('-->'))
        if len(invar)==0:      
            print "Channel name is set to default '{}'".format(stack[1][1])
            invar = stack[1][1]
        stack[1][1] = str(invar)
        cconstant[1] = str(invar)
			
    except ValueError:
        print "No input."
        print "channel name set to '{}' as a default.".format(stack[1][1])
 
    print "This is cconstant: {}".format(cconstant) 

    try:
        print 'Sensor channel calibration value, in uV/count: Default = [ {} ] '.format(stack[2][1])
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Channel gain set to default of {}\n\n".format(stack[2][1])
            invar = stack[2][1]
        stack[2][1] = (float(invar))
        cconstant[2] = float(invar)
		
    except ValueError:
        print "Value must be a floating point number."
        print "Calibration number being set to {} uV/count as a default.\n\n".format(stack[2][1])

			
			
    try:
        print"\nEnter the name of the laser channel: (Default = [ {} ]) ".format(stack[3][1])
        invar = str(raw_input('-->'))
        if len(invar)==0:      
            print "laser Channel name is set to default '{}'".format(stack[3][1])
            invar = stack[3][1]
        stack[3][1] = str(invar)
        cconstant[3] = str(invar)
			
    except ValueError:
        print "No input."
        print "laser channel name set to '{}' as a default.".format(stack[3][1])
         

    try:
        print 'laser channel calibration value, in uV/count: Default = [ {} ] '.format(stack[4][1])
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Laser Channel gain set to default of {}\n\n".format(stack[4][1])
            invar = stack[4][1]
        stack[4][1] = (float(invar))
        cconstant[4] = float(invar)
    except ValueError:
        print "Value must be a floating point number."
        print "Laser channel calibration number being set to {} uV/count as a default.\n\n".format(stack[4][1])
		

    try:
        print 'Enter laser resolution calibration (mV/micron). default = [ {} ]'.format(stack[5][1])
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Laser resolution set to default of {} mV/micron\n".format(stack[5][1])
            invar = stack[5][1]
        stack[5][1] = (float(invar))
        cconstant[5] = float(invar)
    except ValueError:
        print "Value must be a floating point number."
        print "Calibration number being set to {} mV/micron as a default.\n".format(stack[5][1])


    try:
        print 'Enter the mass/laser position Geometry correction ratio: default = [ {} ]'.format(stack[6][1])
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "correction ratio set to default of {}\n".format(stack[6][1])
            invar = stack[6][1]
        stack[6][1] = (float(invar))
        cconstant[6] = float(invar)
    except ValueError:
        print "Value must be a floating point number."
        print "Correction ratio being set to {} as a default.\n".format(stack[6][1])


    try:
        print 'Enter the damping ratio for this seismometer:'
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Damping ratio (h) set to default of {}\n".format(stack[7][1])
            invar = stack[7][1]
        stack[7][1] = (float(invar))
        cconstant[7] = float(invar)
    except ValueError:
        print "Value must be a floating point number."
        print "Damping ratio (h) being set to {} as a default.\n".format(stack[7][1])


    try:
        print 'Enter the resonance frequency (1/free period) in Hz:'
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Resonance frequency set to default of {} Hz\n".format(stack[8][1])
            invar = stack[8][1]
        stack[8][1] = (float(invar))
        cconstant[8] = float(invar)
    except ValueError:
        print "Value must be a floating point number."
        print "Resonance frequency being set to {} Hz as a default.\n".format(stack[8][1])

  

#                         Fill out the remainder of the header for compatability
      
    
                          # constant[0] = (text) Station: 'station name'
                          # constant[1] = (float) adccal[0]: cal constant for ch 0 (microvolts / count)
                          # constant[2] = (float) adccal[1]: cal constant for ch 1 (microvolts / count)
                          # constant[3] = (float) adccal[2]: cal constant for ch 2 (microvolts / count)
                          # constant[4] = (float) adccal[3]: cal constant for ch 3 (microvolts / count)
                          # stack[5][1] = (float) laserres: cal constant for the laser ( mV / micron)
                          # stack[6][1] = (float) lcalconst: cal constant for geometry correction factor
                          # stack[7][1] = (float) h: Damping ratio for the seismometer as measured by engineer.
                          # stack[8][1] = (float) resfreq: Free period resonance freq. as measured by engineer.

                          # Write out the new variables to the file.

    try:
        invar = raw_input('Save as new defaults? Y/N ')
        if string.lower(invar)[:1] == "y":
            with open(calcontrol,'wb') as fout:
                cal = csv.writer(fout, delimiter=',',
                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for i in range(0,len(stack)):        
                    cal.writerow(stack[i])
                    print "{0} set to = {1}".format(stack[i][0],stack[i][1])
            print "Parameters saved as new defaults."    
    except ValueError:
        print "Unable to write the defaults. Check file folder {} to see if it exists.".format(calcontrol)

    print " Cal control written to:",calcontrol
	
    return(cconstant) # Return to sigcal the updated calibration constants.



                                   # function process(): 
# Process the incoming data and return the frequency and sensitivities at that calculated frequency.
# sensor is the channel with the sensor data to be calibratied
# laser is the laser position sensor channel
# cconstant consists of:

              # cconstant[0] = (text) Station: 'station name'
              # cconstant[1] = (text) Sensor channel name    
              # cconstant[2] = (float) adccal[0]: cal constant for sensor channel (microvolts / count)
              # cconstant[3] = (text) Laser channel name
              # cconstant[4] = (float) adccal[1]: cal constant for laser channel (microvolts/count)
              # cconstant[5] = (float) laserres: cal constant for the laser resolution ( mV / micron)
              # cconstant[6] = (float) lcalconst: cal constant for geometry correction factor
              # cconstant[7] = (float) h: Damping ratio for the seismometer as measured by engineer.
              # cconstant[8] = (float) resfreq: Free period resonance freq. as measured by engineer.                                   


# delta is the sampling period in terms of seconds.
 
def process(sensor,laser,delta,cconstant):          # cconstant is a list of the calibration values. 

    Station = cconstant[0]                         # Name of Station under test
    Sensorchanname = cconstant[1]# cconstant[cconstant[13]*2+1] 
    sensor_adccal = float(cconstant[2]) # float(cconstant[cconstant[13]*2+2])# ADC channel sensitivity for sensor channel
    laserchanname = cconstant[3] # cconstant[cconstant[14]*2+1]
    laser_adccal = float(cconstant[4])  # cconstant[cconstant[14]*2+2] )       # ADC channel sensitivity for the laser channel uV/count
    laserres = float(cconstant[5])                 # CALIBRATED value from laser position sensor in mV/micron
    lcalconst = float(cconstant[6])               # Typ. 0.957, for the SM3, based on the geometry of the laser target 
                                                   # and center of mass relative to radius of moment arm
    h = float(cconstant[7])                       # typically about 0.7 but MUST be accurately measured beforehand!
    resfreq = float(cconstant[8])                 # Typically between 0.7 and 1.3 Hz. Expressed in Hz, not seconds.
    Rn = (np.pi * 2.0 * resfreq)                   # Free period as expressed in radians / second                      
    lasercal = laserres/1000                       # microns / count from the CALIBRATED laser and CALIBRATED ADC.
                                                   # Parse out the sensor and laser data
    

                                      #            
                                      # Find the period of the observed signal
                                      #

    # Create a head and tail for the file of 4096 sample apiece.
    # We will create two ratios, from the head and tail of the file
    # and use the one with the lowest standard deviation for determining
    # the one for use with the FFT
    
    sensor = signal.detrend(sensor)
    laser = signal.detrend(laser)
    sensor1 = []
    sensor2 = []
    laser1 = []
    laser2 = []
    print "The length of the sensor chunk for this file is {} samples.".format(len(sensor)/2)
    for i in range(0,len(sensor)/2):
        sensor1.append(sensor[i]) # take the first 4096 samples
        sensor2.append(sensor[(len(sensor)-(len(sensor)/2)+i)]) # Take the last 4096 samples
        laser1.append(laser[i]) # take the first 4096 samples
        laser2.append(laser[(len(laser)-(len(sensor)/2)+i)]) # take the last 4096 samples
    
    ratio1 = np.std(sensor1)*np.std(laser1)
    ratio2 = np.std(sensor2)*np.std(laser2)
    if ratio1<ratio2:                      # The chunk with the smallest standard deviation wins.
        sensor3 = sensor1
        laser3 = laser1
    else:
        sensor3 = sensor2
        laser3 = laser2
                         # Apply the ADC constants to the sensor channel data to convert to units of volts
    sensor3 = sensor_adccal*np.array(sensor3)
                         # Apply an FFT to the sensor data
                         # Generate a frequency table
                         # Find the index point where rms energy is highest
                         # Return the frequency in Hz.
    senfft   = np.fft.fft(sensor3)
    freq = np.fft.fftfreq(len(sensor3),delta) # Length of the sample set and delta is the samplerate
    idx = np.where(abs(senfft)==max(np.abs(senfft)))[0][-1]
    Frequency = abs(freq[idx])
   
                                      #
                                      # Take the sample with the largest amplitude as our center frequency. 
                                      # This only works if the signal is heavily sinusoidal and stationary 
                                      # in nature, like our calibration data.
                                      #
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
                                      # Now compensate the laser signal.
                                      # laser_adccal is the ADC in uV/count
                                      # lasercal = unit-corrected resolution of laser

    gmotion = laser_adccal*lasercal*lcalconst/gmcorrect*np.array(laser3)

                                      # Calculate the FFT for the ground motion signal
    lasfft   = np.fft.fft(gmotion)    # 
    freqlaser = np.fft.fftfreq(len(laser3),delta) # number of samples and delta is the sample rate
                                      #
                                      # Take the rms value of each signal at the main frequency only
                                      #

    sensor_rms = np.abs(np.sqrt(senfft[idx]**2)/(len(freq)/2))
    laser_rms = np.abs(np.sqrt(lasfft[idx]**2)/(len(freq)/2))

                                      # Since the FFT at a single frequency breakpoint is by definition 
                                      # the energy contributed by a sine at that frequency,
                                      # the derivative and integral are related by a factor of 2pi*f
                                      #
                                      # Calculate the equivilant rms value of the derivative and integral 
                                      # of each signal.
                                      # Integral of sensor = sensor / 2pi*f
                                      # Derivative of laser = laser * 2pi*f
                                      # in either case, the ratio works out to sensor_rms/(2pi*f*laser_rms)
    fcal = 0.0
    cal = sensor_rms/(2*np.pi*Frequency*laser_rms) # This is the calibration factor.
    if not np.isnan(cal):
        fcal = cal
    
                                      #
                                      #     Reset the ground motion back to laser displacement
                                      #     for output 
                                      #


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
                                      # 
                                      #     Validate the fields for NaN's


 
    return(Frequency,sensor_rms,laser_rms,fcal,Rn,h,gmcorrect)


######################## Start of grid_search algorithm by Hans Hartse ###################

                                 ###### LA-CC-14-079 #######
# Author: Hans Hartse, LANL : August, 2014
# Modified by D Burk, Michigan State University
# Version: 20140831
#
# Modification 20140828 : Adjust amplitude calculation to start at 2x freeperiod to 5x freeperiod
# Also correct the path of the plot file output
# Modification 20140831 : minor bug fixes to file output path, and of lmult,hmult
#
# holds the following functions:
# write_sacpz - write a SAC-style pole-zero file where input is an ObsPy "dictionary"
# find_pole_zero - grid search about MSU measured/estimated response, free-period, and damping factor
# plot_response_curves - plots amplitude and phase curves using best-fit information from grid search
# plot_misfit_results - plot an RMS misfit vs iteration number from grid search

# write a function that will take obsby resp "dictionary" info
# and create a sac pole-zero file
# add one extra zero for sac pz to declare velocity, rather than displacement



def write_sacpz(fname, resp):

# resp is the obspy data structure holding poles, zeros, and scale factor
    print "Writing the SAC poles and zeros file:\n"
    with open(fname,'w') as f:
        f.write("ZEROS {}\n".format(len(resp['zeros']) + 1 ))
        print "ZEROS: {}".format(len(resp['zeros']) + 1 )
        f.write("POLES {}\n".format(len(resp['poles'])))
        print "POLES {}\n".format(len(resp['poles']))
        for pole in resp['poles']:
            f.write("{:e} {:e}\n".format(pole.real, pole.imag))
            print "real:{:e} Imaginary:{:e}".format(pole.real, pole.imag)
        f.write("CONSTANT {:e}".format(resp['gain']))
        print "\nsensor gain constant {:2.3f} Volts/(m/sec)".format(resp['gain'])

    spz = "SAC pole-zero file is named %s" % ( fname )
    print ( "\n" )
    print spz

# done with custom sac pz write function "write_sacpz"



# start of function that does a grid search to find a response that best fits the MSU measured response
# function "find_pole_zero"
                              # Input parameters:
                              # freq_msu: List of frequencies of n terms
                              # amp_msu: List of ampltudes at those frequencies (n terms)
                              # seismometer: Seismometer description
                              # msu_freep: Measured Free-period frequency from calibration
                              # msu_damp: Measured damping ratio from calibration
                              # nsearch: Constraint options (0 = fully constrainted,1,2,3 = full grid search)
                              # coarse_search: The step size for grid searching parameters (Typ 0.1)
                              # fine_search: Step size for fine grid searching (typ 0.005)
                              # nloops: Number of iterations to try for best fit (Typ. 4)
                              # ngrids: Total number of grid points within the search to use (typ. 20)
 
def find_pole_zero(freq_msu,amp_msu,seismometer,msu_freep,msu_damp,nsearch,coarse_search,fine_search,nloops,ngrids,lmult,hmult):

# ngrids is the number of grid points to be searched for each parameter, per each "percentage" loop
                        # At nsearch = 3, grid search on amplitude, damping ratio, and free period.
    nfreqs = ngrids
    if ( nsearch < 3 ): # Set flags. Free period is constrained at nsearch = 2
        nfreqs = 1
    ndamps = ngrids
    if ( nsearch < 2 ): # Set flags. Free period & Damping ratio is constrained at nsearch = 1
        ndamps = 1
    nscales = ngrids
    if ( nsearch < 1 ): # set flags. Free period, Damping Ratio, and amplitude are all constrained.
        nscales = 1

# search the grids nloops times, first between coarse_search percent smaller than starting params 
#   and coarse_search percent larger than starting params, then, eventually search only within fine_search percent
#   of the best params found on each previous loop search

    search_range = np.linspace(coarse_search, fine_search, nloops)

# freq_msu is array holding frequency values where MSU made amp measurements
# amp_msu is array holding amplitude values measured by MSU
# note that msu_freep is the MSU estimated freee period in seconds

# now find average amplitude from MSU measurements where freq > 1 Hz
#
# edit: Change the average amplitude calculation to use frequencies greater than 
# 3x the free period frequency but less than 8x the free-period frequency.
# This program calculates only two poles & zeros: Response should be flat within
# this passband and avoids any weird issues at higher frequencies and keeps 
# calculation off the knee of the response curve in cases of high or low damping
# ratios
# - drb 08/28/2014

    count = 0
    amp_average = 0.
#    lmult = lmult/msu_freep # make it a multiplier of freeperiod in Hz (lowest)
#    hmult = hmult/msu_freep                                         # (Highest)
    
    for i, freq in enumerate(freq_msu):
        if ( freq > lmult) and (freq < hmult):  
                                      # Set frequency discriminator to msu_freep * 2 to get off the 
                                      # knee of the curve for SP instruments - drb
           amp_average = amp_average + amp_msu[i] 
           count += 1
    amp_average = amp_average / float(count)

                                      # set preliminary "best parameters"

    best_freep = msu_freep 
    best_damp = msu_damp
    best_scale = amp_average


                                      # best_fit is the RMS misfit between MSU observed 
                                      # and model amplitudes in log10 space,
                                      #    an outrageously large value, initially

    best_fit = 1000000.
    best_corner = 1/msu_freep
    best_index = 0
                                      # an index counter to keep track of the total number of searches/misfits
    j = 0
                                      # for use with later plotting
                                      # prepare array to hold total number of interation results

    misfits = np.zeros(nscales * ndamps * nfreqs * nloops)

                                      # prepare array to store each iteration number

    misfit_count = np.zeros(nscales * ndamps * nfreqs * nloops)

                                      # start of loops 

    for range in search_range:

                                      # build a list of "corner frequencies" to test
                                      # I think these "corner frequencies" - in ObsPy Speak means 1/free period of seismometer

        freep_adjust = best_freep * range
        fp_long = best_freep + freep_adjust
        fp_short = best_freep - freep_adjust

                                      # the case where free period is held constant at the MSU-supplied value

        if ( nsearch < 3 ):
            fp_long = best_freep
            fp_short = best_freep

                                      # np.linspace will create an array from low_freq to high_freq over nfreqs of even spacing

        corners = np.linspace(1./fp_long, 1./fp_short, nfreqs)
        print ( "\nsearching free periods between %f and %f seconds" % ( fp_long, fp_short ) )

                                      # build a list of damping factors to test

        damp_adjust = best_damp * range
        low_damp = best_damp - damp_adjust 
        high_damp = best_damp + damp_adjust
        if ( high_damp >= 1.0 ):
            print ( "\nwarning - damping factor is %f - must be below 1.0 - setting damping to 0.9999" % ( high_damp ) )
            high_damp = 0.9999
        if ( nsearch < 2 ):
            low_damp = best_damp
            high_damp = best_damp

        damps = np.linspace(low_damp, high_damp, ndamps)
        print ( "searching damping factors between %f and %f" % ( low_damp, high_damp ) )

                                      # build a list of scale factors to test

        scale_adjust = best_scale * range
        low_scale = best_scale - scale_adjust 
        high_scale = best_scale + scale_adjust
        if ( nsearch < 1 ):
            low_scale = best_scale
            high_scale = best_scale
            nscales = 1
        scales = np.linspace(low_scale, high_scale, nscales)
        print ( "searching scale factors between %f and %f" % ( low_scale, high_scale ) )

                                      # here are the grid search loops, over corners, dampings, and scales

        for corner in corners:   
            for damp in damps:
                for scale in scales:

                                      # the key obspy function to find inst resp based on "corner frequency" and damping constant 
                                      # cornFreq2Paz takes an instrument's corner freq and damping factor to produce
                                      #   an Obspy-style paz file

                    resp = sim.cornFreq2Paz(corner, damp) 
                    resp['gain'] = scale
                    amp_predicted = np.zeros_like(freq_msu)
                    for i, freq in enumerate(freq_msu):
                        amp_predicted[i] = sim.paz2AmpValueOfFreqResp(resp, freq) 
    
                    misfit = np.linalg.norm(np.log10(amp_msu) - np.log10(amp_predicted))
                    misfits[j] = misfit
                    misfit_count[j] = j + 1
       
                    if ( misfit < best_fit ):
                       best_fit = misfit
                       best_corner = corner
                       best_damp = damp
                       best_scale = scale
                       best_index = j

                    j = j + 1

                                      # find the best free period, which is 1/best_corner
                                      # this happens at the end of a particlar grid search loop

        best_freep  = 1./best_corner 

                                      # end of all loops

                                      # find poles and zeros using best corner freq, damp and scale 

    resp = sim.cornFreq2Paz(best_corner, best_damp) 
    resp['gain'] = best_scale
    return(resp, best_freep, best_damp, best_scale, amp_average, misfits, misfit_count, best_index) 
                                      # end of function "find_pole_zero"







#
#
                             # start of function "plot_response_curve"
                             # function plot_response_curve
#
#

def plot_response_curves(resp, freq_msu, amp_msu, best_freep, best_damp, best_scale, msu_freep,\
msu_damp, amp_average, amp_label, seismometer, sac_pz_file,wdir):

                             # build an array of zeros with same length as freq_msu

    amp_predicted = np.zeros_like(freq_msu)

                             # loop over the frequencies present in the msu data file one at a time
                             # to find the amplitudes predicted for a given frequency 
                             # based on the best resp file

    for i, freq in enumerate(freq_msu):
        amp_predicted[i] = sim.paz2AmpValueOfFreqResp(resp, freq) 

                             # this code taken straight from the Obspy webpage examples 
                             # numbers for obspy to create a resp curve, based on an fft of a time series
                             # with sample rate of 0.01

    samp_rate = 0.01
    npts = 16384

                             # obtain "continuous" amp and freq values from obsby function to display continuous response curve

    poles = resp['poles']
    zeros = resp['zeros']
    h, f = sim.pazToFreqResp(poles, zeros, best_scale, samp_rate, npts, freq=True)

                             # plotting amp vs freq

    plt.figure()

#plt.subplot(121)
                             # plot the continuous response curve, and the msu data, 

    plt.loglog(f, abs(h), freq_msu, amp_msu, 'go', markersize=6 )

                             # plot the predicted amplitudes at the MSU frequencies

    plt.loglog(freq_msu, amp_predicted, 'ro', markersize=4 )

                             # labels

    plt.xlabel('Frequency [Hz]')

                             # this str function is part of the standard Python, no need to "import" a special "package"

    plt.ylabel( str(amp_label) )
    plt.suptitle('Frequency vs Amplitude: Channel ' + str(seismometer) )

                             # plot over range from 2/3 * minimum frequency to 2.0 * maximum frequency  
                             # and over range from 2/3 * minimum amplitude to 2.0 * maximum amplitude  

    plx_min = 0.05 # freq_msu[0] * 0.66
    plx_max = 40.0 # freq_msu[len(freq_msu) - 1] * 2.00
    ply_min = 0.10 # amp_msu[0] * 0.66
    ply_max = 1000.0 # amp_msu[len(freq_msu) - 1] * 2.00
    plt.axis([plx_min, plx_max, ply_min, ply_max])

    freep_per = 100. * ( abs ( best_freep - msu_freep ) / msu_freep )
    damp_per = 100. * ( abs ( best_damp - msu_damp ) / msu_damp )
    scale_per = 100. * ( abs ( best_scale - amp_average ) / amp_average )
    rsp = ""
    cdt = "Calibration date = "+ (time.strftime("%d/%m/%Y %H:%M:%S"))
    tfp = "free period = %.3f Hz (%.2f%% MSU: %.3f)" % ( 1./best_freep, freep_per, 1./msu_freep )
    print ( "\n" )
    print tfp
    tdr = "damping = %.3f (%.2f%% MSU: %.3f)" % ( best_damp, damp_per, msu_damp )
    print tdr
    tsf = "scale = %.3f Volts/(m/sec)( Avg. amp: %.2f)" % ( best_scale, amp_average )
    print tsf
    spz = "File: %s" % ( sac_pz_file )
    #f.write("ZEROS {}\n".format(len(resp['zeros']) + 1 ))
    zzz = "ZEROS: {}".format(len(resp['zeros']) + 1 )
     #   f.write("POLES {}\n".format(len(resp['poles'])))
    ppp = "POLES {}\n".format(len(resp['poles']))
    for pole in resp['poles']:
      #      f.write("{:e} {:e}\n".format(pole.real, pole.imag))
        rsp = rsp+"real:  {:e} Imaginary:  {:e}\n".format(pole.real, pole.imag)
       # f.write("CONSTANT {:e}".format(resp['gain']))
    print "\nsensor gain constant {:2.3f} Volts/(m/sec)".format(resp['gain'])
 

                             # post results as text lines on the plot

    xtext = plx_min * 7.
    ytext = ply_min * 60
    plt.text( xtext, ytext, cdt )
    ytext = ply_min * 40
    plt.text( xtext, ytext, tfp )
    ytext = ply_min * 30
    plt.text( xtext, ytext, tdr )
    ytext = ply_min * 20
    plt.text( xtext, ytext, tsf )
    ytext = ply_min * 10
    plt.text( xtext, ytext, zzz )
    ytext = ply_min * 5
    plt.text( xtext, ytext, ppp )
    ytext = ply_min * 2
    plt.text( xtext, ytext, rsp )

                             # post some symbols and text for a legend

    amp_symbol = np.zeros(1)
    amp_symbol[0] = best_scale * 1.0
    freq_symbol = np.zeros(1)
    freq_symbol[0] = freq_msu[0]
    plt.loglog(freq_symbol, amp_symbol, 'go', markersize=6 )
    plt.text( freq_symbol[0] * 1.1, amp_symbol[0], 'Measurement', va='center' )
    amp_symbol[0] = best_scale * 0.70
    freq_symbol[0] = freq_msu[0]
    plt.loglog(freq_symbol, amp_symbol, 'ro', markersize=4 )
    plt.text( freq_symbol[0] * 1.1, amp_symbol[0], 'Model Best Fit', va='center' )
    plt.grid(True, which='major')
    plt.grid(True, which='minor')

  #  cconstant,fileopts = getoptions()           # Use the getoptions def to parse the command line options.
  #  wdir     = fileopts[0]            # working directory

    fig = wdir+"\\"+seismometer + '_freq_v_amp' + '.png' # Place it in current working directory - drb
    txt = "best-fit freq. vs ampl. plot: %s" % ( fig )
    print "\n"
    print txt
    plt.savefig( fig )

    plt.show()
#    plt.close()


                             # plotting phase vs freq, not sure how much this can be trusted

#plt.subplot(122)

    plt.figure()

                             #take negative of imaginary part

    phase = np.unwrap(np.arctan2(-h.imag, h.real))
    plt.semilogx(f, phase)
    plt.xlabel('Frequency [Hz]')

    plt.ylabel('Phase [radians]')

                             # title, centered above both subplots

    plt.suptitle('Frequency vs Phase: Seismometer ' + str(seismometer) )
    plt.axis([0.004, 100, -3.5, 0.5])

                             # make more room in between subplots for the ylabel of right plot

#plt.subplots_adjust(wspace=0.3)
    plt.grid(True, which='major')
    plt.grid(True, which='minor')
    fig = wdir+"\\"+ seismometer + '_freq_v_phase' + '.png' # save in data directory
    txt = "plotted best-fit frequency vs phase results - saved in file: %s" % ( fig )
    print "\n"
    print txt
    plt.savefig( fig )
#    plt.show()
#    plt.close()

# end of function plot_response_curves




# start function to plot iteration number vs misfit for grid search work

def plot_misfit_results(misfits,misfit_count,seismometer,best_index):    

# plotting count vs misfit for final grid search 

    misfit_max = np.amax(misfits)
    misfit_min = np.amin(misfits)
    j = len(misfit_count)
    plt.figure()

#plt.subplot(121)

    plt.plot(misfit_count, misfits, 'bo', markersize=4 )
    plt.plot(misfit_count[best_index], misfits[best_index], 'r^', markersize=8 )
    plt.xlabel('Grid Search Interation Count')
    plt.ylabel( 'RMS Misfit in Log10 Space' )
    plt.suptitle('Final Grid Search: Seismometer ' + str(seismometer) )
    plt.axis([-5, j + 5, misfit_min * 0.9, misfit_max * 1.1])
    plt.grid(True, which='major')
    plt.grid(True, which='minor')
    fig = os.cwd()+seismometer + '_misfit' + '.png'
    txt = "plotted rms misfit vs iteration number - saved in file: %s" % ( fig )
    print "\n"
    print txt
    plt.savefig( fig )
    plt.show()
    plt.close()



                                           
def grid_search(outfile,nsearch,lmult,hmult,wdir):                 # Subroutine grid search
                                          # Bring in the data and plot.                
                                          #
                                          # Prepare to make the poles and zeroes from Hans Hartse gridsearch algorithm
                                          # Set up the control constants.
#    print"Grid search will iterate through several scenarios in order to find "
#    print"a best fit poles & zeros combination to describe the sensitivity curve."
#    print"\nThere are several options for this search:"
#    print"Option 0: Constrain all parameters to the calibration file (no grid search)"
#    print"Option 1: Optimize amplitude but constrain damping ratio and free period"
#    print"Option 2: Optimize amplitude, damping ratio but constrain free period"
#    print"Option 3: Optimize for amplitude, damping ratio and free period"
#    print"\n Most calibrations are best served with option 1.\n"

#    Inputstring = raw_input("\n\n Choose grid search option: 0,1,2, or 3):")
#    if (Inputstring == ""):
#	Inputstring = 2        # use the default
#    nsearch = int(Inputstring) # use measured freeperiod 
					  # 0: Full constraint on grid search to use MSU-measured amplitudes, damping ratio and free period.
                                          # 1: Optimize for amplitude w/i passband but constrain damping ratio and free period.
                                          # 2: Optimize amplitude w/i passband, optimize damping ratio, but constrain free period.
                                          # 3: Grid search for optimum amplitude, damping ratio AND free period
    coarse_search = 0.10                  # Typically 0.10
    fine_search = 0.005                   # Typically 0.005
    nloops = 6                            # Number of iterations through the grid (typically 4 or 5)
    ngrids = 21                           # Number of steps (typically 20)
    amp_units = "V*sec/m"
    amp_label = "Amplitude [" + amp_units + "]"

#    Inputstring = raw_input("What is the lower frequency (Hz) for averaging amplitude? \n (should be higher than the resonance freq.)")
#    if (Inputstring == ""):#
#	Inputstring = "1.5"        # use the default    
#    lmult = float(Inputstring) # Lower freq. bandpass multiple (typically 2)
#    Inputstring = raw_input("what is the upper frequency? (I sugggest 5.0 Hz)")
#    if (Inputstring == ""):
#        Inputstring = "5.0"
#    hmult = float(Inputstring) # higher freq. bandpass multiple (typically 5)
                                          # Gather the relevant information from the output file
    fdata = load(outfile)
    header = fdata[0]                     # The header contains the initial constants used for creation of the datafile
                                          # and includes the damping ratio, free period frequency, and channel calibration information
                                          # in this order:
    seismometer = fdata[0][0][0]          # fdata[0][0][0]  # Station name
                                          # fdata[0][0][1]  # Sensor name
                                          # fdata[0][0][2]  # Channel 0 ADC sensitivity in microvolts / count
                                          # fdata[0][0][3]  # Laser name
                                          # fdata[0][0][4]   # Laser ADC sensitivity
                                          # fdata[0][0][5]  # Laser position sensor in millivolts/micron
                                          # fdata[0][0][6] # Lcalconstant geometry correction factor
    msu_damp = float(fdata[0][0][7])     # fdata[0][0][7] # h damping ratio
    msu_freep = 1/float(fdata[0][0][8])  # fdata[0][0]8] # Free period oscillation in Seconds, not Hz (as stored in cal file).

    channel = seismometer+'_CH_'+fdata[0][0][1]
    freq_msu = []                         # Initialize the frequency array
    amp_msu = []                          # Initialize the matching amplitude array

    for i in range(0,len(fdata[1])):      #        Build the list of frequencies and sensitivities from the file.
        freq_msu.append(float(fdata[1][i][0]))     # Field 0 is the frequency
        amp_msu.append(float(fdata[1][i][1]))      # Field 1 is the average sensitivity

                                          #    plot_curve(Station,Frequencies,Sensitivities,Freeperiod,h)
                                          #    plot_curve2(Station,Frequencies,Calint,Calderiv,Freeperiod,h)

                                          # Perform the grid search and create the curve

    (resp,best_freep,best_damp,best_scale,amp_average,misfits,misfit_count,best_index) = \
     find_pole_zero(freq_msu,amp_msu,channel,msu_freep,msu_damp,nsearch,\
     coarse_search,fine_search,nloops,ngrids,lmult,hmult)

                                          # Create the sac poles & zeros file

    sac_pz_file = os.getcwd() +'\\'+ channel + '.sacpz' # Set the file name to whatever station name is.
    write_sacpz(sac_pz_file,resp)

                                          # Plot the data for the user.

    plot_response_curves(resp,freq_msu,amp_msu,best_freep,best_damp,best_scale,\
    msu_freep,msu_damp,amp_average,amp_label,channel, sac_pz_file,wdir)



##############################################################################################










def main():
                                      #           MAIN PROGRAM BODY
                                      # Sigcal.py target_directory filetype station MYSTA
                                      # where, filetype can be either a csv or a sac file.
                                      # If station is used, the next option MUST be a station name 
                                      # that is resident in the file name, and the file type must
                                      # be a sac file type.
                                      # example: python sigcal.py c:/seismo/Calibration/msu_north csv
                                      #          python sigcal.py c:/seismo/Calibration/msu_north station MSU
                                      # 
                                      # Note that the channel to be calibrated is designated in the cal 
                                      # control file.

    cconstant,fileopts = getoptions()           # Use the getoptions def to parse the command line options.
    wdir     = fileopts[0]            # working directory
    filelist = fileopts[1]            # the file list that complies to the file type or station name
    calfile  = fileopts[2]            # The cal control file location
    outfile  = fileopts[3]            # The location of the ascii output file
    filetype = fileopts[4]            # The type of files to be processed.
    nsearch = 1 # Default grid search type - Optimize amplitude only.
    lmult = 1.70 # Default Lower frequency of grid search average amplitude calculation
    hmult = 5.0 # Default upper frequency of grid search average amplitude calculation
    

#    print " calibration file: '{}'".format(calfile)
#    print " output file : '{}'".format(outfile)
#    print " The selected file type is: {} ".format(filetype)    
    print " Cal control file: {}\n\n".format(calfile)
#    print " The length of the file list is {} files.".format(len(filelist))
#    for i in range(0,len(filelist)):
#        print " File # {0}: '{1}' ".format(i,filelist[i])
    outlog = outfile+".log"
                                                           #    constant = getconstants(calfile)
#    cconstant = getcal(calfile)                        # Generate a list of the calibration constants
                                                           # 
                                                           # Create the header for the calibration output file.
                                                           # Header contains the station name, ADC cal constants,
                                                           # Laser cal constant, the geometric correction factor,
                                                           # the damping ratio, and the free period frequency.


                                                           #
                                                           # Now loop through the directory of csv files to build the
                                                           # calibration curve

#    if filetype == "csv":

 #       frequency = []  
 #       sensor = []
 #       laser = []
 #       calnum = []
 #       filenames = []
 #       rn = []
 #       h = []
 #       gm_correct = []
 #       for n in range(len(filelist)):                     # Parse through directory for all .csv files
 #           if ".csv" in filelist[n]:                      # Skip any files that are not a .csv
 #               infile = wdir+filelist[n]                       # Set the input file from the file listing if it is a .csv
 #               print "Infile set to: ",infile

                # csvload the file to return the sensor data, laser data, and cal constants, and the delta function.
                # csvload requires infile name, sensor channel, and laser channel designators.
                # sensor channel is cal_constants[13]
                # laser channel is cal_constants[14]
                # csvload returns a three-element list: sensor[], laser[], and delta(float) 
 #               data = csvload(infile,cal_constants[13],cal_constants[14])

                # data[0] is the sensor data 
                # data[1] is the laser data 
                # data[2] is the delta ( sample period in seconds)
                # Process input arguments are sensor data, laser data, delta and cal_constants
                # Process the file and output to outfile based on parameters
  #              (freq,senrms,lasrms,cal,resonance,damprat,gm_c) = process(data[0],data[1],data[2],cal_constants)
 
  #              frequency.append(freq)
  #              sensor.append(senrms)                 
  #              laser.append(lasrms)
  #              calnum.append(cal)
  #              rn.append(resonance)
  #              h.append(damprat)
  #              gm_correct.append(gm_c)
  #              filenames.append(infile)

    if filetype == "sac":
        frequency = []  
        sensor = []
        laser = []
        calnum = []
        filenames = []
        rn = []
        h = []
        gm_correct = []

        senchan = cconstant[1]   # cal_constants[((cal_constants[13]*2)+1)] # This points at the name of the sensor channel
        lsrchan = cconstant[3]   # cal_constants[((cal_constants[14]*2)+1)]  # Name of the laser channel
        (sensorfiles,laserfiles) = sacparse(wdir,filelist,senchan,lsrchan) # returns a two item list of matched file names for the channel pair
                                                           # create a list of matched channel files for each frequency
        for n in range(0,len(sensorfiles)):
            data = sacload(sensorfiles[n],laserfiles[n],senchan,lsrchan) # This should return two lists, which are the sensor data(sacfiles[0], 
                                        # the laser data, and the delta.
            infiles = sensorfiles[n]+';'+laserfiles[n]
            
            (freq,senrms,lasrms,cal,resonance,damprat,gm_c) = process(data[0],data[1],data[2],cconstant) # cal_constants) # Process the file and output to outfile based on parameters
            # data[0] is the sensor data 
            # data[1] is the laser data 
            # data[2] is the delta ( sample period in seconds)
            # Process input arguments are sensor data, laser data, delta and cal_constants
            frequency.append(freq)
            sensor.append(senrms)
            laser.append(lasrms)
            calnum.append(cal)
            rn.append(resonance)
            h.append(damprat)
            gm_correct.append(gm_c)
            filenames.append(infiles)

    if filetype == "css":                    # Start working on bringing in the css file format
        frequency = []  
        sensor = []
        laser = []
        calnum = []
        filenames = []
        rn = []
        h = []
        gm_correct = []
        senchan = cconstant[1]  #  cal_constants[((cal_constants[13]*2)+1)] # This points at the name of the sensor channel
        lsrchan = cconstant[3]  #  cal_constants[((cal_constants[14]*2)+1)] 
		# Remember that the file name references the wfd containing the file names and they all get loaded at once.
		# So, we need to open the wfd here. Then, we need to parse through the paired streams and feed them into the loader.
		# This IS NOT like the SAC file or miniseed at all. The user must ensure that there is only one wfd in the cal directory.
		# Create a css parse definition that will:

		# - Make a list of paired channelsets
		
		#cssparse should return:
		# The streams (css_stream)
		# The list of paired channel streams (element list): streamlist[0] - sensor, streamlist[1] laser
		# 
        for i in range(0,len(filelist)): # each file is a list of files. 
		    # For each file, first audit the file.
			# - Audit the wfd wfdaudit(cwd,wfdin) return--> wfdout which is the filename of the cleaned wfd
            wfd =read(wfdaudit(wdir,filelist[i]),format = "css")

			# Then, load the streams from that file
            streamlist0 = []
            streamlist1 = []
            print senchan, lsrchan
            for j in range(0,len(wfd)):
                if senchan == wfd[j].stats.channel:
                    streamlist0.append(j)
                if lsrchan == wfd[j].stats.channel:
                    streamlist1.append(j)
            streamlist = [streamlist0,streamlist1] # Streamlist is a list of streams matching sensor and laser
					
		
            for n in range(0,len(streamlist[0])): # n represents the number of paired channel streams are located in the directory
		    # cssload needs to bring in the streams, parse the time-history into two lists, and output the delta.
                data = cssload(wfd[streamlist[0][n]],wfd[streamlist[1][n]]) # The data is derived from the matched streams.
            #     data[0] is the sensor data 
			
            #     data[1] is the laser data 
            #     data[2] is the delta (sample period in seconds) 
                (freq,senrms,lasrms,cal,resonance,damprat,gm_c) = process(data[0],data[1],data[2],cconstant) # cal_constants) # Process the file and output to outfile based on parameters

            # Process input arguments are sensor data, laser data, delta and cal_constants

                frequency.append(freq)
                sensor.append(senrms)
                laser.append(lasrms)
                calnum.append(cal)
                rn.append(resonance)
                h.append(damprat)
                gm_correct.append(gm_c)
                filenames.append(filelist[i])
#    print "length of frequency array is {} items.".format(len(frequency))

    if len(frequency)<>0:

                                          # Write out the header for the csv output file containing the calibration curve data

        with open(outfile,'wb') as csvfile:   # use 'wb' in place of 'a' if you want to overwrite the file.
            outrow = csv.writer(csvfile, delimiter = ",",
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            outrow.writerow(cconstant) # cal_constants)

                                          # Write out the calibration matrix to the csv calibration output file
                                          
        with open(outfile,'a') as csvfile:    # use 'wb' in place of 'a' if you want to overwrite the file.
            for n in range(len(frequency)):
                print("fcal calculates to: {0:.3f} for frequency {1:.2f} Hz".format(calnum[n],frequency[n]))
                if calnum[n]<>0.00:
                    outrow = csv.writer(csvfile, delimiter = ",",
                                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    outrow.writerow([frequency[n],calnum[n],sensor[n],laser[n],rn[n],h[n],gm_correct[n],filenames[n]])
                else:
                    print "    entry not written to cal file due to bad amplitude or frequency calculation."
         
            print("output sent to {} \n\n".format(outfile))
    
        grid_search(outfile,nsearch,lmult,hmult,wdir)
    else:
        print "No data files of the appropriate format were found within this directory."


#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()