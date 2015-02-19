__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20150210"
__license__ = "MIT"

import os, sys, csv

class Calconst(object):
    '''CALCONST is a utility for generating the calibration constants necessary for running
       the 20150210 version of sigcal.py (rev2), which takes a series of data files containing
       sinusoidal data from a seismometer and laser position sensor in order to fabricate
       a calibration curve sufficient for generating a calibation of poles and zeros.
       
       Useage: Install Python, then from the command prompt
       specify the target directory. No other options are valid. The program will generate
       a csv file named "calcontrol.cal" within the directory you specify. If no directory
       is specified, the file will be created in your current working directory. This file
       should then be placed within the directory along with the series of csv files
       representing your calibration data.

       Syntax: Calconst.py c:\seismo\calibration\ 

       
       Typical useage:
       <ObsPy> C:\Python27\scripts> python Calconst.py c:\seismo\calibration\

    '''
                                   # Function getconstants:
                                   # From calcontrol file, retrieve the list of constants 
                                   # that relate these measurements to the real world.
                                   # constants[0] contains headers that we don't really use
                                   # constant[0] = (text) Station: 'station name'
                                   # constant[1] = (float) adccal[0]: cal constant for ch 0 (microvolts / count)
                                   # constant[2] = (float) adccal[1]: cal constant for ch 1 (microvolts / count)
                                   # constant[3] = (float) adccal[2]: cal constant for ch 2 (microvolts / count)
                                   # constant[4] = (float) adccal[3]: cal constant for ch 3 (microvolts / count)
                                   # constant[5] = (float) laserres: cal constant for the laser ( mV / micron)
                                   # constant[6] = (float) lcalconst: cal constant for geometry correction factor
                                   # constant[7] = (float) h: Damping ratio for the seismometer as measured by engineer.
                                   # constant[8] = (float) resfreq: Free period resonance freq. as measured by engineer.

def main():
                                  # MAIN PROGRAM BODY

                                  #  Parse the command line switches
                                  # Commmand example: 
                                  # c:\Python27>Python.exe Calconst.py c:\seismo\caldata\momo\
                                  # where momo is the working directory. 
                                  # No file extension will create the file in the current 
                                  # working directory.
    optioncount = len(sys.argv)    
    calcontrol = os.getcwd()+"\calcontrol.cal"

    if optioncount > 1:           # If there are switches, check the first one only.                           
        if optioncount == 2:
            if "\\" in sys.argv[1]:
                calcontrol = sys.argv[1]+"\calcontrol.cal"

                                  # Scan to see if file exists. If so, load it for defaults.
                                  #

#       main execution code goes here for parsing through all the files in filelist.
#                                 # Populate the header
    header = []
                                   # Populate the array
    constant = []
    selection = []

    try:
        invar = raw_input('Please enter the station name. ')
        if len(invar)==0:
            invar = "SGCAL"
            print "Station name is set to default 'SGCAL'"
        constant.append(str(invar))
        header.append(str(invar))
    except ValueError:
        print "Please enter appropriate characters. Station name set to 'SGCAL'."
        constant.append("SGCAL")
        header.append("SGCAL")

    for j in range(0,4):
        try:
            print"\nEnter the name for channel {}:  ".format(j)
            invar = str(raw_input('  '))
            if len(invar)==0:
                invar = "Channel"+str(j)
                print "Channel name is set to default '{}'".format(invar)
            header.append(invar)
        except ValueError:
            print "No input."
            print "channel name set to 'Channel{}' as a default.".format(j)
            header.append('Channel'+str(j))

        try:
            constant.append(float(raw_input('Channel 0 calibration value, in uV/count:  ')))
        except ValueError:
            print "Value must be a floating point number."
            print "Calibration number being set to 0.9425 uV/count as a default."
            constant.append(float(0.9425))


    try:
        constant.append(float(raw_input('\nEnter the laser resolution cal constant (mV/micron)  ')))
    except ValueError:
        print "Error! Value must be a floating point number."
        print "Calibration number being set to 0.9932 as a default."
        constant.append(float(0.9932))

    try:
        constant.append(float(raw_input('\nEnter the mass/laser position Geometry correction ratio:  ')))
    except ValueError:
        print "Error! Value must be a floating point number."
        print "Calibration number being set to 0.579 as a default for SM3."
        constant.append(float(0.579))

    try:
        constant.append(float(raw_input('\nEnter the measured damping ratio h:  ')))
    except ValueError:
        print "Error! Value must be a floating point number."
        print "Calibration number being set to 0.707 as a default."
        constant.append(float(0.707))

    try:
        constant.append(float(raw_input('\nEnter the measured free period frequency in Hz:  ')))
    except ValueError:
        print "Error! Value must be a floating point number."
        print "Calibration number being set to 0.75 Hz as a default."
        constant.append(float(0.750))

    try:
        print "\n\nChoose the channel that represents the unit under test."
        for i in range(0,4):
            print"Channel {0} is listed as channel number {1}".format(header[i+1],i)
        
        selection.append(int(raw_input('Choose the channel number representing the unit under test:  ')))
        selection.append(int(raw_input('Choose the channel number representing the laser position sensor:  ')))
    
    except ValueError:
        print "No input."
        print "UUT channel set to 'Channel2' as a default."
        print "Laser channel set to 'Channel3' as a default."
        print "If these are incorrect, you may manually edit the calibration control file."
        selection.append(int(2))
        selection.append(int(3))

#                         Fill out the remainder of the header for compatability
    header.append('laserres')
    header.append('lcalconst')
    header.append('h')
    header.append('resfreq')
      
    
                          # constant[0] = (text) Station: 'station name'
                          # constant[1] = (float) adccal[0]: cal constant for ch 0 (microvolts / count)
                          # constant[2] = (float) adccal[1]: cal constant for ch 1 (microvolts / count)
                          # constant[3] = (float) adccal[2]: cal constant for ch 2 (microvolts / count)
                          # constant[4] = (float) adccal[3]: cal constant for ch 3 (microvolts / count)
                          # constant[5] = (float) laserres: cal constant for the laser ( mV / micron)
                          # constant[6] = (float) lcalconst: cal constant for geometry correction factor
                          # constant[7] = (float) h: Damping ratio for the seismometer as measured by engineer.
                          # constant[8] = (float) resfreq: Free period resonance freq. as measured by engineer.

                          # Write out the new variables to the file.

    with open(calcontrol,'wb') as csvfile: # use 'wb' in place of 'a' if you want to overwrite the file.
         outrow = csv.writer(csvfile, delimiter = ",",
                      quotechar='|', quoting=csv.QUOTE_MINIMAL)
         outrow.writerow(header)
         outrow.writerow(constant)
         outrow.writerow(selection)

    print " Cal control written to:",calcontrol


#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()

