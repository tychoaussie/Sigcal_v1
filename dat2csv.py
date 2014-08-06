__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20140806"
__license__ = "MIT"



import os
import sys
                                           #from scipy import signal
                                           #from scipy.integrate import simps
                                           #import pylab as plt
                                           #import numpy as np
                                           #import scipy as sp
import string                              # We use the string.find utility for file naming
import time                                # we use the sleep function to enable conversion of the DAT
import subprocess                          # used for the execution of command-line programs
                                           # from obspy.core import read, Trace, Stream, UTCDateTime
                                           # from obspy.sac import SacIO


class Dat2csv(object):
    '''Dat2csv.py is a utility for batch converting Symmetric Research .DAT files into csv files
       for a whole directory. It uses the 2010 build of dat2asc.exe as provided from symmetric
       and converts the file, followed by a rename of the csv file. It has only one command line
       switch, and that is to point it at a directory for converting the dat files.

       The program will convert non-sequential DAT files into separate csv files, and all
       sequential files will be concatenated into a single csv file. It is therefore important
       to rename or move any sequential csv file that you do not wish to include within the csv.
        
       One critical requirement is that dat2asc.exe (2010 build) exists in the
       directory as such: "c:\Python27\dat2asc.exe"

       Syntax: dat2csv target_directory  

       

       Typical useage:
       <ObsPy> C:\Python27\scripts> python Dat2csv.py c:/calibration/station/ 

    '''



def convert(infile):
    print infile
    outfile = infile[string.rfind(infile,"\\")+1:string.find(infile,'.')]+".csv"
    dat2csvfile = infile[:string.rfind(infile,"\\")+1]+"Dat2asc-301-Data.csv"
    subprocess.call(["c:\\Python27\\dat2asc.exe",infile,"csv"])
    print dat2csvfile
    print outfile
    subprocess.call(["ren",dat2csvfile,outfile],shell=True)



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
    directory = os.getcwd()
    directory = directory.replace("/","\\")
    print "This is the directory name as taken from the computer:",directory
    if optioncount > 1:
        
        
        directory = sys.argv[1]
        directory = directory.replace("/","\\")
        if directory[-1:] !="\\":
                directory = directory+"\\"
        try:
            filelist = os.listdir(directory)            
        except:
            print "Command line parameter must consist of a valid directory. {}".format(directory)
            sys.exit(0)
    else:
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
 