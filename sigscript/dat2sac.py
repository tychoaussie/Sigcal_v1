__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20150910"
__license__ = "MIT"
# Fixed bug in convert definition that didn't like being in the same working directory as the data.
# Fixed bug in sac write that wouldnt work in the 32-bit installations.


import os
import sys
import csv
                                           #from scipy import signal
                                           #from scipy.integrate import simps
                                           #import pylab as plt
import numpy as np
                                           #import scipy as sp
import string                              # We use the string.find utility for file naming
import time                                # we use the sleep function to enable conversion of the DAT
import subprocess                          # used for the execution of command-line programs
from obspy.core import read, Trace, Stream, UTCDateTime
from obspy.sac import SacIO

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

class dat2sac(object):
    '''dat2sac.py is a utility for batch converting Symmetric Research csv into sac files
       for a whole directory. It uses the 2010 build of dat2asc.exe as provided from symmetric
       and converts the file, followed by a rename of the csv file. It has only one command line
       switch, and that is to point it at a directory for converting the dat files.

       The program will convert non-sequential DAT files into separate csv files, and all
       sequential files will be concatenated into a single csv file. It is therefore important
       to rename or move any sequential csv file that you do not wish to include within the csv.
        
       One critical requirement is that dat2asc.exe (2010 build) exists in the
       directory as such: "c:\Anaconda\dat2asc.exe"

       Syntax: dat2csv target_directory  

       

       Typical useage:
       <ObsPy> C:\Anaconca\sigscript> python Dat2sac.py c:/calibration/station/ 

    '''


                            # Function getcal: Retrieve the calibration control file
def getcal(calcontrol): 
    # calcontrol needs to include calibration constants as well as the station name and the channel name, and the particular constant for that channel.
    # Thus a third line is necessary that specifies the channel identifier and the channel assignment of that channel.
    # Channel name is located in the top row already, and it's position is associated with the sensitivity. So the third row designates the UUT and the
    # laser position channel.
    cconstant = ["MSU","CH0",1.0,"CH1",1.0,"CH2",1.0,"CH3",1.0,1.0,1.0,0.707,1.0,1,2]
    try:
        with open(calcontrol,'r') as fin:
            list = csv.reader(fin)
            rowcnt=0            
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
            
                selection.append(int(raw_input('Choose the channel number representing the unit under test:  ')))
                selection.append(int(raw_input('Choose the channel number representing the laser position sensor:  ')))

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
    except:
        print "Calibration control file not found!\n"
        print "You may enter the calibration information manually, or else press <ctrl>C"
        print "then place the cal control file in the directory containing the data files."
        cconstant = ["","",1.0,"",1.0,"",1.0,"",1.0,1.0,1.0,1.0,1.0,2,3]
        try:
            cconstant[0] = raw_input('Enter the station name: ')# (test) Station name
            print "Enter the four channel names, starting with channel 0:\n"
            cconstant[1] = raw_input('Channel 0: ') # (text) Channel name for CH0
            cconstant[3] = raw_input('Channel 1: ') # (text) Channel name for CH1
            cconstant[5] = raw_input('Channel 2: ') # (float) adccal[1]: cal constant for ch 1 (microvolts / count)
            cconstant[7] = raw_input('Channel 3: ') # (text) Channel name for CH2
#            print "Enter the channel calibration constants for the above four channels.\n"
#            cconstant[2] = raw_input('CH0 calibration constant (uV/count): ') # (float) adccal[2]: cal constant for ch 2 (microvolts / count)
#            cconstant[4] = raw_input('CH1 calibration constant (uV/count): ')              # (text) Channel name for CH3
#            cconstant[6] = raw_input('CH2 calibration constant (uV/count): ') # (float) adccal[3]: cal constant for ch 3 (microvolts / count)
#            cconstant[8] = raw_input('CH3 calibration constant (uV/count): ')  # (float) laserres: cal constant for the laser ( mV / micron)
#            cconstant[9] = raw_input('Enter the resolution for the laser position sensor (mV/micron): ')
#            print "The laser geometry correction ratio is the ratio of distance from pendulum pivot to center of mass"
#            print "divided by the distance from pendulum pivot to the measurement point of the laser beam."
#            cconstant[10] = raw_input('What is the laser geometry correction constant ratio? ') # (float) lcalconst: cal constant for geometry correction factor
#            cconstant[11] = raw_input('Enter the measured damping ratio for the seismometer under test. ') # (float) h: Damping ratio for the seismometer as measured by engineer.
#            cconstant[12] = raw_input('Enter the resonance frequency of the seismometer under test. (in Hz). ') # (float) resfreq: Free period resonance freq. as measured by engineer.
#            cconstant[13] = raw_input('Enter the channel number (0 through 3) for the seismometer under test. ')    # channel number of channel being tested
#            cconstant[14] = raw_input('Enter the channel number (0 through 3) repesenting the laser position sensor. ')     # channel number of the laser position sensor
        except:
           print "Error during manual input of the calibration constant parameters.\n"
           print "Setting the paramters to default settings."
           cconstant = ["MSU","CH0",1.0,"CH1",1.0,"CH2",1.0,"CH3",1.0,1.0,1.0,0.707,1.0,1,2]
    return(cconstant)

def load(infile): # Load the csv file
    with open(infile,'r') as fin:
        list = csv.reader(fin)
        rowcnt=0
        stack = []
        header = []
        for row in list:
#
#          Bring in the data and create a list of lists, each of which
#           corresponds with a given sample.
#
            if rowcnt == 0:
                header.append(row)
            else:
                stack.append(row)
            rowcnt = 1
    return(header,stack)



                        # process dat2sac
                        # Converts a dat file into a sac file format

