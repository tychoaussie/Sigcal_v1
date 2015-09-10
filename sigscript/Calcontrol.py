__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20150910"
__license__ = "MIT"

# 20150806 version : Load the calcontrolcache from main script directory for starting values
# then save these values to the cache at the end, if the user desires it.
#

import os, sys, csv,string

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

def getcal(cachefile): 
    # calcontrol needs to include calibration constants as well as the station name and the channel name, and the particular constant for that channel.
    # Thus a third line is necessary that specifies the channel identifier and the channel assignment of that channel.
    # Channel name is located in the top row already, and it's position is associated with the sensitivity. So the third row designates the UUT and the
    # laser position channel.
    cconstant = ["MSU","CH0",0.9537,"CH1",0.9537,"CH2",0.9537,"CH3",0.9537,1.0,0.579,0.707,0.890,1,3]
    try:
        with open(cachefile,'r') as fin:
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


    except:
        print "Error during retrieval of the calibration constant default parameters.\n"
        print "Setting the paramters to default settings."
        header = ['MSU','CH0','CH1','CH2','CH3','Laserres','lcalconst','h','resfreq']
        calconstants = ['MSU',0.9537,0.9537,0.9537,0.9537,0.9990,0.579,0.707,0.890]
        selection = [1,3]
    return(header,calconstants,selection)

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
    cache = "c:\Anaconda\sigscript\calcontrolcache.cal"

    if optioncount > 1:           # If there are switches, check the first one only.                           
        if optioncount == 2:
            if "\\" in sys.argv[1]:
                calcontrol = sys.argv[1]+"\calcontrol.cal"

                                  # Scan to see if file exists. If so, load it for defaults.
  
   

    header,constant,selection = getcal(cache) 

    try:
        invar = raw_input('Please enter the station name. (Default = [ {} ]) \n--> '.format(header[0]))
        if len(invar)==0:
            invar = str(header[0])
            print "Station name is set to default '{}'".format(header[0])
        constant[0]=str(invar)
        header[0]=(str(invar))
    except ValueError:
        print "Please enter appropriate characters. Station name set to '{}'.".format(header[0])


    for j in range(1,5):
        try:
            print"\nEnter the name for channel {0}: (Default = [ {1} ]) ".format(j,header[j])
            invar = str(raw_input('-->'))
            if len(invar)==0:
                #invar = "Ch"+str(j)
                print "Channel name is set to default '{}'".format(header[j])
                invar = header[j]
            header[j] = (invar)
        except ValueError:
            print "No input."
            print "channel name set to '{}' as a default.".format(header[j])
            # header[j] = ('Ch'+str(j))

        try:
            print 'Channel {0} calibration value, in uV/count: Default = [ {1} ] '.format(j,constant[j])
            invar = str(raw_input('--> '))
            if len(invar)==0:
                print "Channel gain set to default of {}\n\n".format(constant[j])
                invar = constant[j]
            constant[j] = (float(invar))
        except ValueError:
            print "Value must be a floating point number."
            print "Calibration number being set to {} uV/count as a default.\n\n".format(constant[j])


    try:
        print 'Enter laser resolution calibration (mV/micron). default = [ {} ]'.format(constant[5])
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Laser resolution set to default of {} mV/micron\n".format(constant[5])
            invar = constant[5]
        constant[5] = (float(invar))
    except ValueError:
        print "Value must be a floating point number."
        print "Calibration number being set to {} mV/micron as a default.\n".format(constant[5])


    try:
        print 'Enter the mass/laser position Geometry correction ratio: default = [ {} ]'.format(constant[6])
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "correction ratio set to default of {}\n".format(constant[6])
            invar = constant[6]
        constant[6] = (float(invar))
    except ValueError:
        print "Value must be a floating point number."
        print "Correction ratio being set to {} as a default.\n".format(constant[6])


    try:
        print 'Enter the damping ratio for this seismometer:'
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Damping ratio (h) set to default of {}\n".format(constant[7])
            invar = constant[7]
        constant[7] = (float(invar))
    except ValueError:
        print "Value must be a floating point number."
        print "Damping ratio (h) being set to {} as a default.\n".format(constant[7])



    try:
        print 'Enter the resonance frequency (1/free period) in Hz:'
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Resonance frequency set to default of {} Hz\n".format(constant[8])
            invar = constant[8]
        constant[8] = (float(invar))
    except ValueError:
        print "Value must be a floating point number."
        print "Resonance frequency being set to {} Hz as a default.\n".format(constant[8])



    
    for i in range(0,4):
        print"{0} assigned to: ------>Ch # {1}".format(header[i+1],i)



    try:
        print 'Choose the channel number representing the sensor:(default = [ {} ]'.format(selection[0])
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Channel number {} assigned to represent the sensor.".format(selection[0])
            invar = selection[0]
        selection[0] = int(invar)

        if int(invar)>=0 and int(invar) <= 3:
            selection[0] = int(invar)
        else:
            print "Selection is outside the bounds for the digitizer. Must be a value between 0 and 3."
            print " Channel selection set to default of ADC digitizer channel # {}\n\n".format(selection[0])

    except ValueError:
        print "Value must be a floating point number."
        print "Channel number {} assigned to represent the sensor.".format(selection[0])



    try:
        print 'Choose the channel number representing the sensor:(default = [ {} ]'.format(selection[1])
        invar = str(raw_input('--> '))
        if len(invar)==0:
            print "Channel number {} assigned to represent the sensor.\n\n".format(selection[1])
            invar = selection[1]
        if int(invar)>=0 and int(invar) <= 3:
            selection[1] = int(invar)
        else:
            print "Selection is outside the bounds for the digitizer. Must be a value between 0 and 3."
            print " Channel selection set to default of ADC digitizer channel # {}\n\n".format(selection[1])
    except ValueError:
        print "Value must be a floating point number."
        print "Channel number {} assigned to represent the sensor.\n\n".format(selection[1])

    print "Station name: {}".format(header[0])
    for i in range(1,5):
        print "ADC Ch {0} assigned to channel {1} with sensitivity of {2} uV/count.".format(i-1,header[i],constant[i])
    print "Laser resolution = {} mV/mm".format(constant[5])
    print "Mass length to laser measurement point ratio (lcalconstant) = {}".format(constant[6])
    print "Damping ratio h = {}".format(constant[7])
    print "Resonance frequency = {} Hz".format(constant[8])
    print "Sensor is connected to ADC channel number {}".format(selection[0])
    print "Laser is connected to ADC channel number {}".format(selection[1])
  

#                         Fill out the remainder of the header for compatability
      
    
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

    try:
        invar = raw_input('Save as new defaults? Y/N ')
        if string.lower(invar)[:1] == "y":
             with open(cache,'wb') as csvfile: 
                 outrow = csv.writer(csvfile, delimiter = ",",
                              quotechar='|', quoting=csv.QUOTE_MINIMAL)
                 outrow.writerow(header)
                 outrow.writerow(constant)
                 outrow.writerow(selection) 
             print "Parameters saved as new defaults."    
    except ValueError:
        print "Unable to write the defaults. Check file folder c:/anaconda/sigscript to see if it exists."

    print " Cal control written to:",calcontrol


#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()

