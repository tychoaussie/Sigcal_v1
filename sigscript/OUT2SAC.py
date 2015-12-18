# -*- coding: utf-8 -*-

'''The MIT License (MIT)

Copyright (c) 2013 Daniel Burk
during my time on campus during a summer of delightful albeit, uncompensated labor.
Michigan State University.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''


__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20150817"
__license__ = "MIT"

# -*- coding: utf-8 -*-

# Beta version to try and bring in calibrations, if they exist.
# 20150817 - updated to run on latest Obspy version plus bring in channel names into
# the SAC filename. Also correct the start time bug by using the encoded start time
# from the first two samples of the timing signal.

import sys, os, csv, time, string, numpy as np
from obspy.core import read, Trace, Stream, UTCDateTime
from obspy.sac import SacIO

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


#class OUTconvertError(Exception):
#
#   def __init__(self, error_name, error_text):
#       self.args = (error_name, error_text)
#       self.error_name = error_name
#       self.error_text = error_text
#
#   def __str__(self):
#       return repr('{0}: {1}'.format(self.error_name, self.error_text)


class OUTconvert(object):
    '''OUT2SAC is a utility for converting OUT binary files as generated by
       the Russian seismic networks that use Symmetric Research seismic hardware.
       The OUT files are converted to SAC file format for integration within other
       seismic analysis tools. At present, only OUT files generated in version 1.14 
       and later are compatable with the converter. Future iterations of this code
       should also include early OUT files as well as conventional Symres DAT files.

       Syntax:     OUT2SAC infile (outfile)
       or,
       Syntax:     OUT2SAC Targetdirectory (destinationdirectory)
       
       where:      infile may be either a file name or a file directory.
       Outfile is optional. If no outfile is specified, SAC files shall be
       named the same as the original infile but with a "_x" on the end of file
       name where x represents the sequence of each channel within the series.
       It is a requirement that the infile be co-located in a directory
       which also contains the file "vdaq.txt" that describes the data
       file header information.

       Useage requirements: You must have installed both Python27, ObsPy, 
       and NumPy on your machine in order to run this package. Dependencies
       include the os, csv, time, string, numpy, and obspy modules.

       Typical useage:
       c:\Python27\scripts> python OUT2sac.py c:/data/20130816112559.OUT
       c:\Python27\scripts> python OUT2sac.py c:/data c:/data/outputfiles

       '''
#
#    OUTconvert is a utility for converting ascii files generated by Symmetric Research 
#       and Russian network .OUT files into a ObsPy compatable format. 
#       Once reformatted, ObsPy may be used to convert the data into SAC or even
#       Miniseed format.
#       
#       Useage: Activate Python's ObsPy package, then from the command prompt
#       specify the target file and the output filename. If no output filename
#       is provided, the default will be called output.ASC in your current
#       working directory. If a directory is specified, all OUT files found within
#       will be converted. If no command line options are specified, the format will
#       default to SAC-BIN. The target directory in all cases must contain at least
#       one OUT file and one vdaq.txt file with appropriate header information.#
#
#       Syntax: OUTconvert infile_name outfile_name (-sac) (-seed)#
#
#       -sac is an optional command line switch for also creating a series of SAC files
#       from your ascii dataset as specified by the input.
#       -seed is an optional command line switch for also creating a series of SEED files
#       from your ascii dataset as specified by the input.
#
#       Typical useage:
#       <ObsPy> C:\Python27\scripts> python OUTconvert.py /../infil.ASC /../out.ASC -sac
#
#      OUTconvert:
#      Soubrouting that opens the binary file infile, uses the header information generated 
#      by the vdaq subroutine, and creates an ObsPy compatable ASC file.
# 


def vdaq(headerfile):
    #
    #vdaq seeks the headerfile and loads the appropriate variables as defined by the Magadan
    # network vdaq.txt, a modification of symmetric research's dat file format.
    
    with open(headerfile,'r') as head:
        headdata = csv.reader(head)
        header = {}
        for row in headdata:
            r = row[0].split()
            # Load a dictionary of header file information
            header[r[0]] = r[1]   
    return header




def convert(infile,outfile,stname):
            #       Look for the header file by parsing out the directory. 
            #       If it doesn't exist, the program will error.
            #
#    print "The infile specified into the conversion is {}".format(infile)
#    print "The outfile specified into the conversion is {}".format(outfile)
    headerfile = infile[:infile.rfind('\\')+1]+'vdaq.txt'
    hexfile = infile   #  
    header = vdaq(headerfile)
    Samplecount = header['RecordPts:']


        # Extract the start time to the nearest second from the file name
        # File name is an established standard of 14 characters
        # hexfile[-18:-4] represents st.tiome to nearest second
        # 20130314000509
        # Note!! This is computer system time, NOT the start time. So don't do this.
        # Use the start time as encoded within the timing channel (channel 0) as found
        # within the first two samples.

        #    St_time = time.strptime(hexfile[-18:-4],"%Y%m%d%H%M%S")
 
            # Import the binary data
            # Each channel sample comprises of four bytes
            # Epoch time is taken from bytes 1, 0, 13, 12 in that order.
            # Create a data type object of four channels each of which consist of a 32bit integer

    dt = np.dtype([(header['Ch0ID:'],np.int32),(header['Ch1ID:'],np.int32),(header['Ch2ID:'],np.int32),(header['Ch3ID:'],np.int32)])

            # Calculate sample rate and seconds remainder for adding onto file start time.
            # Load timing signal into an array and calculate mean. 
            # Find first sample representing the first positive edge trigger that's greater than sample 5
            # Note that if signal starts high, it must drop low before counting.
            # Count the number of excursions where timing signal goes initially high, starting with the second timing signal
            # and en
            # Find the first sample where gps tick-mark goes high.
            # If tickmark is already high on the 4th sample, go to the next tick mark and count back.


    Data = np.fromfile(hexfile,dtype = dt)      # load all data from the binary file using our specified format dt

            # Data[0][0] represents MSBaLSBa 0000 of epoch start time from gps
            # Data[1][0] represents MSBbLSBb 0000 of epoch start time from gps
            # Epoch start time must be arranged thus: MSBa LSBa MSBb LSBb            
    data = []
    data.append(Data[0][0]) # MSB of start time from file
    data.append(Data[1][0]) # LSB of start time from file
    timestamp = long(int(data[0])<<16|int(data[1])) # Assemble them into the timestamp
    St_time = time.gmtime(timestamp) # Convert them into a tuple representing start time to nearest second
            # Note that rest of the Data is simply a list of raw counts from the ADC and is a 32 bit integer value.
            # It would be nice if each channel was converted to a measurement in terms of volts as a float value.
            # The Symres PAR4CH system is 24 bits for +-10V, and the USB4CH is listed as +-4V
            # but practical measurements in the lab put it more like +-8V. 
            # Therefore, this code is going to ASSUME a nominal value of 0.94 microvolts / count.
            # This converter will convert raw counts into millivolts using this gain factor. Future versions
            # will enable us to input the gain factor as it becomes available.
            #
            #
    Channelgain = [0.94*1e-6,0.94*1e-6,0.94*1e-6,0.94*1e-6] # volts per count
            #

    GPS = []                   # declare our GPS stream which will be loaded from the Data
    Latch = False
    Count = -1                                  # First time Count is incremented is on tic mark number zero.
    Initial_sample = 0
    Final_sample = 0
    Frac_second = 0.0
    Sps = 0.0
    units = ['Volts   ','Volts   ','Volts   ','Volts   ']
    comment = ['TIME    ','Velocity','Velocity','Velocity']
    for n in range(len(Data)):                  # Load the GPS array
        GPS.append(Data[n][0])
    Gpsmean15 = (1.5 * np.median(GPS))            # Use a value that is 1.5 times the median as the pulse break


            # Check to see if the signal started out on a high pulse
    if GPS[4] > np.mean(GPS): 
        Latch = True

    for n in range (4,(len(GPS))):
        if (Latch == True):             # Look for falling edge to reset latch#
            if GPS[n] < Gpsmean15:
                Latch = False
        else:             
            if GPS[n] > Gpsmean15:
                Latch = True
                Count += 1
                if Initial_sample == 0:
                    Initial_sample = n  # Set the first known good rising edge
                else:    
                    Final_sample = n    # Keep updating last known good rising edge


    Sps = float((Final_sample-Initial_sample)/Count)


            #                       Calculate time remainder which equals 
            #                 1000 milliseconds - (#samples before first impulse)

    if (Initial_sample - Sps) > 1:
        Frac_second = 1 - ((Initial_sample - Sps)/Sps)
    else: 
        Frac_second = 1 - (Initial_sample / Sps)

            #                        Create a start time string for ascii file exports

    Start_time = time.strftime("%d-%b-%Y_%H:%M:%S.",St_time)
    Start_time +=str.format("{0:0.3f}",Frac_second)[2:]


    
            # At this point, we have our header information in an index, and we have calculated the true sample rate, 
            # We have extracted the true start time and we've 
            # verified the true second remainder for placing into the start time.

#    print "Initial_sample: {}  VALUE: {}".format(Initial_sample,GPS[Initial_sample])
#    print "Final_sample: {} VALUE: {}".format(Final_sample,GPS[Final_sample])
#    print "Total samples between tic marks = {}".format((Final_sample-Initial_sample))
#    print "Total count of tickmarks: {}".format(Count)
#    print "Samples per second: {}".format(Sps)
#    print "Fraction of a second for start time = {0:1.3f}".format(Frac_second)
#    print "Sample Count from the header file: ",Samplecount
#    print "Start time as calculated:", Start_time
#    print "Delta: {0:8.6e}".format((1/Sps))
#    print "Channel gains used:"
#    for i in range(4):
#        print "    Channel {0}: {1} Volts / count.".format(i,Channelgain[0])

             #                      Create the obspy SAC stream
    for i in range(4):
        t = SacIO()
        b = np.arange(len(Data),dtype=np.float32)   #   Establishes the size of the datastream
        for n in range(len(Data)):        #   Load the array with time-history data
            b[n] = Channelgain[i] * np.float32(Data[n][i]) #   Convert the measurement from counts to volts.
        t.fromarray(b)

             #                     set the SAC header values
        t.SetHvalue('scale',1.00) # Set the scale for each channel. This one is important to declare.
        t.SetHvalue('delta', (1/Sps))
        t.SetHvalue('nzyear',St_time.tm_year)
        t.SetHvalue('nzjday',St_time.tm_yday)
        t.SetHvalue('nzhour',St_time.tm_hour)
        t.SetHvalue('nzmin',St_time.tm_min)
        t.SetHvalue('nzsec', St_time.tm_sec)
        t.SetHvalue('nzmsec', int(Frac_second*1000))
        t.SetHvalue('kstnm',header['A-DInfo:'])
        t.SetHvalue('kcmpnm',header["Ch{}ID:".format(i)])
#        print "Channel name is listed as '{}'".format(header["Ch{}ID:".format(i)])
        t.SetHvalue('idep',4) # 4 = units of velocity (in Volts)
                              # Dependent variable choices: (1)unknown, (2)displacement(nm), 
                              # (3)velocity(nm/sec), (4)velocity(volts), 
                              # (5)nm/sec/sec
        t.SetHvalue('kinst',comment[i-1])       # Instrument type
        t.SetHvalue('knetwk','OUT2SAC ')         # Network designator
        t.SetHvalue('kuser0',units[i-1])        # Place the system of units into the user text field 0

        f = outfile+"_{}.sac".format(header["Ch{}ID:".format(i)])
#        print "filename for SACoutput file = '{}'".format(f)
        with open(f,'wb') as sacfile:
            t.WriteSacBinary(sacfile)
        print " File successfully written: {0}_{1}.sac".format(outfile,header["Ch{}ID:".format(i)])       
        sacfile.close()






def main():

    # Go process the command line switches
    # If the switch for processing a whole directory is called, first catalog the diretory
    # then interatively run through the conversion program for as long as the list exists.
    # If the switch isn't valid, use the previous CLSs to process one specific file.
    # This code will not iterate through bottom directories. 
    # Actually, perhaps a better method would be to NOT embed the crawler into this program
    # but instead use csh and bash and pipe the outputs into thte converter

    #           MAIN PROGRAM BODY
    #  Parse the command line switches

    optioncount = len(sys.argv)
    outputfile_defined = False
    filelist = []
    indir=""
    outdir=""
    extension = '.out'

    if optioncount > 1:
            # Parse out the command line arguments         
        if optioncount >= 3:    # out2sac infile/directoryname outfile/directoryname
            if "." in sys.argv[1]:           # means this is a file name, not a directory
                infile = sys.argv[1]
                filelist.append(infile)      # Put the file into the filename list
                outputfile_defined = True
                outfile = sys.argv[2] # Second argument should also be a file name.
            else:
                indir=sys.argv[1]+"\\"
                filelist = os.listdir(indir) # Collect a list of all files in the directory                
                outdir = sys.argv[2]+"\\"
                infile = filelist[0]    # initialize for the first iteration
                outfile = filelist[0]
                print "Indir and outdir are specified as '{0}' and '{1}'".format(indir,outdir)
            
        elif optioncount == 2:     # Out2sac inputfile/targetdirectory 
                                   # use default name for target file and directory
            if "." in sys.argv[1]:           # means this is a file name
                infile = sys.argv[1]
                filelist.append(infile)      # Put the file into the filename list
                outfile = infile
            else:
                indir = sys.argv[1]+"\\"
                filelist = os.listdir(indir) # Collect a list of all files in the directory
                outdir = indir
                infile = filelist[0]
                outfile = filelist[0]

                                  # Parse through the directory and convert all out files
                                  # If indir, outdir have not yet been specified,
                                  # Specify them.
        stname = "        "
#        stname = raw_input(" Please enter the network designator --> ")
        for n in range(len(filelist)):
            if extension in str.lower(filelist[n]):
                print "Converting {}".format(filelist[n]) 
                if len(filelist)>1:
                    infile = indir+filelist[n]
                if not outputfile_defined:
                    if string.find(infile,'.') > 0: 
                        outfile = outdir+filelist[n][:string.find(filelist[n],'.')]  # drop the file extension off the end
                    else:      
                        outfile = outdir+filelist[n]
                convert(infile,outfile,stname)  # Convert the out file into sac files


    else:
        print "Useage: OUT2SAC infile.out (outfile.sac)"
        print "Or, OUT2SAC input_directory (output_directory)"
        print "No infile or directory specified."
        print len(sys.argv)

#Call the main loop
#
if __name__ == '__main__':
  main()

# <codecell>