def csv2sac(infile,calcontrol):
#
    Channel = ["","","",""]
    units = ['Counts  ','Counts  ','Counts  ','Counts  ']
    comment = ['Velocity','Velocity','Velocity','Velocity']
    (header,stack) = load(infile)
#    header = fdata[0]
#    stack = fdata[1]
    datetime = stack[0][13]+","+stack[0][14]
    Frac_second = float(stack[0][15])
    St_time = time.strptime(datetime,"%Y/%m/%d,%H:%M:%S")
    cconstant = getcal(calcontrol) # This will need to be fixed when using targeted directories.
    Station = cconstant[0]
    outfile = infile[0:string.rfind(infile,'.')]
    for i in range(0,4):
        Channel[i]=cconstant[(2*i)+1]

    Samplecount = len(stack)
    print "Sample count stands at {} samples.".format(Samplecount)
    Delta = (float(stack[len(stack)-1][12])-float(stack[0][12]))/len(stack)
    sacfile = outfile[:string.find(infile,'.')]+'{}'.format(i)+'.sac'
        #
        # stack[1] = channel 1 time history
        # .
        #
        # stack[4] = channel 4 time history
        #


    for i in range(0,4): # Build each channel
        t = SacIO()
        b = np.arange(len(stack),dtype=np.float32)   #   Establishes the size of the datastream
        for n in range(len(stack)):        #   Load the array with time-history data
            b[n] = np.float32(stack[n][i+1]) #   Convert the measurement from counts to volts.
        t.fromarray(b)

             #                     set the SAC header values
        t.SetHvalue('scale',1.00) # Set the scale for each channel. This one is important to declare.
        t.SetHvalue('delta', Delta)
        t.SetHvalue('nzyear',St_time.tm_year)
        t.SetHvalue('nzjday',St_time.tm_yday)
        t.SetHvalue('nzhour',St_time.tm_hour)
        t.SetHvalue('nzmin',St_time.tm_min)
        t.SetHvalue('nzsec', St_time.tm_sec)
        t.SetHvalue('nzmsec', int(Frac_second*1000))
        t.SetHvalue('kstnm',Station)
        t.SetHvalue('kcmpnm',Channel[i])
        t.SetHvalue('idep',4) # 4 = units of velocity (in Volts)
                              # Dependent variable choices: (1)unknown, (2)displacement(nm), 
                              # (3)velocity(nm/sec), (4)velocity(volts), 
                              # (5)nm/sec/sec
        t.SetHvalue('kinst',comment[i-1])       # Instrument type
        t.SetHvalue('knetwk','CSV2SAC ')         # Network designator
        t.SetHvalue('kuser0',units[i-1])        # Place the system of units into the user text field 0
        f = outfile+"_{}.sac".format(Channel[i])
        with open(f,'wb') as sacfile:
            t.WriteSacBinary(sacfile)
        print " File successfully written: {0}_{1}.sac".format(outfile,Channel[i])       
        sacfile.close()
  


def convert(infile):
    print infile
    target = infile[string.rfind(infile,"\\")+1:string.find(infile,'.')]+".csv"
    outfile = infile[:string.find(infile,'.')]+".csv"
    dat2csvfile = infile[:string.rfind(infile,"\\")+1]+"Dat2asc-301-Data.csv"
    calcontrol = infile[:string.rfind(infile,"\\")+1]+"calcontrol.cal"
    subprocess.call(["c:\\Anaconda\\dat2asc.exe",infile,"csv"])
    print "convert {} to: \n".format(dat2csvfile)
    print outfile

    subprocess.call(["ren",dat2csvfile,target],shell=True)
    csv2sac(outfile,calcontrol)


def main():
                                      #           MAIN PROGRAM BODY
                                      #  Parse the command line switches
                                      # Commmand example: c:\Anaconda>Python.exe Sigcal.py c:\seismo\caldata\momo
                                      # where momo is the working directory containing the csv files
                                      # as well as the calibration control file, c:\seismo\caldta\calcontrol.csv
                                      # The third option can designate an optional location for the calcontrol file.
                                      #
    optioncount = len(sys.argv)
    outputfile_defined = False
    filelist = []
    dir=""
    infile = ""
    directory = os.getcwd()
    directory = directory.replace("/","\\")
    print "This is the directory name as taken from the computer:",directory
    if optioncount > 1:
        
        
        directory = sys.argv[1]
        directory = directory.replace("/","\\")
        print directory
        if directory[-1:] !="\\":
                directory = directory+"\\"
        try:
            filelist = os.listdir(directory)            
        except:
            print "Command line parameter must consist of a valid directory. {}".format(directory)
            sys.exit(0)
    else:
        if directory[-1:] !="\\":
                directory = directory+"\\"
        filelist = os.listdir(directory)
    
                                           
    
    if ".dat" in filelist[0]:
        infile = directory+filelist[0]
        convert(infile)

    for n in range(1,len(filelist)):                                
        if ".dat" in filelist[n]:
            try:                    
                filenum1= int(filelist[n][string.rfind(filelist[n],'.')-8:string.rfind(filelist[n],'.')])
                try: 
                    filenum0= int(filelist[n-1][string.rfind(filelist[n-1],'.')-8:string.rfind(filelist[n-1],'.')]) # If 
                    if ((filenum1-filenum0)!=1):                    # Skip sequential files that have likely been converted with prev. file
                        infile = directory+filelist[n]
                        print "Converting: ",infile
                        convert(infile)
                except:                                             # previous file failed but this one does not.
                    infile = directory+filelist[n]     
                    print "Converting: ",infile
                    convert(infile)
            except:
                print "File {} does not comply to standard symmetric research naming formats and must be manually converted.".format(filelist[n])

#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()
 